import random
import time

import infrastructure_management as im
from autonomic_manager import scale_kafka_service
from util import Util

util = Util()

# the lifetime of an aggregator in second
aggregator_lifetime = 30


def print_red(prt): print("\033[91m {}\033[00m".format(prt))


def start_death_process(lifetime):
    """
    This function every lifetime downscales the service to
    imitate the exiting of an aggregator container.
    Here we are trying to create a birth-death process.
    :param lifetime:
    :return:
    """
    print_red("Death process get started ...")
    agg_services = util.load_initial_aggregators_node_names()
    while True:
        service = agg_services[random.randint(0, len(agg_services) - 1)]
        count = im.get_all_agg_replicas()
        sample_lifetime = random.expovariate(count / lifetime)
        time.sleep(sample_lifetime)
        scale_kafka_service(service, -1)


start_death_process(aggregator_lifetime)
