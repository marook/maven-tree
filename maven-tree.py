#!/usr/bin/python2

import argparse
import os
import pygraphml
import sys
import xml.etree.ElementTree as xml

MAVEN_NAMESPACES = {
    'mvn': 'http://maven.apache.org/POM/4.0.0',
}

def main(graph_output_path, pom_root_paths):
    maven_modules = find_maven_modules(pom_root_paths)

    graph = DependencyGraphBuilder().build_graph(maven_modules)

    write_graph(graph_output_path, graph)

def find_maven_modules(pom_root_paths):
    for pom_root_path in pom_root_paths:
        for current_dir_path, subdirs, files in os.walk(pom_root_path):
            if('pom.xml' in files):
                yield parse_maven_module_from_pom(os.path.join(current_dir_path, 'pom.xml'))

def parse_maven_module_from_pom(pom_path):
    pom = xml.parse(pom_path)

    group_id, artifact_id = parse_artifact_ids_from_pom(pom)

    if(group_id is None):
        raise Exception('Missing groupId')

    if(artifact_id is None):
        raise Exception('Missing artifactId')

    maven_module = MavenModule(group_id, artifact_id)

    maven_module.dependencies.update(parse_dependencies_from_pom(pom))

    return maven_module

def parse_dependencies_from_pom(pom):
    for dependency_node in pom.findall('mvn:dependencies/mvn:dependency', MAVEN_NAMESPACES):
        dep_group_id, dep_artifact_id = parse_artifact_ids_from_node(dependency_node)

        yield MavenModule(dep_group_id, dep_artifact_id)

def parse_artifact_ids_from_pom(pom):
    project_node = pom.getroot()

    group_id, artifact_id = parse_artifact_ids_from_node(project_node)

    if(group_id is None):
        parent_group_id, parent_artifact_id = parse_parent_artifact_ids_from_project_node(project_node)

        group_id = parent_group_id

    return (group_id, artifact_id)

def parse_parent_artifact_ids_from_project_node(project_node):
    for parent_node in project_node.findall('mvn:parent', MAVEN_NAMESPACES):
        return parse_artifact_ids_from_node(parent_node)

    return (None, None)

def parse_artifact_ids_from_node(node):
    return (get_child_node_value(node, 'groupId'), get_child_node_value(node, 'artifactId'))

def get_child_node_value(parent_node, child_node_name):
    for child_node in parent_node.findall('mvn:%s' % (child_node_name, ), MAVEN_NAMESPACES):
        return child_node.text

    return None

class DependencyGraphBuilder(object):

    def __init__(self):
        self.graph = pygraphml.Graph()

        self.maven_module_nodes = {}

    def build_graph(self, maven_modules):
        for maven_module in maven_modules:
            maven_module_node = self.get_maven_module_node(maven_module)

            self.add_dependency_edges(maven_module)

        return self.graph

    def add_dependency_edges(self, maven_module):
        maven_module_node = self.get_maven_module_node(maven_module)

        for dependency_module in maven_module.dependencies:
            dependency_module_node = self.get_maven_module_node(dependency_module)

            self.graph.add_edge(maven_module_node, dependency_module_node)

    def get_maven_module_node(self, maven_module):
        if(maven_module in self.maven_module_nodes):
            return self.maven_module_nodes[maven_module]
        else:
            node_id = '%s:%s' % (maven_module.group_id, maven_module.artifact_id)
            maven_module_node = self.graph.add_node(node_id)

            self.maven_module_nodes[maven_module] = maven_module_node

            return maven_module_node

def write_graph(graph_output_path, graph):
    pygraphml.GraphMLParser().write(graph, graph_output_path)

class MavenModule(object):

    def __init__(self, group_id, artifact_id):
        self.group_id = group_id
        self.artifact_id = artifact_id
        self.dependencies = set()

        self._id = None

    @property
    def id(self):
        if(self._id is None):
            self._id = (self.group_id, self.artifact_id)

        return self._id

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

def parse_args():
    parser = argparse.ArgumentParser(description='maven dependency tree graph builder')

    parser.add_argument('graph_output_file', metavar='GRAPH_OUTPUT_FILE', help='the generated graph is written to that file')

    parser.add_argument('maven_module_paths', metavar='MAVEN_MODULE_DIR', nargs='+', help='directories which will be recursively searched for pom.xml files')

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()

    main(args.graph_output_file, args.maven_module_paths)
