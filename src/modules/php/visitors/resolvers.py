"""Visitors that make certain mutations to the AST"""

import sys
import os

from src.modules.php import syntax_tree
from src.modules.php.base import Visitor
from src.compiler.php import phpast

class CircularImport(phpast.Node):
    fields = ["file_name"]
    def __init__(self, child_path, looping_tree):
        self.looping_tree = looping_tree
        self.file_name = os.path.basename(child_path)


class DependencyResolver(Visitor):
    """Expands the tree by augmenting the ASTs for files added in it using
       Include and Require tags
       Should preceed any visitors that depend on it.
    """
    def __init__(self, debug=False):
        self.namespace_stack = []
        self.constants = {}
        self.expr_fails = []
        self.not_found = []
        self.debug = debug
        self.current_file_tree = None

    def visit(self, current_node):
        if isinstance(current_node, phpast.Include) or isinstance(current_node, phpast.Require):
            # Get the last file visited by getting the last SyntaxTree element 
            # of the namespace_stack.
            # This is required to properly form the absolute path for the 
            # file in the Include/Require
            current_tree_stack = [tree for tree in self.namespace_stack if isinstance(tree, syntax_tree.SyntaxTree)]
            self.current_file_tree = current_tree_stack[-1]

            # Get the Syntax tree for the node (Include/Require) and augment it 
            # to the node by using previous file included as base path
            file_to_build = self.evaluate_require(current_node.expr)
            dependency_path = os.path.join(self.current_file_tree.file_location, file_to_build)
            dependency_path = os.path.normpath(dependency_path)

            # Counter Circular Imports
            for file_tree in current_tree_stack:
                if dependency_path == file_tree.file_path:
                    ci_node = CircularImport(child_path=dependency_path, looping_tree=file_tree)
                    current_node.body = ci_node
                    break
            else:
                self.follow_dependency(current_node, dependency_path)

        elif isinstance(current_node, phpast.FunctionCall):
            if current_node.name == "define":
                constant_name = current_node.params[0].node
                try:
                    constant_value = current_node.params[1].node
                    self.constants[constant_name] = constant_value
                except:
                    pass

    def register_with(self, traverser):
        # Add a reference to Traverser's namespace stack so that we can
        # access it from this visitor
        self.namespace_stack = traverser.namespace_stack

    def follow_dependency(self, node, dependency_path):

        if not os.path.isfile(dependency_path):
            dp_file = os.path.basename(dependency_path)
            if self.debug:
                print("Require/Include Error")
                print(f"File {dp_file} does not exist")
                print(f"Line: {node.lineno}")
            self.not_found.append((dependency_path, node.lineno, 
                                   self.current_file_tree.file_path))

        else:
            file_handle = open(dependency_path, "r")
            sub_ast = syntax_tree.SyntaxTree(file_handle)
            node.body = sub_ast

    def evaluate_require(self, expr):
        """
        Takes the 'expr' block of a require/include call and
        reduces it to the actual string produced from that expression
        """
        if isinstance(expr, str):
            return expr

        elif isinstance(expr, phpast.BinaryOp):
            if expr.op == ".":
                return self.evaluate_require(expr.left) + self.evaluate_require(expr.right)

        elif isinstance(expr, phpast.Constant):
            const_value = self.constants.get(expr.name)
            if not isinstance(const_value, str):
                return "[PATH]"
            if const_value is None:
                const_value = "[PATH]"
                self.expr_fails.append((expr, expr.lineno, self.current_file_tree.file_path ))
            return const_value

        else:
            self.expr_fails.append((expr, expr.lineno, self.current_file_tree.file_path ))
            return "[PATH]"


class ResourceDependencyResolver(DependencyResolver):

    def __init__(self, resource_tree_root, debug=False):
        self.rt_root = resource_tree_root
        self.namespace_stack = []
        self.not_found = []
        self.expr_fails = []
        self.constants = {}
        self.debug = debug

    def follow_dependency(self, node, dependency_path, debug=False):
        try:
            sub_ast = self.rt_root.trees[dependency_path]
            node.body = sub_ast
        except:
            if self.debug:
                print(f"File not found at {dependency_path}")
            self.not_found.append((dependency_path, node.lineno, self.current_file_tree.file_path))

    def visit(self, current_node):

        file_stack = [tree for tree in self.namespace_stack if \
                      isinstance(tree, syntax_tree.SyntaxTree)]
        if file_stack:
            last_file = file_stack[-1]

        super().visit(current_node)  # Connects the Included ASTs

        if type(current_node) in (phpast.Include, phpast.Require):
            if isinstance(current_node.body, syntax_tree.SyntaxTree):
                self.rt_root.dep_table[last_file.file_path].append(current_node.body)


class TablesBuilder(Visitor):
    def __init__(self, rt_root):
        self.rt_root = rt_root
        self.namespace_stack = []

    def register_with(self, traverser):
        self.namespace_stack = traverser.namespace_stack

    def visit(self, current_node):

        file_stack = [tree for tree in self.namespace_stack if \
                      isinstance(tree, syntax_tree.SyntaxTree)]
        if not file_stack: return  # Don't go further if we are not in a file yet
        last_file = file_stack[-1]

        if isinstance(current_node, phpast.Function):
            self.rt_root.function_table[last_file.file_path][current_node.name] = current_node

        elif isinstance(current_node, phpast.Method):
            last_ns_node = self.namespace_stack[-1]
            if isinstance(last_ns_node, phpast.Class):
                self.rt_root.method_table[last_file.file_path][current_node.name] = (current_node, last_ns_node)

        elif type(current_node) in (phpast.Include, phpast.Require):
            if isinstance(current_node.body, syntax_tree.SyntaxTree):
                self.rt_root.dep_table[last_file.file_path].append(current_node.body)

