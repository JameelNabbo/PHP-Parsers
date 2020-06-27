import sys
import os
import collections

from src.compiler.php import phpast

from src.modules.php.base import Traverser, Visitor
from src.modules.php import syntax_tree

class BFTraverser(Traverser):
    """Performs a Breadth-First Traversal on the syntax_tree"""

    def __init__(self, syntax_tree, visitors=[]):
        self.syntax_tree = syntax_tree
        # nearest_ns_parent is the last parent of a node that is a SyntaxTree, Class, 
        # Function or Namespace (Nearest Namespace Parent). For the root
        # node, it is None. Keeping track of the namespace stack in BFT was 
        # quite complicated so I had to use this.
        self.syntax_tree.nearest_ns_parent = None
        self.namespace_stack = []

        for visitor in visitors:
            visitor.register_with(self)
        self.visitors = [*visitors]

    def register_visitor(self, new_visitor):
        if new_visitor not in self.visitors:
            new_visitor.register_with(self)
            self.visitors.append(new_visitor)
        else:
            raise Exception("Visitor already registered with Traverser")

    def traverse(self):
        # Queue of Nodes to visit
        queue = collections.deque([self.syntax_tree])

        while len(queue):
            current_node = queue.popleft()

            # Enter Node
            for visitor in self.visitors:
                visitor.enter(current_node)

            # Only let Node instances past this
            if not isinstance(current_node, phpast.Node):
                continue

            self.resolve_namespace(current_node) # Updates the Namespace Stack

            # If current node defines a Namespace, change the Nearest
            # Namespace Parent of all the child nodes
            if type(current_node) in (syntax_tree.SyntaxTree, phpast.Class, phpast.Function, phpast.Namespace, phpast.Interface):
                child_nearest_ns_parent = current_node
            else:
                # Otherwise keep it the same as the current node
                child_nearest_ns_parent = current_node.nearest_ns_parent

            # Traverse Node
            for visitor in self.visitors:
                current_node.accept(visitor)

            # Add all the Node children of current node to the queue
            for field in current_node.fields:
                field_value = getattr(current_node, field)
                if isinstance(field_value, phpast.Node):
                    queue.append(field_value)
                    # Set the nearest namespace parent of children
                    field_value.nearest_ns_parent = child_nearest_ns_parent
                elif isinstance(field_value, list):
                    queue.extend(field_value)
                    for field_value_node in field_value:
                        if isinstance(field_value_node, phpast.Node):
                            field_value_node.nearest_ns_parent = child_nearest_ns_parent

            for visitor in self.visitors:
                visitor.leave(current_node)

    def resolve_namespace(self, node):
        self.namespace_stack.clear() # Empty the namespace first
        nearest_parent = node.nearest_ns_parent
        # Populate it by backtracking the Nearest Namespace Parents
        while nearest_parent is not None:
            self.namespace_stack.insert(0, nearest_parent)
            nearest_parent = nearest_parent.nearest_ns_parent
