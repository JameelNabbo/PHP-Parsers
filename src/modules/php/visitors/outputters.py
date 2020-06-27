"""Visitors for outputting information about the AST.
Used for debugging and visualizations
"""

import sys
# Add compiler path for imports
sys.path.insert(1, "../../compiler/php")

from base import Visitor
import graphviz
import phpast

class Printer(Visitor):
    """ Prints out information about the nodes visited for debugging
    purposes"""

    def __init__(self):
        self.namespace_stack = []

    def register_with(self, traverser):
        self.namespace_stack = traverser.namespace_stack

    def visit(self, node):
        print(type(node), end="  ")
        print(self.namespace_stack)

class GraphBuilder(Visitor):
    """ 
    Builds a graph as it walks through the AST.
    The ids of the Node objects are used as identifiers for the nodes
    on the graph.
    """

    def __init__(self):
        # Create the Graph
        self.graph = graphviz.Graph()

    def register_with(self, traverser):
        # Create the Root Node on the graph
        current_node_identifier = str(id(traverser.syntax_tree))
        self.graph.node(current_node_identifier, type(traverser.syntax_tree).__name__)

    def visit(self, current_node):
        # Create a node for all the Node children of current_node and 
        # connect the to it
        for field in current_node.fields:
            field_value = getattr(current_node, field)

            if isinstance(field_value, phpast.Node):
                self.build_node_and_edge(current_node, field_value, field)

            elif isinstance(field_value, list):
                for node in field_value:
                    if isinstance(node, phpast.Node):
                        self.build_node_and_edge(current_node, node, "")

    def build_node_and_edge(self, parent_node, child_node, link):
        # Utility function fo building a node for child_node and connecting it
        # to parent_node
        self.graph.node(str(id(child_node)), type(child_node).__name__)
        self.graph.edge(str(id(parent_node)), str(id(child_node)), link, dir="forwards")

