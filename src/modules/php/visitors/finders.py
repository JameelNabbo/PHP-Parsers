"""
Visitors for finding particular Nodes in the AST
- NameFinder: Takes a list of names and searches for them
- NameHighlighter: Takes a list of names and GraphBuilder reference.
  Highlights the found names on the graph built by the GraphBuilder
"""

import sys
try:
    import importlib_resources as pkg_resources
except:
    import importlib.resources as pkg_resources

import src.modules.php
from src.modules.php import syntax_tree
from src.modules.php.base import Visitor
from src.compiler.php import phpast

builtin_functions = pkg_resources.read_text(src.modules.php, "builtin_functions.txt")
builtin_functions = list(map(lambda x: x.strip(), builtin_functions))


def params_are_compatible(fn_def, fn_call):
    required_params = len(list(filter(lambda x: x.default is None, fn_def.params)))
    total_params = len(fn_def.params)
    return required_params <= len(fn_call.params) <= total_params


class NameFinder(Visitor):
    """
    Searches for all function or variable nodes with the specified names
    and returns a dictionary mapping the specified names to a list of the
    found results.

    Greedy specifies whether the search should stop at first match or
    continue to find as many results as it can
    """

    def __init__(self, names, greedy=True):
        self.traverser = None
        # The result of NameFinder. A dictionary mapping names that the finder
        # is initialized with to list containing the results of the search. 
        # None means no match was found
        self.names = {}
        for name in names:
            self.names[name] = []
        self.finished = False
        self.greedy = greedy # False means search should stop at first match

    def register_with(self, traverser):
        self.traverser = traverser

    def visit(self, current_node):
        if not self.finished:
            if isinstance(current_node, phpast.Function):
                if current_node.name in self.names.keys():
                    node_details = {
                        "node": current_node,
                        "type": "Function Declaration",
                        "namespace_stack": [*self.traverser.namespace_stack]
                    }
                    self.names[current_node.name].append(node_details)
                    if not self.greedy:
                        self.finished = True
            elif isinstance(current_node, phpast.Assignment):
                if isinstance(current_node.node, phpast.Variable):
                    var_name = current_node.node.name[1:]
                    if var_name in self.names.keys():
                        node_details = {
                            "node": current_node,
                            "type": "Variable Declaration",
                            "namespace_stack": [*self.traverser.namespace_stack]
                        }
                        self.names[var_name].append(node_details)
                        if not self.greedy:
                            self.finished = True

class NameHighlighter(Visitor):
    """
    With the specified list of names and GraphBuilder instance, it searches
    for the variable and function nodes matching the names and highlights them
    on the graph
    """

    def __init__(self, names, graph, greedy=True):
        self.names = names
        self.graph_builder = graph
        self.greedy = greedy

    def register_with(self, traverser):
        pass

    def visit(self, current_node):
        if isinstance(current_node, phpast.Function):
            if current_node.name in self.names:
                self.graph_builder.graph.node(str(id(current_node)), color="red")
                if not self.greedy:
                    self.names.remove(current_node.name)
        elif isinstance(current_node, phpast.Assignment):
            if isinstance(current_node.node, phpast.Variable):
                variable_name = current_node.node.name[1:]
                if variable_name in self.names:
                    self.graph_builder.graph.node(str(id(current_node)), color="red")
                    if not self.greedy:
                        self.names.remove(current_node.name)


class NodeFinder(Visitor):
    """Visitor for finding nodes based on a particular filter callback.
    Collects information about all nodes for which the callback returns
    True
    """
    def __init__(self, callback):
        self.callback = callback
        self.namespace_stack = []
        self.found = []

    def register_with(self, traverser):
        self.namespace_stack = traverser.namespace_stack

    def visit(self, current_node):
        if self.callback(current_node):
            self.found.append({
                "node": current_node,
                "namespace_stack": [*self.namespace_stack]
            })


class ResourceCallsFinder(NameFinder):
    """

    Catches all Function and method calls and searches for all the function
    and method definitions in the resource tree with the same name.

     - rt_root: Instance of the ResourceTree of the project
     - ignore_builtins: Specifies whether the Finder should omit any calls
       to built in functions. (specified by the global builtin_functions)
     - match_params: Specifies whether the Finder should only collect definitions
       that have parameters compatible with the function/method calls

   """

    def __init__(self, rt_root, ignore_builtins=True, match_params=False, debug=False):
        self.rt_root = rt_root
        self.traverser = None
        self.bound_calls = []
        self.unbound_calls = []
        self.debug = debug
        self.ignore_builtins = ignore_builtins
        self.match_params = match_params

    def visit(self, current_node):
        if type(current_node) in (phpast.FunctionCall, phpast.MethodCall):
            is_bound = isinstance(current_node, phpast.MethodCall)

            if isinstance(current_node, phpast.FunctionCall):
                if self.ignore_builtins and current_node.name in builtin_functions:
                    return

            try:
                found_definitions = self.rt_root.function_finder(current_node.name, bound=is_bound)
            except:
                if self.debug:
                    print("MethodCall Name could not be resolved")
                return

            if self.match_params:
                if not is_bound:
                    found_definitions = filter(lambda x: params_are_compatible(x[1], current_node), found_definitions)
                else:
                    found_definitions = filter(lambda x: params_are_compatible(x[1][0], current_node), found_definitions)

            call_details = {
                "stack": self.traverser.namespace_stack + [current_node],
                "found_definitions": list(found_definitions)
            }
            if is_bound:
                self.bound_calls.append(call_details)
            else:
                self.unbound_calls.append(call_details)
