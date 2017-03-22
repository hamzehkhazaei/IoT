import json
import math
import os
import threading
import time

import pika
import spur

from monitor import StartMonitoringThread, log_rt_metrics
from platform_management import connect_node_to_wavecloud
from util import Util

auth_url = "http://iam.savitestbed.ca:5000/v2.0"
driver = "openstack"
password = "ham01nas"
ssh_user = "ubuntu"
ubuntu14 = "Ubuntu-14-04"
ubuntu16 = "Ubuntu-16-04"
tenant_name = "demo2"
core = "CORE"

small_flavor = "m1.small"
medium_flavor = "m1.medium"
large_flavor = "m1.large"
xlarge_flavor = "m1.xlarge"

# number of containers that can be run on top of each flavor
large_vm_capacity = 8
medium_vm_capacity = 3
small_vm_capacity = 4

max_kafka_vm = 3
max_spark_vm = 2

# I use this to scale spark if we have to many aggregators
spark_to_kafka_ratio = 1 / 2

# I use this to scale cassandra worker in the core if we have to many spark worker in edges
cassandra_to_spark_ratio = 1 / 8
max_cassandra_cont = 3

master_shell = ''
controller_shell = ''
controller_ip = '127.0.0.1'
initial_workers_name = []
initial_aggs_name = []
initial_db_name = []
util = Util()

swarm_master_name = "swarm-master"
swarm_master_ip = ""

regions_name = util.load_regions()
provisioning_worker_on_region = [0, 0, 0, 0]
provisioning_agg_on_region = [0, 0, 0, 0]

core_worker_role = "iot-core-worker"
edge_worker_role = "iot-edge-worker"
agg_role = "iot-agg"
core_db_role = "iot-core-db"

manager_role = "manager"
workers_ip = []


# agg_queue = Queue()
# edge_queue = Queue()


def alarm(message):
    msg = 'say ' + message
    os.system(msg)


def init():
    global master_shell
    global controller_shell

    controller_shell = ssh_to(controller_ip)
    master_shell = ssh_to(ip=get_swarm_master_ip(), user_name='ubuntu', node_name=swarm_master_name)
    load_initial_nodes_name()


def print_green(prt): print("\033[92m {}\033[00m".format(prt))


def print_cyan(prt): print("\033[96m {}\033[00m".format(prt))


def print_red(prt): print("\033[91m {}\033[00m".format(prt))


def ssh_to(ip='127.0.0.1', user_name='', node_name=''):
    """Connect to the IoT controller to setup the cluster
        :param node_name: the name of the node; this one is used to find the private key
        :param user_name: for ssh connection
        :param ip: is the ip or host name of the machine
        :return a shell connected to the local or remote machine
        This machine should have Docker, Docker-Machine and Swarm installed
    """
    if ip == "127.0.0.1":
        shell = spur.LocalShell()
    else:
        shell = spur.SshShell(
            hostname=ip,
            username=user_name,
            private_key_file="/Users/hamzeh/.docker/machine/machines/" + node_name + "/id_rsa",
            missing_host_key=spur.ssh.MissingHostKey.accept
        )
    result = shell.run(["hostname", "-fs"], allow_error=True, encoding='utf8')

    if result.return_code > 0:
        print("\n***" + result.stderr_output)
    return shell


def get_swarm_master_ip():
    result = controller_shell.run(["docker-machine", "ip", swarm_master_name], store_pid="True", allow_error=True,
                                  encoding="utf8")
    if result.return_code > 0:
        print(result.stderr_output)
        return ""
    else:
        return str(result.output)[:-1]  # we do this to remove the \n at the end of the output


def load_initial_nodes_name():
    global initial_workers_name, initial_aggs_name, initial_db_name
    initial_workers_name = util.load_initial_workers_node_names()
    initial_aggs_name = util.load_initial_aggregators_node_names()
    initial_db_name = util.load_initial_datastore_node_names()


def inspect_service(service_name):
    result = master_shell.run(["sudo", "docker", "service", "inspect", service_name], store_pid="True",
                              allow_error=True, encoding="utf8")
    if result.return_code > 0:
        print(result.stderr_output)
    else:
        return str(result.output)


