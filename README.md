<p align="center">
<h3 align="center">AST Generator and Analyser written in Python</h3>

<p align="center">
    A small tools for building ASTs using Python and performing simple queries on them.
    <p align="center">
        <a href="https://opensource.org/licenses/MIT">
            <img src="https://img.shields.io/badge/License-MIT-blue.svg"/>
        </a>
    </p>
    <br />
</p>
</p>




## Table of Contents

* [About the Project](#about-the-project)
* [Installation](#installation)
* [Getting Started](#getting-started)
    * [Building AST for a File](#building-ast-for-a-file)
    * [Building Resource Tree for a Directory](#building-resource-tree-for-a-directory)
    * [Using Traversers and Visitors](#using-traversers-and-visitors)
    * [Querying for Particular Nodes](#querying-for-particular-nodes)
* [Predefined Traversers and Visitors](#predefined-traversers-and-visitors)
    * [Traversers](#traversers)
    * [Visitors](#visitors)
    * [Resource Tree Specific Visitors](#resource-tree-specific-visitors)
* [Known Issues](#known-issues)



<!-- ABOUT THE PROJECT -->
## About The Project

A small Python Library for building ASTs from source code and performing simple queries on them. 

**Note: This project only supports ASTs for PHP as of now and is no longer in development. There are a few known issues listed [here](#known-issues). Any contributions are welcome.**

The project uses a PLY-based Parser for building ASTs for PHP. There is also an ANTLR-based compiler but it is not fully complete and compatible with the `modules`. Therefore, all the modules in the project use the PLY-based compiler.

The project is license under the [MIT License](LICENSE.md)

## Installation

The project requires Python 3.x.

Dependencies for the project are stored in `requirements.txt`. Install them using
```
pip install -r requirements.txt
```

## Getting Started

### Building AST for a File
To build ast for a file, create the following `test.py` file in the root directory.

```
from src.modules.php.syntax_tree import build_syntax_tree

tree = build_syntax_tree("path/to/php/file")
```

Run it using `python -i test.py` to inspect the result of the AST built. `build_syntax_tree` returns a [SyntaxTree](CLASSES.md) object.

### Building Resource Tree for a Directory
A Resource Tree is basically a collection of ASTs for all the files in a project directory along with some other information (e.g, Function and Method definitions).

To build a Resource Tree for a given directory, create a `test2.py`  file in the root directory.
```
from src.modules.php.resource import build_resource_tree

r_tree = build_resource_tree("examples/php")
```
Then run it using `python -i test2.py` to inspect the results. `build_resource_tree` returns a [ResourceTree](CLASSES.md) object.

### Using Traversers and Visitors
Analysing the built Abstract Syntax Trees requires you to follow the Visitor Pattern. You need to use a traverser that inherits from the built-in [Traverser](CLASSES.md) class and overrides its methods. The traverser can register one or more visitors that inherit from the built-in [Visitor](CLASSES.md) class.

Once the traverser runs, it should visit each node in the tree and dispatch all of the visitors on the visited node. The visitors can collect information or mutate the AST during the traversal.

Have a look at the predefined [Visitors](CLASSES.md) and [Traversers](CLASSES.md) to get an idea of how it works.


Here is a minimal example that uses the built-in [BFTraverser](CLASSES.md) and a custom visitor to print the types of all the nodes present in the AST:

```
from src.modules.php.traversers.bf import BFTraverser
from src.modules.php.base import Visitor 
from src.modules.php.syntax_tree import build_syntax_tree

class CustomVisitor(Visitor):
    def visit(self, node):
        print(type(node))

s_tree = build_syntax_tree("/path/to/file")
traverser = BFTraverser(s_tree) 
printer_visitor = CustomVisitor()
traverser.register_visitor(printer_visitor)

traverser.traverse()
```

### Querying for Particular Nodes
To search for and collect nodes that meet a particular criterion, you can use the pre-defined `NodeFinder` visitor. It takes a boolean-valued callback function and searches for nodes that meet that callback.

For example, to search for all function calls without a parameter, you would use the following example,

```
from src.modules.php.syntax_tree import build_syntax_tree
from src.modules.php.visitors.finders import NodeFinder
from src.modules.php.traversers.bf import BFTraverser
from src.compiler.php.phpast import FunctionCall

def function_has_no_params(node):
    return isinstance(node, FunctionCall) and len(node.params) == 0

s_tree = build_syntax_tree("/path/to/php/file")
bft = BFTraverser(s_tree)
node_finder = NodeFinder(function_has_no_params)
bft.register_visitor(node_finder) 

bft.traverse()
print(node_finder.found)
```

## Predefined Traversers and Visitors

#### Traversers:
* [BFTraverser](CLASSES.md): Carries the visitors in a Breadth-first manner
* [DFTraverser](CLASSES.md): Carries the visitors in a Depth-first manner

#### Visitors:
* [Printer](CLASSES.md): Prints the nodes of the AST
* [GraphBuilder](CLASSES.md): Builds a graph using the AST
* [NameFinder](CLASSES.md): Searches for specified names (Function Definitions/Variables) and collects those nodes
* [NameHighlighter](CLASSES.md): Searches and highlights specified names using the AST and a GraphBuilder instance
* [NodeFinder](CLASSES.md): Takes a boolean-valued callback function and collects all the nodes that satisfy that callback filter
* [DependencyResolver](CLASSES.md): Searches for all the Include/Require nodes and tries to expand them by connecting the SyntaxTree for the imported file

#### Resource Tree specific Visitors:

Work similar to the above visitors, except they require a ResourceTree instance at initialization. 
* [TablesBuilder](CLASSES.md): Searches for all function/method definitions while walking a file and updates the `function_table` and `method_table` in the corresponding ResourceTree
* [ResourceCallsFinder](CLASSES.md): Searches for all the Function Calls and Method Calls and associates them with the definitons in `function_table` and `method_table` of the corresponding ResourceTree.

## Known Issues
* Poor Performance, especially in the ANTLR-based parser
* The PLY-based parser does not interpret some constrcuts properly. For example,
    * Use declarations of the format `use (const|function) (namespace)`
    * Arrow Functions
    * Nested Variable Names or Accessors like `$a -> {$b -> c}`
* The ANTLR-based parser has poor performance and is tens of times slower than the PLY-based parser. The AST Generation is also not fully complete
