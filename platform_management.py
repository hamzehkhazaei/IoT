import json
import threading
import time

import spur

import monitor
from util import Util

# todo: I need to separate edge workers from core workers later.
# todo: I need to update the ip of initial nodes in the property file later.
# todo: I need to make the downscaling smother. so the tasks should be first removed and then an empty node should be
# todo: deprovisioned.


# Autonomic Manager info
auth_url = "http://iam.savitestbed.ca:5000/v2.0"
# driver = "openstack"
user = "hamzeh"
password = "password"

small_flavor = "m1.small"
medium_flavor = "m1.medium"
large_flavor = "m1.large"
xlarge_flavor = "m1.xlarge"

ubuntu14 = "Ubuntu-14-04"
ubuntu16 = "Ubuntu-16-04"
tenant_name = "demo2"
ssh_user = "ubuntu"
controller_ip = "127.0.0.1"  # this machine is the default controller on which we access cloud;
# it has docker-machine installed.
controller_name = 'iot-controller'
privatekey_path_macos = '/Users/hamzeh/.docker/machine/machines/'
privatekey_path_ubuntu = '/home/ubuntu/.docker/machine/machines/'
security_group = "savi-iot"

# Swarm info
swarm_master_name = "swarm-master"
swarm_master_ip = ""
core_worker_role = "iot-core-worker"
edge_worker_role = "iot-edge-worker"
manager_role = "manager"

locations_name = ["Toronto", "Chicago", "Waterloo", "Montreal"]

# Spark info
#  do not change this, as other names don't work.
spark_overlay_network_name = 'spark'
spark_memory_reserve = '1G'
spark_memory_limit = '1250M'
initial_workers_ip = []
flavors_name_workers = [medium_flavor, medium_flavor, medium_flavor, medium_flavor, medium_flavor]
initial_workers_name = []

# Kafka info
agg_role = "iot-agg"
initial_aggs_ip = []
initial_aggs_name = []
kafka_memory_reserve = '412M'
kafka_memory_limit = '512M'
flavors_name_aggs = [small_flavor, small_flavor, small_flavor, small_flavor, small_flavor]

# cassandra info
ds_role = "iot-ds"
initial_ds_ip = []
initial_db_name = []
cassandra_memory_reserve = '2G'
cassandra_memory_limit = '3G'
cassandra_overlay_network_name = "cassandra"
flavors_name_datastore = [large_flavor]

# visualization on WaveCloud
wavecloud_token = 'hr1px97yozs5qw3gw33onsjykm9kh4of'

master_shell = ''
controller_shell = ''

util = Util()
regions_name = util.load_regions()
core = regions_name[0]  # the first one would be the core


# core_workers_name = ["core-worker"]


def print_green(prt): print("\033[92m {}\033[00m".format(prt))


def print_red(prt): print("\033[91m {}\033[00m".format(prt))


def print_cyan(prt): print("\033[96m {}\033[00m".format(prt))


def synchronized(func):
    func.__lock__ = threading.Lock()

    def synced_func(*args, **kws):
        with func.__lock__:
            return func(*args, **kws)

    return synced_func


def init(is_creation_time=False, local=False):
    global master_shell
    global controller_shell
    global swarm_master_ip
    controller_shell = ssh_to(controller_ip)
    if not is_creation_time and not local:
        swarm_master_ip = get_swarm_master_ip()
        master_shell = ssh_to(swarm_master_ip, user_name='ubuntu', node_name=swarm_master_name, mode='key')
    elif local:
        master_shell = ssh_to(controller_ip)
    load_initial_nodes_name()


def load_initial_nodes_name():
    global initial_workers_name, initial_aggs_name, initial_db_name
    initial_workers_name = util.load_initial_workers_node_names()
    initial_aggs_name = util.load_initial_aggregators_node_names()
    initial_db_name = util.load_initial_datastore_node_names()