def get_no_replicas(service_name):
    service_info = inspect_service(service_name)
    service_json = json.loads(service_info, encoding='utf8')
    current_replicas = int(service_json[0]['Spec']['Mode']['Replicated']['Replicas'])
    return current_replicas


def find_number_of_vms(vm_name_prefix):
    counter = 0
    result = master_shell.run(["sudo", "docker", "node", "ls"],
                              store_pid="True", allow_error=True, encoding="utf8")
    if result.return_code > 0:
        print(result.stderr_output)
    else:
        arr = str(result.output).split("\n")
        for i in range(0, len(arr)):
            if arr[i].__contains__(vm_name_prefix):
                counter += 1
    return counter


def get_node_ip(node_name):
    result = controller_shell.run(["docker-machine", "ip", node_name], store_pid="True", encoding="utf8")
    return str(result.output)[:-1]  # we do this to remove the \n at the end of the output


def delete_vm(name):
    """delete a VM using: docker-machine rm -f VM-name"""
    result = controller_shell.run(["docker-machine", "rm", "-f", name], allow_error=True, encoding="utf8")
    if result.return_code > 0:
        print_red(result.stderr_output)
    else:
        print_red(result.output)


def remove_swarm_node(node_name, role, node_ip=""):
    if node_ip == "":
        node_ip = get_node_ip(node_name)

    try:
        shell = ssh_to(node_ip, user_name='ubuntu', node_name=node_name)
        result = shell.run(["sudo", "docker", "swarm", "leave"], store_pid="True", allow_error=True,
                           encoding="utf8")
        if result.return_code > 0:
            print_red(result.stderr_output)
        else:
            print_red(node_name + " " + result.output)
    except:
        print_red("\n**** " + node_name + " is not reachable; will be removed forcefully.\n")
        raise

    result = master_shell.run(["sudo", "docker", "node", "rm", "--force", node_name], store_pid="True",
                              allow_error=True, encoding="utf8")
    if result.return_code > 0:
        print_red(result.stderr_output)
    else:
        print_red(result.output)

    delete_vm(node_name)
    util.remove_node_info(node_name, role)  # scale the aggregator service


def scale_kafka_service(service_name, change):
    # global agg_queue
    if not service_name.__contains__("agg"):
        print("Wrong service.")
        return
    current_replicas = get_no_replicas(service_name)
    no_vms = find_number_of_vms(service_name)
    region, provisioning_index = get_region_and_prov_index(service_name)

    if change > 0:
        if no_vms <= max_kafka_vm:
            if current_replicas + change <= small_vm_capacity * no_vms:
                scale_service(service_name, current_replicas + change)
            elif current_replicas + change <= small_vm_capacity * max_kafka_vm:
                if provisioning_agg_on_region[provisioning_index] == 0:
                    print_cyan("Utilization is high, requesting for a new VM.")
                    scale_cluster(service_name, small_flavor, agg_role)
                else:
                    print_cyan("Kafka: Utilization is high, request for a new VM has already been submitted: "
                               + service_name)
                    # agg_queue.put(service_name)
            else:
                print_cyan("Kafka: Capacity is full for region: " + service_name)

    else:
        if current_replicas == 1:
            print_red("Invalid down scaling; there is only one replica of: " + service_name)
        elif current_replicas + change < 1:
            print_red("Invalid down scaling; the service will be downsized to 1 replica.")
            scale_service(service_name, current_replicas - (current_replicas - 1))
        else:
            scale_service(service_name, current_replicas + change)
            if math.ceil(float((current_replicas + change) / small_vm_capacity)) < no_vms:
                name, ip = find_candidate_for_deleting(service_name)
                remove_swarm_node(name, "aggregators_name", ip)

    check_if_edge_service_is_to_scale(service_name)


