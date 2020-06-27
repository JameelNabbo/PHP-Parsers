"""Builds the Syntax Tree for a directory by walking through it, building the
SyntaxTree for all the PHP files, expanding the dependencies and removing
files that are already imported in other files (to eliminate redundancy)
"""

import os
import sys

from collections import defaultdict

from src.modules.php import syntax_tree
from src.modules.php.visitors.resolvers import ResourceDependencyResolver, TablesBuilder
from src.modules.php.traversers.bf import BFTraverser


class InvalidPathException(Exception):
    pass

class ResourceTree:
    """ Structure for building ASTs for all files in the project,
    managing them and performing collective operations on them

    Methods:
        - __init__(self, path, debug=False): Does the necessary initializations
          and collects the paths for all the PHP files in the project
        - build_trees(): Takes the collected paths and builds ASTs for all the
          files in the project.
        - build_tables(): Builds function_table and method_table which
          contain information regarding all the function and method definitions
          inside the project

    Attributes:
        - files: Contains the absolute paths for all the collected files
        - function_table: Stores information regarding all the function defintions
        - method_table: Stores information regarding all the method defintions
    """

    def __init__(self, path, debug=False):
        """
        Initializes the AST and collects the paths for all the PHP files in 
        the project
        Path should be the relative or absolute path to the root directory
        of the project.
        """

        self.debug = debug
        self.files = []
        self.trees = {}
        self.function_table = defaultdict(lambda: {})
        self.method_table = defaultdict(lambda: {})
        self.dep_table = {}
        self.not_found = []
        self.expr_fails = []

        path = os.path.abspath(path)
        # Give Error if the specified path is invalid
        if not os.path.exists(path):
            raise InvalidPathException("The path specified does not exist.")

        # If it is a PHP file, simply add it to the files list
        if os.path.isfile(path) and path.endswith(".php"):
                self.files.append(os.path.abspath(path))
        # If it is a directory, recursively look for PHP files and add them
        else:
            for current_path, dirs, files in os.walk(path):
                for current_file in files:
                    file_path = os.path.join(current_path, current_file)
                    if file_path.endswith(".php"):
                        self.files.append(file_path)
                        self.dep_table[file_path] = []
        # Output Status
        print(f"Total {len(self.files)} PHP files found in the project.")

    def build_trees(self):
        """ Takes all the collected files in the current ResourceTree and
        builds SyntaxTrees for all of them"""

        no_of_files = len(self.files)

        if self.trees:
            self.trees = []
            print(f"Rebuilding Trees for all {no_of_files} files")
        else:
            print(f"Building Trees for all {no_of_files} files")

        for file_path in self.files:
            file_handle = open(file_path)
            file_tree = syntax_tree.SyntaxTree(file_handle)
            self.trees[file_path] = file_tree

    def build_tables(self):
        """Builds function_table and method_table, storing definitions of all 
        the functions and methods inside the project
        """

        print("Building Functions and Methods table")

        tables_builder = TablesBuilder(self)
        for file_path in self.trees:
            tree_traverser = BFTraverser(self.trees[file_path])
            tree_traverser.register_visitor(tables_builder)
            tree_traverser.traverse()

    def function_finder(self, function_name, bound=False, params=-1):
        """
        Returns a generator which iterates over the locations
        of all function/method definitions in the project with
        the name 'function_name'
        """

        f_table = self.method_table if bound else self.function_table
        for file_path in f_table:
            if f_table[file_path].get(function_name):
                found_function = f_table[file_path][function_name]
                if params < 0 or params == len(found_function.params):
                    yield (file_path, f_table[file_path][function_name])


def build_resource_tree(dir_path, debug=False):
    """Utility function to build the resource tree and generate the tables"""

    r_tree = ResourceTree(dir_path, debug=debug)
    r_tree.build_trees()
    r_tree.build_tables()
    return r_tree