def ssh_to(ip='127.0.0.1', user_name='', node_name='', mode='', passphrase=''):
    """Connect to the IoT controller to setup the cluster
        :param passphrase:
        :param mode: could be key or password based authentication
        :param node_name: the name of the node; this one is used to find the private key
        :param user_name: for ssh connection
        :param ip: is the ip or host name of the machine
        :return a shell connected to the local or remote machine
        This machine should have Docker, Docker-Machine and Swarm installed
    """
    if ip == "127.0.0.1":
        shell = spur.LocalShell()
        # result = shell.run(["sudo", ".", "savi-hamzeh", user, "demo2", core], allow_error=True, encoding='utf8')
        # if result.return_code > 0:
        #     print("\n***" + result.stderr_output)
    elif mode == 'key':
        shell = spur.SshShell(
            hostname=ip,
            username=user_name,
            private_key_file=privatekey_path_macos + node_name + "/id_rsa",
            missing_host_key=spur.ssh.MissingHostKey.accept
        )
    elif mode == 'password':
        shell = spur.SshShell(
            hostname=ip,
            username=user_name,
            password=passphrase
        )

    else:
        print('SSH has not been stabilised.')
        return
    result = shell.run(["hostname", "-fs"], allow_error=True, encoding='utf8')

    if result.return_code > 0:
        print("\n***" + result.stderr_output)
    return shell


def create_vm(vm_name, user_name, flavor, image, region, driver='openstack', ip=''):
    """
    Connect to the backend cloud service provider
    the cloud provider could be any driver supported by docker-machine
    :type driver: str supported as of now are: openstack and generic
    """
    if driver == 'openstack':
        result = controller_shell.run(
            ["docker-machine", "create", "--driver", driver, "--openstack-auth-url", auth_url,
             "--openstack-insecure", "--openstack-username", user_name,
             "--openstack-password", password,
             "--openstack-flavor-name", flavor, "--openstack-image-name", image,
             "--openstack-tenant-name", tenant_name, "--openstack-region", region,
             "--openstack-sec-groups", security_group, "--openstack-ssh-user", ssh_user, vm_name],
            store_pid="True", allow_error=True, encoding="utf8")

    elif driver == 'generic':
        result = controller_shell.run(
            ["docker-machine", "create", "--driver", driver, "--generic-ip-address=" + ip,
             "--generic-ssh-key", key, "--generic-ssh-user", user_name],
            store_pid="True", allow_error=True, encoding="utf8")

    if result.return_code > 0:
        print(result.stderr_output)


def delete_vm(name):
    """delete a VM using: docker-machine rm -f VM-name"""
    result = controller_shell.run(["docker-machine", "rm", "--force", name], allow_error=True, encoding="utf8")
    if result.return_code > 0:
        print_red(result.stderr_output)
    else:
        print_red(result.output)


class CreateVMThread(threading.Thread):
    def __init__(self, thread_id, vm_name, user_name, flavor, image, region):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.vm_name = vm_name
        self.user_name = user_name
        self.flavor = flavor
        self.image = image
        self.region = region

    def run(self):
        print(self.vm_name + " is being provisioned ...")
        create_vm(self.vm_name, self.user_name, self.flavor, self.image, self.region)
        print(self.vm_name + " is up and running with latest docker engine ...")


def provision_iot_controller(driver='', ip=''):
    global controller_shell
    shell = ssh_to(ip='127.0.0.1')
    print("\nCreating IoT controller on the CORE cloud ...")

    try:
        result = shell.run(["docker-machine", "help"], store_pid="True", allow_error=True, encoding='utf8')
        result = shell.run(["docker", "help"], store_pid="True", allow_error=True, encoding='utf8')
    except:
        print("You need to install Docker-Machine and/or Docker on your local machine manually.")

    if driver == 'openstack':
        create_vm(controller_name, user, small_flavor, ubuntu16, 'CORE', driver='openstack')
        iot_controller_ip = get_node_ip(controller_name)
        iot_controller_shell = ssh_to(iot_controller_ip, 'ubuntu', controller_name, mode='key')
        try:  # installing docker-machine
            iot_controller_shell.run(["wget",
                                      "https://github.com/docker/machine/releases/download/v0.10.0/docker-machine-Linux-x86_64"],
                                     store_pid="True", allow_error=True, encoding='utf8')
            iot_controller_shell.run(["chmod", "+x", "./docker-machine-Linux-x86_64"], store_pid="True",
                                     allow_error=True, encoding='utf8')
            iot_controller_shell.run(["mv", "./docker-machine-Linux-x86_64", "./docker-machine"], store_pid="True",
                                     allow_error=True, encoding='utf8')
            iot_controller_shell.run(["sudo", "mv", "./docker-machine", "/usr/local/bin/"],
                                     store_pid="True", allow_error=True, encoding='utf8')
            iot_controller_shell.run(["sudo", "rm", "-fr", "./docker/machine/certs"],
                                     store_pid="True", allow_error=True, encoding='utf8')
            iot_controller_shell.run(["sudo", "apt", "-y", "install", "python3-pip", "python-dev", "libffi-dev",
                                      "libssl-dev", "libxml2-dev", "libxslt1-dev", "libjpeg8-dev", "zlib1g-dev"],
                                     store_pid="True", allow_error=True, encoding='utf8')
            iot_controller_shell.run(["sudo", "pip3", "install", "spur"],
                                     store_pid="True", allow_error=True, encoding='utf8')

        except Exception as inst:
            print("Something went wrong when provisioning IoT controller.")
            print(inst.args)
        # here we set the IoT controller to the machine on the CORE Cloud
        controller_shell = ssh_to(iot_controller_ip, 'ubuntu', controller_name, mode='key')
        print("\nIoT controller has been created ...")


    elif driver == 'generic':  # use the ip address
        # todo: to be implemented later.
        print()


