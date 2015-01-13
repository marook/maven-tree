#!/usr/bin/python2

import pygraphml

def main(graph_output_path, pom_root_paths):
    maven_modules = find_maven_modules(pom_root_paths)

    graph = DependencyGraphBuilder().build_graph(maven_modules)

    write_graph(graph_output_path, graph)

def find_maven_modules(pom_root_paths):
    for pom_root_path in pom_root_paths:
        pass

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
            node_id = '%s:%s' % (maven_module.package_id, maven_module.artifact_id)
            maven_module_node = self.graph.add_node(node_id)

            self.maven_module_nodes[maven_module] = maven_module_node

            return maven_module_node

def write_graph(graph_output_path, graph):
    pygraphml.GraphMLParser().write(graph, graph_output_path)

class MavenModule(object):

    def __init__(self, package_id, artifact_id, version):
        self.package_id = package_id
        self.artifact_id = artifact_id
        self.dependencies = set()

    # TODO equals and hash functions

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
