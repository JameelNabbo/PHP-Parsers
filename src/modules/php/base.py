"""Base Classes for Different Components"""

class Traverser():
    def register_visitor(self, new_visitor) -> None:
        """called when a new Visitor is added to the traverser
        Should call the visitor's register_with method
        """
        pass

    def traverse(self, current_node) -> None:
        """Performs the actual traversal. Should the enter, visit and leave
        methods of every visitor in self.visitors at appropriate places
        """
        pass


class Visitor():
    def enter(self, current_node):
        """Called when the visitors enters the node. 'current_node' may be of
        any type including Node. This method is optional
        """
        pass

    def visit(self, current_node) -> None:
        """This is called after appropriate checks are applied on the node
        by the traverser. current_node is of type phpast.Node
        """
        pass

    def leave(self, current_node) -> None:
        """ Called just before the traversal of the current node ends. In
        recursion-based traversers, this is called after the current_node is
        traversed and its children nodes are recursed
        """
        pass

    def register_with(self, traverser) -> None:
        """Called when the given visitor is added to the traverser. Should 
        perform initializations and keep a reference to any traverser data 
        (e.g. namespace_stack) required
        """
        pass