def provision_cluster():
    thread = [CreateVMThread(0, swarm_master_name, user, large_flavor, ubuntu14, core)]
    base = len(thread)

    for i in range(0, len(initial_workers_name)):
        thread.append(CreateVMThread(i + base, initial_workers_name[i], user, flavors_name_workers[i], ubuntu14,
                                     regions_name[i]))
        thread.append(CreateVMThread(i + base + len(initial_workers_name), initial_aggs_name[i], user,
                                     flavors_name_aggs[i], ubuntu14, regions_name[i]))

    for i in range(0, len(initial_db_name)):
        thread.append(CreateVMThread(i + base + len(initial_workers_name) + len(initial_aggs_name),
                                     initial_db_name[i], user, large_flavor, ubuntu14, core))

    for i in range(0, base + len(initial_workers_name) + len(initial_aggs_name) + len(initial_db_name)):
        thread[i].start()

    for i in range(0, base + len(initial_workers_name) + len(initial_aggs_name) + len(initial_db_name)):
        thread[i].join()


def deprovision_cluster():
    delete_vm(swarm_master_name)

    workers_name = util.load_worker_node_info()[0]
    aggs_name = util.load_aggregators_node_info()[0]

    # we don't have VM scalability for datastore for now, se we only delete the initial one in next block
    for i in range(0, len(workers_name)):
        delete_vm(workers_name[i])
        util.remove_node_info(workers_name[i], "workers_name")

    for i in range(0, len(aggs_name)):
        delete_vm(aggs_name[i])
        util.remove_node_info(aggs_name[i], "aggregators_name")

    # we don't remove initial node name from properties file
    for i in range(0, len(initial_workers_name)):
        delete_vm(initial_workers_name[i])

    for i in range(0, len(initial_aggs_name)):
        delete_vm(initial_aggs_name[i])

    for i in range(0, len(initial_db_name)):
        delete_vm(initial_db_name[i])


def get_token_and_master_ip_port():
    result = master_shell.run(["sudo", "docker", "swarm", "join-token", "worker"], store_pid="True", encoding="utf8")
    words = str(result.output).replace("\\", " ").replace("\n", " ").split(" ")
    token_index = words.index("--token") + 1

    token = words[token_index]
    master_ip_port = words[-3]
    return token, master_ip_port


def join_node_to_swarm_cluster(node_ip, node_name):
    token, master_ip_port = get_token_and_master_ip_port()
    shell = ssh_to(ip=node_ip, user_name='ubuntu', node_name=node_name, mode='key')
    with shell:
        result = shell.run(["sudo", "docker", "swarm", "join", "--token", token, master_ip_port],
                           store_pid="True", allow_error=True, encoding="utf8")
        if result.return_code > 0:
            print(result.stderr_output)
        else:
            print(result.output + node_name)