# scale the edge service
def scale_spark_service(service_name, change):
    # global edge_queue
    if not service_name.__contains__("worker"):
        print("Wrong service.")
        return
    current_replicas = get_no_replicas(service_name)
    no_vms = find_number_of_vms(service_name)
    region, provisioning_index = get_region_and_prov_index(service_name)

    if change > 0:
        if no_vms <= max_spark_vm:
            if current_replicas + change <= medium_vm_capacity * no_vms:
                scale_service(service_name, current_replicas + change)
            elif current_replicas + change <= medium_vm_capacity * max_spark_vm:
                if provisioning_worker_on_region[provisioning_index] == 0:
                    print_cyan("Spark: Utilization is high, requesting for a new VM.")
                    scale_cluster(service_name, medium_flavor, edge_worker_role)
                else:
                    print_cyan("Spark: Utilization is high, request for a new VM has already been submitted: "
                               + service_name)
                    # edge_queue.put(service_name)
            else:
                print_cyan("Spark: capacity is full for region: " + service_name)
    else:
        if current_replicas == 1:
            print_red("Spark: Invalid down scaling; there is only one replica of the service.")
        elif current_replicas + change < 1:
            print_red("Spark: Invalid down scaling; the service will be downsized to 1 replica.")
            scale_service(service_name, current_replicas - (current_replicas - 1))
        else:
            scale_service(service_name, current_replicas + change)
            if math.ceil(float((current_replicas + change) / medium_vm_capacity)) < no_vms:
                name, ip = find_candidate_for_deleting(service_name)
                remove_swarm_node(name, "workers_name", ip)

    check_if_core_db_service_is_to_scale()


def check_if_core_db_service_is_to_scale():
    load_initial_nodes_name()
    workers_service_reps = 0
    # for the moment we have on db service;
    db_service_reps = get_no_replicas(initial_db_name[0])

    # get the total replications of worker services in all edges and core
    for i in range(0, len(initial_workers_name)):
        workers_service_reps += get_no_replicas(initial_workers_name[i])

    change = db_service_reps - (workers_service_reps * cassandra_to_spark_ratio)
    if change > 1 and db_service_reps > 1:  # we need at least one replication
        scale_service(initial_db_name[0], db_service_reps - 1)  # down scaling
    elif change < 0 and db_service_reps < max_cassandra_cont:
        scale_service(initial_db_name[0], db_service_reps + 1)  # up scaling
    else:
        print()


def scale_service(service_name, replicas):
    resp_time_metrics = []
    old_rep = get_no_replicas(service_name)
    print("\nScaling service: " + service_name + " to new size: " + str(replicas))
    t0 = time.time()
    result = master_shell.run(
        ["sudo", "docker", "service", "scale", service_name + "=" + str(replicas)],
        store_pid="True", allow_error=True, encoding="utf8")
    if result.return_code > 0:
        print(result.stderr_output)
        return
    if old_rep < replicas:  # if this is scaling out, we log the record
        t1 = time.time()
        resp_time_metrics.append(int(time.time()))
        resp_time_metrics.append('N/A')  # this means, this metric is not for a VM
        resp_time_metrics.append(round(t1 - t0, 3))
        region, inx = get_region_and_prov_index(service_name)
        resp_time_metrics.append(region)
        if service_name.__contains__('agg'):
            resp_time_metrics.append('Kafka')
            resp_time_metrics.append(agg_role)
        elif service_name.__contains__('worker'):
            resp_time_metrics.append('Spark')
            resp_time_metrics.append(edge_worker_role)
        elif service_name.__contains__('core-db'):
            resp_time_metrics.append('Cassandra')
            resp_time_metrics.append(core_db_role)

        resp_time_metrics.append(service_name)
        log_rt_metrics(resp_time_metrics)  # here we log the provisioning process.


def find_candidate_for_deleting(service_name):
    if service_name.__contains__("agg"):
        names, ips = util.load_aggregators_node_info()
        for name, ip in zip(names, ips):
            if name.__contains__(service_name):
                return name, ip
    elif service_name.__contains__("worker"):
        names, ips = util.load_worker_node_info()
        for name, ip in zip(names, ips):
            if name.__contains__(service_name):
                return name, ip


