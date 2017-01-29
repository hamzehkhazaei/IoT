import threading
import time

import infrastructure_management as ci
from util import Util

metrics_file = './output/monitor.txt'
rt_metrics_file = './output/rt_monitor.txt'
metrics = []
util = Util()
default_interval_sec = 3


def print_green(prt): print("\033[92m {}\033[00m".format(prt))


def init_monitoring():
    headers = ['Time', 'CORE-spark-VM', 'CG-spark-VM', 'CT-spark-VM', 'VC-spark-VM',
               'CORE-kafka-VM', 'CG-kafka-VM', 'CT-kafka-VM', 'VC-kafka-VM', 'CORE-cassandra-VM',
               'CORE-spark-cont', 'CG-spark-cont', 'CT-spark-cont', 'VC-spark-cont',
               'CORE-kafka-cont', 'CG-kafka-cont', 'CT-kafka-cont', 'VC-kafka-cont',
               'CORE-cassandra-cont']
    rt_headers = ['Time', 'Resp-Time-VM', 'Resp-Time-cont', 'Region', 'Flavor', 'Role', 'Name']

    with open(metrics_file, 'w') as f:
        for i in range(0, len(headers)):
            f.write(headers[i].ljust(20, ' '))
        f.write('\n')
        f.write('-' * 380 + '\n')
    f.close()

    with open(rt_metrics_file, 'w') as f:
        for i in range(0, len(rt_headers)):
            f.write(rt_headers[i].ljust(20, ' '))
        f.write('\n')
        f.write('-' * 150 + '\n')
    f.close()


def get_vm_metrics():
    global metrics
    metrics.append(int(time.time()))
    init_workers_name = util.load_initial_workers_node_names()
    init_aggs_name = util.load_initial_aggregators_node_names()
    init_dbs_name = util.load_initial_datastore_node_names()

    no_spark_vms = [0] * len(init_workers_name)
    no_kafka_vms = [0] * len(init_aggs_name)
    no_db_vms = [0] * len(init_dbs_name)
    ip = ci.get_swarm_master_ip()
    shell = ci.ssh_to(ip, 'ubuntu', ci.swarm_master_name)
    with shell:
        result = shell.run(["sudo", "docker", "node", "ls"], store_pid="True", allow_error=True, encoding="utf8")
        if result.return_code > 0:
            print(result.stderr_output)
        else:
            info = str(result.output).split("\n")
            for i in range(0, len(info)):
                for j in range(0, len(init_workers_name)):  # no workers and aggs are the same
                    if info[i].__contains__(init_workers_name[j]):
                        no_spark_vms[j] += 1
                    elif info[i].__contains__(init_aggs_name[j]):
                        no_kafka_vms[j] += 1

                for k in range(0, len(init_dbs_name)):
                    if info[i].__contains__(init_dbs_name[k]):
                        no_db_vms[k] += 1
    metrics.extend(no_spark_vms)
    metrics.extend(no_kafka_vms)
    metrics.extend(no_db_vms)


def get_cont_metrics():
    global metrics
    init_workers_name = util.load_initial_workers_node_names()
    init_aggs_name = util.load_initial_aggregators_node_names()
    init_dbs_name = util.load_initial_datastore_node_names()

    no_spark_cont = [0] * len(init_workers_name)
    no_kafka_cont = [0] * len(init_aggs_name)
    no_db_cont = [0] * len(init_dbs_name)

    for i in range(0, len(init_workers_name)):
        no_spark_cont[i] = ci.get_no_replicas(init_workers_name[i])
        no_kafka_cont[i] = ci.get_no_replicas(init_aggs_name[i])

    for i in range(0, len(init_dbs_name)):
        no_db_cont[i] = ci.get_no_replicas(init_dbs_name[i])

    metrics.extend(no_spark_cont)
    metrics.extend(no_kafka_cont)
    metrics.extend(no_db_cont)


def get_metrics():
    get_vm_metrics()
    get_cont_metrics()
    return metrics


def log_metrics():
    get_metrics()
    with open(metrics_file, 'a') as f:
        f.write(str(metrics[0]).ljust(25, ' '))  # do the first one here to make numbers centrally justified.
        for i in range(1, len(metrics)):
            f.write(str(metrics[i]).ljust(20, ' '))
        f.write('\n')


def log_rt_metrics(rt_metrics):
    """
    Here we log response time for both VMs and Containers
    If it is VM, then for container we put 0 and vice versa.
    As opposed to logging for other metrics, this function will be called on demand.
    :param rt_metrics: includes vm response time, cont response time, name, region, flavor, role
    :return:
    """
    with open(rt_metrics_file, 'a') as f:
        f.write(str(rt_metrics[0]).ljust(20, ' '))
        for i in range(1, len(rt_metrics)):
            f.write(str(rt_metrics[i]).ljust(20, ' '))
        f.write('\n')


def do_monitoring(interval=default_interval_sec):
    ci.init(False)
    while True:
        log_metrics()
        print_green("\nLogged at: " + time.strftime("%Y-%m-%d.%H-%M-%S", time.localtime()))
        metrics.clear()
        time.sleep(interval)


class StartMonitoringThread(threading.Thread):
    def __init__(self, interval=default_interval_sec):
        threading.Thread.__init__(self)
        self.interval = interval

    def run(self):
        print_green("Starting monitoring ...")
        do_monitoring(interval=self.interval)


if __name__ == "__main__":
    # ci.init(False)
    do_monitoring()
    # init_monitoring()
    # get_vm_metrics()
    # print(metrics)
    # smp_met = [int(time.time()), 120, 3, 'core-agg', 'CORE', 'm1.small', 'worker']
    # log_rt_metrics(smp_met)