def create_swarm_cluster():
    global master_shell
    print("\nInit Swarm cluster ...")
    load_initial_workers_ip()
    load_initial_aggs_ip()
    load_initial_ds_ip()

    master_shell = ssh_to(swarm_master_ip, user_name='ubuntu', node_name=swarm_master_name, mode='key')

    result = master_shell.run(["sudo", "docker", "swarm", "init"], store_pid="True", encoding="utf8")
    if result.return_code > 0:
        print(result.stderr_output)
    else:
        print("\nJoining workers to the swarm cluster ...")
        for i in range(0, len(initial_workers_ip)):
            join_node_to_swarm_cluster(initial_workers_ip[i], initial_workers_name[i])

        print("\nJoining aggregators to the swarm cluster ...")
        for i in range(0, len(initial_aggs_ip)):
            join_node_to_swarm_cluster(initial_aggs_ip[i], initial_aggs_name[i])

        print("\nJoining datastores to the swarm cluster ...")
        for i in range(0, len(initial_ds_ip)):
            join_node_to_swarm_cluster(initial_ds_ip[i], initial_db_name[i])


def detach_swarm_cluster():
    load_initial_workers_ip()
    load_initial_aggs_ip()
    load_initial_ds_ip()
    edge_node_names, edge_node_ips = util.load_worker_node_info()
    agg_node_names, agg_node_ips = util.load_aggregators_node_info()

    for i in range(0, len(agg_node_ips)):
        remove_swarm_node(agg_node_names[i], agg_node_ips[i])

    for i in range(0, len(initial_aggs_ip)):
        remove_swarm_node(initial_aggs_name[i], initial_aggs_ip[i])

    for i in range(0, len(edge_node_ips)):
        remove_swarm_node(edge_node_names[i], edge_node_ips[i])

    for i in range(0, len(initial_workers_ip)):
        remove_swarm_node(initial_workers_name[i], initial_workers_ip[i])

    for i in range(0, len(initial_ds_ip)):
        remove_swarm_node(initial_db_name[i], initial_ds_ip[i])

    result = master_shell.run(["sudo", "docker", "swarm", "leave", "--force"], store_pid="True", allow_error=True,
                              encoding="utf8")
    if result.return_code > 0:
        print(result.stderr_output)
    else:
        print(swarm_master_name + " " + result.output)


def label_a_node(node_name, loc='', role=''):
    print("\nAdding labels:" + loc + ", " + role + " to node: " + node_name)

    result = master_shell.run(["sudo", "docker", "node", "update", "--label-add", "loc=" + loc,
                               "--label-add", "role=" + role, node_name], store_pid="True", encoding="utf8")
    # shell.run(["sudo", "docker", "node", "update", "--label-add", "role=" + role, node_name],
    #           store_pid="True", encoding="utf8")
    if result.return_code > 0:
        print(result.stderr_output)
    else:
        return str(result.output)


def label_nodes():
    label_a_node(swarm_master_name, loc=locations_name[0], role=manager_role)
    for i in range(0, len(regions_name)):
        label_a_node(initial_workers_name[i], loc=locations_name[i], role=edge_worker_role)
        label_a_node(initial_aggs_name[i], loc=locations_name[i], role=agg_role)
        print("Role and Location labels have been updated.")

    for i in range(0, len(initial_db_name)):
        label_a_node(initial_db_name[i], loc=locations_name[0], role=ds_role)


def get_swarm_master_ip():
    result = controller_shell.run(["docker-machine", "ip", swarm_master_name], store_pid="True", allow_error=True,
                                  encoding="utf8")
    if result.return_code > 0:
        print(result.stderr_output)
        return ""
    else:
        return str(result.output)[:-1]  # we do this to remove the \n at the end of the output


def get_node_ip(node_name):
    result = controller_shell.run(["docker-machine", "ip", node_name], store_pid="True", allow_error=True,
                                  encoding="utf8")
    if result.return_code > 0:
        print(result.stderr_output)
        return None
    else:
        return str(result.output)[:-1]  # we do this to remove the \n at the end of the output


def load_initial_workers_ip():
    global initial_workers_ip
    for i in range(0, len(initial_workers_name)):
        ip = get_node_ip(initial_workers_name[i])
        if ip is not None:
            initial_workers_ip.append(ip)


def load_initial_aggs_ip():
    global initial_aggs_ip
    for i in range(0, len(initial_aggs_name)):
        ip = get_node_ip(initial_aggs_name[i])
        if ip is not None:
            initial_aggs_ip.append(ip)


def load_initial_ds_ip():
    global initial_ds_ip
    for i in range(0, len(initial_db_name)):
        ip = get_node_ip(initial_db_name[i])
        if ip is not None:
            initial_ds_ip.append(ip)


