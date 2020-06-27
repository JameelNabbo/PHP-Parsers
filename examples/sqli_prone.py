""" Script for finding statements prone to SQL Injection """
import sys
sys.path.append("../")
sys.path.append("./")

from src.compiler.php import phpast
from src.modules.php import syntax_tree
from src.modules.php.traversers.bf import BFTraverser


from src.modules.php.visitors.resolvers import DependencyResolver
from src.modules.php.visitors.finders import NodeFinder

a = open(sys.argv[1])

s = syntax_tree.SyntaxTree(a)
t = BFTraverser(s)

# Callback for NodeFinder
def is_prone_to_sqli(current_node):
    if isinstance(current_node, phpast.FunctionCall):
        if current_node.name in ["mysql_query", "mssql_query", "mysqli_query", "pg_query"]:
            return True
    return False

d = DependencyResolver()
f = NodeFinder(callback=is_prone_to_sqli)

t.register_visitor(d)
t.register_visitor(f)

t.traverse()

# Evaluate and print the output of f
if not f.found:
    print("No SQLInjection-prone Function Calls Found")
else:
    print(f"\n{len(f.found)} function calls in your code are prone to SQL Injection\n")
    for i, result in enumerate(f.found):
        print(f"Result #{i+1}")
        print(f"Function Call on {result['node'].lineno} in Line ")
        print("Namespace Stack:")
        for namespace in result["namespace_stack"]:
            if isinstance(namespace, syntax_tree.SyntaxTree):
                print(f"--> File: {namespace.file_path}")
            else:
                print(f"--> {type(namespace).__name__}: ", end="")
                print(f"{namespace.name}")
        print()
