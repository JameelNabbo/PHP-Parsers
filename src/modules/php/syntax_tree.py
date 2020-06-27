import sys
import os

from src.compiler.php import phpparse
from src.compiler.php import phplex
from src.compiler.php import phpast

lexer = phplex.lexer
lexer.lineno = 1

parser = phpparse.make_parser()

class SyntaxTree(phpast.Node):
    fields = ['nodes']

    def __init__(self, source_code_handle, debug=False):
        source_code = source_code_handle.read()
        nodes = parser.parse(source_code, lexer=lexer.clone(), debug=debug)
        self.nodes = nodes
        self.file_location = os.path.abspath(os.path.dirname(source_code_handle.name))
        self.file_path = os.path.abspath(source_code_handle.name)
        self.file_name = os.path.basename(source_code_handle.name)


def build_syntax_tree(file_path, debug=False):
    if not os.path.isfile(file_path):
        raise Exception("Please specify a File Path")
    file_handle = open(file_path)
    return SyntaxTree(file_handle)