def create_overlay_network(name):
    print("Creating the overlay network ...")
    result = master_shell.run(
        ["sudo", "docker", "network", "create", "--driver", "overlay", name],
        store_pid="True", allow_error=True, encoding="utf8")
    if result.return_code > 0:
        print(result.stderr_output)
    else:
        print("Overlay network has been created.")


def deploy_spark_cluster():
    """
    Deploy Spark cluster on Core and Edge nodes
    :return: a cluster of Spark
    """
    print("\nDeploying the Spark cluster ...")
    err_flag = False
    create_overlay_network(spark_overlay_network_name)
    command = ["sudo", "docker", "service", "create", "--name", "master",
               "--hostname", swarm_master_name,
               "--network", spark_overlay_network_name,
               "--constraint", "node.labels.role==" + manager_role,
               "-e", "NODE_TYPE=master",
               "-p", "7077:7077", "-p", "8080:8080",
               "--reserve-memory", spark_memory_reserve, "--limit-memory", spark_memory_limit,
               "gettyimages/spark:2.1.0-hadoop-2.7", "bin/spark-class", "org.apache.spark.deploy.master.Master"]

    result = master_shell.run(command, store_pid="True", allow_error=True, encoding="utf8")
    if result.return_code > 0:
        print(result.stderr_output)
        err_flag = True

    for i in range(0, len(initial_workers_name)):
        command = ["sudo", "docker", "service", "create", "--name", initial_workers_name[i],
                   "--network", spark_overlay_network_name,
                   "--constraint", "node.labels.loc==" + locations_name[i],
                   "--constraint", "node.labels.role==" + edge_worker_role,
                   "-p", "808" + str(i + 1) + ":8080",
                   "-e", "NODE_TYPE=slave",
                   "--reserve-memory", spark_memory_reserve,
                   "--limit-memory", spark_memory_limit, "gettyimages/spark:2.1.0-hadoop-2.7", "bin/spark-class",
                   "org.apache.spark.deploy.worker.Worker",
                   "spark://" + get_spark_master_ip("master") + ":7077"]
        # "spark://master:7077"]

        result = master_shell.run(command, store_pid="True", allow_error=True, encoding="utf8")
        if result.return_code > 0:
            print(result.stderr_output)
            err_flag = True

    if not err_flag:
        print("Spark Cluster has been deployed successfully.")
        print("\nSpark Master Management Page:", "http://" + swarm_master_ip + ":8080")
    else:
        print("Something went wrong with cluster provisioning.")


def deploy_kafka():
    print("\nDeploying Kafka on all aggregators ...")
    err_flag = False
    load_initial_aggs_ip()

    for i in range(0, len(initial_aggs_name)):
        result = master_shell.run(
            ["sudo", "docker", "service", "create", "--name", initial_aggs_name[i], "--constraint",
             "node.labels.loc==" + locations_name[i], "--constraint", "node.labels.role==" + agg_role, "-p",
             "218" + str(i) + ":2180", "-p", "909" + str(i) + ":9090", "--env",
             "ADVERTISED_HOST=" + initial_aggs_ip[i],
             "--env", "ADVERTISED_PORT=" + "909" + str(i), "--reserve-memory", kafka_memory_reserve,
             "--limit-memory", kafka_memory_limit, "spotify/kafka"], store_pid="True",
            allow_error=True, encoding="utf8")
        if result.return_code > 0:
            print(result.stderr_output)
            err_flag = True
    if not err_flag:
        print("Kafka has been deployed on all aggregators successfully.")
    else:
        print("Something went wrong with aggregators configuration.")


def deploy_cassandra():
    print("\nDeploying Cassandra on the CORE ...")
    err_flag = False
    create_overlay_network(cassandra_overlay_network_name)

    for i in range(0, len(initial_db_name)):
        command = ["sudo", "docker", "service", "create", "--name", initial_db_name[i],
                   "--network", cassandra_overlay_network_name,
                   "--constraint", "node.labels.loc==" + locations_name[0], "--constraint", "node.labels.role==" + ds_role,
                   "--reserve-memory", cassandra_memory_reserve, "--limit-memory", cassandra_memory_limit, "cassandra"]
        result = master_shell.run(command, store_pid="True", allow_error=True, encoding="utf8")
        if result.return_code > 0:
            print(result.stderr_output)
            err_flag = True
    if not err_flag:
        print("Cassandra has been deployed on the CORE successfully.")
    else:
        print("Something went wrong with Cassandra configuration.")


