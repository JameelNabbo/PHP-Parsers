import sys
import os

from src.compiler.php import phpast
from src.modules.php import syntax_tree
from src.modules.php.base import Traverser

class DFTraverser(Traverser):
    """ Recursive Depth First Traverser"""

    def __init__(self, syntax_tree, visitors=[]):
        self.syntax_tree = syntax_tree
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

    def traverse(self, current_node=None):
        # Visitor Enters
        for visitor in self.visitors:
            visitor.enter(current_node)

        if len(self.namespace_stack) == 0:
            # On first iteration
            current_node = self.syntax_tree

        # Only let Node instances past this
        if not isinstance(current_node, phpast.Node):
            return

        for visitor in self.visitors:
            # Visitor Visits
            current_node.accept(visitor)

        if type(current_node) in (syntax_tree.SyntaxTree, phpast.Class, phpast.Function, phpast.Namespace, phpast.Interface):
            # Update the namespace stack
            self.namespace_stack.append(current_node)

        # Recurse 
        for field in current_node.fields:
            field_value = getattr(current_node, field)
            if isinstance(field_value, phpast.Node):
                self.traverse(current_node=field_value)
            elif isinstance(field_value, list):
                for node in field_value:
                    self.traverse(current_node=node)

        # Remove the current_node from the stack before the traverser
        # gets out of it
        if type(current_node) in (syntax_tree.SyntaxTree, phpast.Class, phpast.Function, phpast.Namespace):
            self.namespace_stack.pop()

        for visitor in self.visitors:
            # Visitor Leaves
            visitor.leave(current_node)
