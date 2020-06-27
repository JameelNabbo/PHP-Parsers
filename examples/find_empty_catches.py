import sys

sys.path.insert(1, "../")
from src.compiler.php import phpast
from src.modules.php import syntax_tree
from src.modules.php.traversers.bf import BFTraverser

from src.modules.php.visitors.resolvers import DependencyResolver
from src.modules.php.visitors.finders import NodeFinder

a = open(sys.argv[1])

s = syntax_tree.SyntaxTree(a)
t = BFTraverser(s)

# Callback for NodeFinder
def try_has_empty_catch(current_node):
    if isinstance(current_node, phpast.Try):
        for catch_block in current_node.catches:
            if not catch_block.nodes:
                return True

d = DependencyResolver()
f = NodeFinder(try_has_empty_catch)

t.register_visitor(d)
t.register_visitor(f)

t.traverse()

# Evaluate the results of f and output it accordingly
if not f.found:
    print("There are no Try Blocks with Empty Catch Blocks")
else:
    print(f"\n{len(f.found)} Try Blocks have empty Catch Blocks\n")
    for i, result in enumerate(f.found):
        print(f"Result #{i+1}")
        print(f"Try statment on {result['node'].lineno} in Line ")
        print("Namespace Stack:")
        for namespace in result["namespace_stack"]:
            if isinstance(namespace, syntax_tree.SyntaxTree):
                print(f"--> File: {namespace.file_path}")
            else:
                print(f"--> {type(namespace).__name__}: ", end="")
                print(f"{namespace.name}")
        print()