def deploy_rabbitmq():
    print("\nDeploying the Rabbit-MQ ...")
    command = ["sudo", "docker", "service", "create", "--name", "rabbitmq",
               "--publish=5001:15672/tcp", "--constraint", "node.labels.role==" + manager_role,
               "--reserve-memory", "512M", "--limit-memory", "1G", "rabbitmq:3-management"]
    result = master_shell.run(command, store_pid="True", allow_error=True, encoding="utf8")
    if result.return_code > 0:
        print(result.stderr_output)
    else:
        print("\nRabbitMQ Management Console:", "http://" + swarm_master_ip + ":5001")
        print("Both username and password are: guest")


def deploy_vis_monomarks():
    print("\nDeploying the MonoMarks Visualization ...")
    command = ["sudo", "docker", "service", "create", "--name", "viz",
               "--publish=5000:8080/tcp", "--constraint", "node.labels.role==" + manager_role,
               "--mount=type=bind,src=/var/run/docker.sock,dst=/var/run/docker.sock",
               "--reserve-memory", "512M", "--limit-memory", "1G", "manomarks/visualizer"]
    result = master_shell.run(command, store_pid="True", allow_error=True, encoding="utf8")
    if result.return_code > 0:
        print(result.stderr_output)
    else:
        print("\nIoT Platform Console:", "http://" + swarm_master_ip + ":5000\n")


def deploy_vis_weave():
    print("Deploying the Weave Dashboard ...")
    init(is_creation_time=False)
    thread = [ConnectToWeaveThread(swarm_master_ip, swarm_master_name, is_swarm_master=True)]

    for worker_name in initial_workers_name:
        thread.append(ConnectToWeaveThread(get_node_ip(worker_name), worker_name))

    for agg_name in initial_aggs_name:
        thread.append(ConnectToWeaveThread(get_node_ip(agg_name), agg_name))

    for db_name in initial_db_name:
        thread.append(ConnectToWeaveThread(get_node_ip(db_name), db_name))

    for i in range(0, len(thread)):
        thread[i].start()

    for i in range(0, len(thread)):
        thread[i].join()

    print("\nIoT Platform Weave Dashboard:", "http://" + swarm_master_ip + ":4040")


class ConnectToWeaveThread(threading.Thread):
    def __init__(self, node_ip, node_name, is_swarm_master=False):
        threading.Thread.__init__(self)
        self.node_ip = node_ip
        self.node_name = node_name
        self.is_swarm_master = is_swarm_master

    def run(self):
        connect_node_to_weave(self.node_ip, self.node_name, self.is_swarm_master)


def connect_node_to_weave(node_ip, node_name, is_swarm_master=False):
    if str(node_name).__contains__("ch-agg") or str(node_name).__contains__("ch-worker"):
        shell = ssh_to(node_ip, "cc", node_name, mode='key')
    else:
        shell = ssh_to(node_ip, ssh_user, node_name, mode='key')
    with shell:
        result = shell.run(["sudo", "curl", "-L", "git.io/scope", "-o", "/usr/local/bin/scope"],
                           store_pid="True", allow_error=True, encoding="utf8")
        if result.return_code > 0:
            print(result.stderr_output)
        else:
            result = shell.run(["sudo", "chmod", "a+x", "/usr/local/bin/scope"],
                               store_pid="True", allow_error=True, encoding="utf8")
        if result.return_code > 0:
            print(result.stderr_output)
        else:  # the token should be hard coded; otherwise it is not gonna work; I need to find out why.
            # this is for connecting to the weave cloud; I prefer the local setup. All probes send their report
            # to the master node; then the Weave app at master node renders all reports from cluster and shows
            # them in the browser at http://master_ip:4040.
            # result = shell.run(["sudo", "scope", "launch", "--service-token=hr1px97yozs5qw3gw33onsjykm9kh4of"],
            #                    store_pid="True", allow_error=True, encoding="utf8")
            if is_swarm_master:
                result = shell.run(["sudo", "scope", "launch"], store_pid="True", allow_error=True, encoding="utf8")
            else:
                result = shell.run(["sudo", "scope", "launch", swarm_master_ip],
                                   store_pid="True", allow_error=True, encoding="utf8")

        if result.return_code > 0:
            print(result.stderr_output)
        else:
            print(node_name + " is connected to Weave Dashboard.")