def create_vm(vm_name, user_name, flavor, image, region):
    """Connect to the backend cloud service provider
    the cloud provider could be any driver supported by docker-machine
    """
    result = controller_shell.run(
        ["docker-machine", "create", "--driver", "openstack", "--openstack-auth-url", auth_url,
         "--openstack-insecure", "--openstack-username", user_name, "--openstack-password",
         password, "--openstack-flavor-name", flavor, "--openstack-image-name", image,
         "--openstack-tenant-name", tenant_name, "--openstack-region", region,
         "--openstack-ssh-user", ssh_user, vm_name],
        store_pid="True", allow_error=True, encoding="utf8")
    if result.return_code > 0:
        print(result.stderr_output)


def get_token_and_master_ip_port():
    result = master_shell.run(["sudo", "docker", "swarm", "join-token", "worker"], store_pid="True", encoding="utf8")
    words = str(result.output).replace("\\", " ").replace("\n", " ").split(" ")
    token_index = words.index("--token") + 1

    token = words[token_index]
    master_ip_port = words[-3]
    return token, master_ip_port


def join_node_to_swarm_cluster(node_ip, node_name):
    token, master_ip_port = get_token_and_master_ip_port()
    shell = ssh_to(ip=node_ip, user_name='ubuntu', node_name=node_name)
    with shell:
        result = shell.run(["sudo", "docker", "swarm", "join", "--token", token, master_ip_port],
                           store_pid="True", allow_error=True, encoding="utf8")
        if result.return_code > 0:
            print(result.stderr_output)
        else:
            print(result.output + node_name)


def label_a_node(node_name, loc='', role=''):
    print("\nAdding labels:" + loc + ", " + role + " to node: " + node_name)
    try:
        result = master_shell.run(["sudo", "docker", "node", "update", "--label-add", "loc=" + loc,
                                   "--label-add", "role=" + role, node_name], store_pid="True", encoding="utf8")
        if result.return_code > 0:
            print(result.stderr_output)
        else:
            return str(result.output)
    except:
        # msg = "Failure to label a node"
        # alarm(msg)
        print_red("Failure in labelling for node: " + node_name)
        remove_swarm_node(node_name, role)


class ProvisionSwarmNodeThread(threading.Thread):
    def __init__(self, thread_id, vm_name, user_name, flavor, image, region, provisioning_inx, role):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.vm_name = vm_name
        self.user_name = user_name
        self.flavor = flavor
        self.image = image
        self.region = region
        self.provisioning_index = provisioning_inx
        self.role = role

    def run(self):
        global provisioning_agg_on_region
        global provisioning_worker_on_region
        resp_time_metrics = []
        print_cyan(self.vm_name + " is being provisioned ...")
        try:
            t0 = time.time()
            create_vm(self.vm_name, self.user_name, self.flavor, self.image, self.region)
            join_node_to_swarm_cluster(get_node_ip(self.vm_name), self.vm_name)
            label_a_node(self.vm_name, self.region, self.role)
            connect_node_to_wavecloud(get_node_ip(self.vm_name), self.vm_name)
            print_cyan(self.vm_name + " is up and running with latest docker engine ...")

            if self.role == edge_worker_role:
                util.add_node_info(self.vm_name, get_node_ip(self.vm_name), "workers_name")
            elif self.role == agg_role:
                util.add_node_info(self.vm_name, get_node_ip(self.vm_name), "aggregators_name")
            else:
                print("Invalid role.")
            t1 = time.time()
            resp_time_metrics.append(int(time.time()))
            resp_time_metrics.append(round(t1 - t0, 3))  # provisioning time for the vm
            resp_time_metrics.append('N/A')  # this means, this metric is not for a container
            resp_time_metrics.append(self.region)
            resp_time_metrics.append(self.flavor)
            resp_time_metrics.append(self.role)
            resp_time_metrics.append(self.vm_name)
            log_rt_metrics(resp_time_metrics)  # here we log the provisioning process.
        except:
            msg = "Something went wrong in provisioning the VM at: " + self.region
            alarm(msg)

        if self.role == edge_worker_role:
            provisioning_worker_on_region[self.provisioning_index] = 0  # declare the end of provisioning
        elif self.role == agg_role:
            provisioning_agg_on_region[self.provisioning_index] = 0


