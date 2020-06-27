# Predefined Modules, Classes and Functions

## Modules
- `src.compiler.php_antlr` : Antlr-based compiler
- `src.compiler.php` : PLY-based compiler
- `src.compiler.php.phpast` : Contains all the node types for PHP
- `src.modules.php.base`: Contains base classes `Visitor` and `Traverser`
- `src.modules.php.visitors`: Contains all the predefined visitors
- `src.modules.php.traversers`: Contains predefined Traversers

## Classes

### Top Level Classes
- `src.modules.php.syntax_tree.SyntaxTree`: Class for building AST for a single file
- `src.modules.php.resource.ResourceTree`: Class for building and processing ASTs for a directory 

### Visitor Classes
- `src.modules.php.visitors.outputters.Printer`
- `src.modules.php.visitors.outputters.GraphBuilder`
- `src.modules.php.visitors.finders.NameFinder`
- `src.modules.php.visitors.finders.NameHighlighter`
- `src.modules.php.visitors.finders.NodeFinder`
- `src.modules.php.visitors.finders.ResourceCallsFinder`
- `src.modules.php.visitors.resolvers.DependencyResolver`
- `src.modules.php.visitors.resolvers.TablesBuilder`
- `src.modules.php.visitors.resolvers.ResourceDependencyResolver`

## Utility Functions

- `src.modules.php.syntax_tree.build_syntax_tree`
- `src.modules.php.resource_tree.build_resource_tree`