def scale_service(service_name, replicas):
    print("\nScaling service: " + service_name + " to new size: " + str(replicas))
    result = master_shell.run(
        ["sudo", "docker", "service", "scale", service_name + "=" + str(replicas)],
        store_pid="True", allow_error=True, encoding="utf8")
    if result.return_code > 0:
        print(result.stderr_output)
    else:
        print(service_name + " service has been scaled.")


def inspect_service(service_name, sudo=True):
    if sudo:
        result = master_shell.run(["sudo", "docker", "service", "inspect", service_name], store_pid="True",
                                  allow_error=True,
                                  encoding="utf8")
    else:
        result = master_shell.run(["docker", "service", "inspect", service_name], store_pid="True",
                                  allow_error=True,
                                  encoding="utf8")
    if result.return_code > 0:
        print(result.stderr_output)
    else:
        return str(result.output)


def inspect_all_agg_services():
    agg_services = util.load_initial_aggregators_node_names()
    result = master_shell.run(["sudo", "docker", "service", "inspect", agg_services[0], agg_services[1],
                               agg_services[2], agg_services[3]], store_pid="True", allow_error=True, encoding="utf8")
    if result.return_code > 0:
        print(result.stderr_output)
    else:
        return str(result.output)


def get_no_replicas(service_name):
    service_info = inspect_service(service_name)
    service_json = json.loads(service_info, encoding='utf8')
    current_replicas = int(service_json[0]['Spec']['Mode']['Replicated']['Replicas'])
    return current_replicas


def get_spark_master_ip(service_name):
    service_info = inspect_service(service_name, sudo=True)
    service_json = json.loads(service_info, encoding='utf8')
    master_ip = str(service_json[0]['Endpoint']['VirtualIPs'][0]['Addr']).split('/')[0]
    return master_ip


def get_all_agg_replicas():
    replicas = 0
    service_info = inspect_all_agg_services()
    service_json = json.loads(service_info, encoding='utf8')
    for service in service_json:
        replicas += int(service['Spec']['Mode']['Replicated']['Replicas'])

    return replicas


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


def remove_spark_service():
    for i in range(0, len(initial_workers_name)):
        master_shell.run(
            ["sudo", "docker", "service", "rm", initial_workers_name[i]], store_pid="True", allow_error=True,
            encoding="utf8")

    master_shell.run(["sudo", "docker", "service", "rm", "master"], store_pid="True", allow_error=True,
                     encoding="utf8")
    master_shell.run(["sudo", "docker", "network", "rm", spark_overlay_network_name], store_pid="True",
                     allow_error=True, encoding="utf8")
    print("Spark service has been deleted.")


def remove_cassandra_service():
    for i in range(0, len(initial_db_name)):
        master_shell.run(
            ["sudo", "docker", "service", "rm", initial_db_name[i]], store_pid="True", allow_error=True,
            encoding="utf8")

    master_shell.run(["sudo", "docker", "network", "rm", cassandra_overlay_network_name], store_pid="True",
                     allow_error=True, encoding="utf8")
    print("Cassandra service has been deleted.")


def remove_kafka_service():
    for i in range(0, len(initial_workers_name)):
        master_shell.run(
            ["sudo", "docker", "service", "rm", initial_aggs_name[i]], store_pid="True", allow_error=True,
            encoding="utf8")

    print("Kafka service has been deleted.")


def remove_swarm_node(node_name, node_ip=""):
    if node_ip == "":
        node_ip = get_node_ip(node_name)

    shell = ssh_to(node_ip, user_name='ubuntu', node_name=node_name, mode='key')
    result = shell.run(["sudo", "docker", "swarm", "leave"], store_pid="True", allow_error=True, encoding="utf8")
    if result.return_code > 0:
        print_red(result.stderr_output)
        return
    else:
        print_red(node_name + " " + result.output)

    result = master_shell.run(["sudo", "docker", "node", "rm", "--force", node_name], store_pid="True",
                              allow_error=True, encoding="utf8")
    if result.return_code > 0:
        print_red(result.stderr_output)
        return