# returns the region of a worker or aggregator
def get_region_and_prov_index(service_name):
    if initial_workers_name.__contains__(service_name):
        inx = initial_workers_name.index(service_name)
        return regions_name[inx], inx
    elif initial_aggs_name.__contains__(service_name):
        inx = initial_aggs_name.index(service_name)
        return regions_name[inx], inx
    elif initial_db_name.__contains__(service_name):
        inx = initial_db_name.index(service_name)
        return regions_name[inx], inx
    else:
        print("Couldn't find the region.")
        return None


def scale_cluster(service_name, flavor, role):
    global provisioning_agg_on_region
    global provisioning_worker_on_region
    region, provisioning_index = get_region_and_prov_index(service_name)

    if role == agg_role:
        new_vm_name = service_name + "." + time.strftime("%Y-%m-%d.%H-%M-%S", time.localtime())
        thread = ProvisionSwarmNodeThread(int(time.time()), new_vm_name, "hamzeh", flavor, ubuntu14, region,
                                          provisioning_index, role)
        provisioning_agg_on_region[provisioning_index] = 1  # set the provisioning true for this region
        thread.start()

    elif role == edge_worker_role:
        new_vm_name = service_name + "." + time.strftime("%Y-%m-%d.%H-%M-%S", time.localtime())
        thread = ProvisionSwarmNodeThread(int(time.time()), new_vm_name, "hamzeh", flavor, ubuntu14, region,
                                          provisioning_index, role)
        provisioning_worker_on_region[provisioning_index] = 1  # set the provisioning true for this region
        thread.start()

    else:
        print("Role is not valid.")


# check if Spark service at the edge needs to scale up due to scaling in its aggregators
def check_if_edge_service_is_to_scale(agg_service_name):
    load_initial_nodes_name()
    agg_service_reps = get_no_replicas(agg_service_name)

    ind = initial_aggs_name.index(agg_service_name)
    edge_service_name = initial_workers_name[ind]
    edge_service_reps = get_no_replicas(edge_service_name)

    change = edge_service_reps - (agg_service_reps * spark_to_kafka_ratio)
    if change > spark_to_kafka_ratio:
        scale_spark_service(edge_service_name, -1)  # down scaling
    elif change <= -1 * spark_to_kafka_ratio:
        scale_spark_service(edge_service_name, 1)  # up scaling
    else:
        print()


# check if Spark service in the core needs to scale due to scaling in Spark workers at edges
def check_if_core_service_is_to_scale():
    return None


# check if this is okay to remove other parameters.
def handle_arrival_request(body):
    if str(body).__contains__(core):
        scale_kafka_service("core-agg", 1)
    elif str(body).__contains__("EDGE-WT-1"):
        scale_kafka_service("wt-agg", 1)
    elif str(body).__contains__("EDGE-CT-1"):
        scale_kafka_service("ct-agg", 1)
    elif str(body).__contains__("EDGE-VC-1"):
        scale_kafka_service("vc-agg", 1)
    else:
        print("Bad Request:")


def start_am():
    init()
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=controller_ip))
    channel = connection.channel()
    channel.queue_declare(queue='qiot')
    print(' [*] Waiting for request. To exit press CTRL+C')

    channel.basic_consume(handle_arrival_request, queue='qiot', no_ack=True)
    channel.start_consuming()


if __name__ == "__main__":
    # start_am()
    init()
    monitor_thread = StartMonitoringThread()
    monitor_thread.setDaemon(True)  # this way, whenever the main program exit, monitoring thread will stop as well.
    monitor_thread.start()
    time.sleep(2)
    modify = 1
    count = 1
    while count <= 2:
        scale_kafka_service("wt-agg", modify)
        time.sleep(1)
        scale_kafka_service("cg-agg", modify)
        time.sleep(1)
        scale_kafka_service("mg-agg", modify)
        time.sleep(1)
        scale_kafka_service("core-agg", modify)
        time.sleep(2)
        count += 1
        # scale_kafka_service("vc-agg", 1)
        # scale_kafka_service("wt-agg", 1)
        # time.sleep(0.5)
        # print(find_candidate_for_deleting("wt-agg"))
        # print(get_all_agg_replicas())
        # down_scale_swarm_cluster_to_initial_state()
