import configparser
import json
from collections import OrderedDict

"""
This file provides functions to manipulate the config file which
has the initial parameters and settings.
"""


def print_green(message):
    print("\033[92m {}\033[00m".format(message))


def print_red(message):
    print("\033[91m {}\033[00m".format(message))


class Util:

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.property_file = "./input/properties.ini"
        self.config.read(self.property_file)

    def load_initial_workers_node_names(self):
        """ initial node names are the same the service names."""
        node_array = []
        initial_worker_name = self.config['Nodes']['initial_workers_name']
        # the second parameter is to get load node_names in order of file
        init_worker_name_json = json.loads(initial_worker_name, object_pairs_hook=OrderedDict)

        for node_name in init_worker_name_json['names']:
            node_array.append(node_name)
        return node_array

    def load_regions(self):
        region_array = []
        core = self.config['Regions']['core']
        edges = self.config['Regions']['edges']
        core_json = json.loads(core, object_pairs_hook=OrderedDict)
        edges_json = json.loads(edges, object_pairs_hook=OrderedDict)

        for node_name in core_json['names']:
            region_array.append(node_name)

        for node_name in edges_json['names']:
            region_array.append(node_name)

        return region_array

    def load_initial_aggregators_node_names(self):
        """ initial node name are the same service names."""
        node_array = []
        initial_agg_name = self.config['Nodes']['initial_aggregators_name']
        agg_name_json = json.loads(initial_agg_name, object_pairs_hook=OrderedDict)

        for node_name in agg_name_json['names']:
            node_array.append(node_name)
        return node_array

    def load_initial_datastore_node_names(self):
        """ initial node name are the same service names."""
        node_array = []
        initial_ds_name = self.config['Nodes']['cassandra']
        agg_name_json = json.loads(initial_ds_name, object_pairs_hook=OrderedDict)

        for node_name in agg_name_json['names']:
            node_array.append(node_name)
        return node_array

    def load_worker_node_info(self):
        node_names = []
        node_ips = []
        worker_name = self.config['Nodes']['workers_name']
        # the second parameter is to get node_names in order of file
        edge_worker_name_json = json.loads(worker_name, object_pairs_hook=OrderedDict)

        for node_name in edge_worker_name_json['names']:
            node_names.append(node_name)
            node_ips.append(edge_worker_name_json['names'][node_name])
        return node_names, node_ips

    def load_aggregators_node_info(self):
        node_names = []
        node_ips = []
        agg_worker_name = self.config['Nodes']['aggregators_name']
        agg_name_json = json.loads(agg_worker_name, object_pairs_hook=OrderedDict)

        for node_name in agg_name_json['names']:
            node_names.append(node_name)
            node_ips.append(agg_name_json['names'][node_name])
        return node_names, node_ips

    def add_node_info(self, node_name, ip, group):
        node_names = self.config['Nodes'][group]
        node_names_json = json.loads(node_names)
        node_names_json['names'][node_name] = ip
        node_names_dump = json.dumps(node_names_json)
        self.config['Nodes'][group] = node_names_dump
        with open(self.property_file, 'w') as conf_file:
            self.config.write(conf_file)
        print("Node " + node_name + " has been added to properties file.")

    def remove_node_info(self, node_name, group):
        node_names = self.config['Nodes'][group]
        node_names_json = json.loads(node_names)
        del node_names_json['names'][node_name]
        node_names_dump = json.dumps(node_names_json)
        self.config['Nodes'][group] = node_names_dump
        with open(self.property_file, 'w') as conf_file:
            self.config.write(conf_file)
        print_red("Node " + node_name + " has been removed from properties file.")


if __name__ == "__main__":
    util = Util()
    print(util.load_regions())