def manipulate_services_replica(spark_master_rep=1, spark_worker_rep=1, kafka_rep=1, cassandra_rep=1, rabbit_rep=1,
                                viz_rep=1):
    """
    Use this function to set replica for all services to a specific value.
    Use 0 in order to remove all replicas. Node that this one doesn't remove the service.
    Use 1 for all to bring back the services to original states.
    """
    load_initial_nodes_name()

    for i in range(0, len(initial_workers_name)):
        scale_service(initial_workers_name[i], spark_worker_rep)

    for i in range(0, len(initial_aggs_name)):
        scale_service(initial_aggs_name[i], kafka_rep)

    for i in range(0, len(initial_db_name)):
        scale_service(initial_db_name[i], cassandra_rep)

    scale_service("master", spark_master_rep)
    scale_service("rabbitmq", rabbit_rep)
    scale_service("viz", viz_rep)


def down_scale_swarm_cluster_to_initial_state():
    init(is_creation_time=False)
    added_worker_nodes = util.load_worker_node_info()[0]
    added_agg_nodes = util.load_aggregators_node_info()[0]

    manipulate_services_replica(1, 1, 1, 1, 1, 1)
    for i in range(0, len(added_worker_nodes)):
        remove_swarm_node(added_worker_nodes[i])
        delete_vm(added_worker_nodes[i])
        util.remove_node_info(added_worker_nodes[i], "workers_name")

    for i in range(0, len(added_agg_nodes)):
        remove_swarm_node(added_agg_nodes[i])
        delete_vm(added_agg_nodes[i])
        util.remove_node_info(added_agg_nodes[i], "aggregators_name")

    monitor.init_monitoring()
    print("\n\nThe Swarm cluster is now back to original state with original services.")


def redeploy_services():
    """
    This method first bring the cluster to original stated and
    then redeploy the services.
    :return:
    """
    init(is_creation_time=False)
    load_initial_nodes_name()
    remove_spark_service()
    remove_kafka_service()

    deploy_spark_cluster()
    deploy_kafka()
    print("Services have been redeployed.")


def create_iot_platform():
    global swarm_master_ip
    t1 = time.time()
    init(is_creation_time=True)
    monitor.init_monitoring()
    # provision_iot_controller(driver='openstack')
    provision_cluster()
    swarm_master_ip = get_swarm_master_ip()  # we know which node is gonna be the master by its name.
    create_swarm_cluster()
    label_nodes()
    deploy_spark_cluster()
    deploy_kafka()
    deploy_rabbitmq()
    deploy_cassandra()
    deploy_vis_monomarks()
    deploy_vis_weave()
    t2 = time.time()
    print("\n\nApplication has been deployed in (seconds): ", t2 - t1)


# removes the IoT platform carelessly. Use with care.
def remove_iot_platform():
    t1 = time.time()
    init(is_creation_time=False)
    remove_spark_service()
    remove_kafka_service()
    remove_cassandra_service()
    detach_swarm_cluster()
    deprovision_cluster()
    monitor.init_monitoring()
    t2 = time.time()
    print("\n\nInfrastructure has been deprovisioned in (seconds): ", t2 - t1)


def hard_remove_iot_platform():
    global controller_shell
    print('Are you sure: (yes/no): ')
    ans = input()
    if ans == 'yes':
        controller_shell = ssh_to(controller_ip)
        result = controller_shell.run(["docker-machine", "ls"], store_pid="True", allow_error=True, encoding="utf8")
        if result.return_code > 0:
            print_red(result.stderr_output)
        else:
            array = str(result.output).split('\n')
            for element in array:
                if element.__contains__('agg') or element.__contains__('worker') or element.__contains__(
                        'db') or element.__contains__('swarm'):
                    delete_vm(element.split(' ')[0])
                    time.sleep(1)
        monitor.init_monitoring()
        print("The platform has been removed.")
    else:
        print("So, you are not sure. :-)")


if __name__ == "__main__":
    # init(True, local=False)
    # provision_iot_controller('openstack')
    # create_iot_platform()
    # remove_iot_platform()
    # redeploy_services()
    # down_scale_swarm_cluster_to_initial_state()
    hard_remove_iot_platform()
    # print(get_region_and_status("core-agg"))
    # deploy_vis_weave()
    # print(get_spark_master_ip("master"))
    # print(get_spark_master_ip("master"))
