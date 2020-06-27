from antlr4 import *
from PhpLexer import PhpLexer
from PhpParser import PhpParser
from visitors import Visitor
from time import time
import timeit
import sys

input_file = sys.argv[1] if len(sys.argv)>1 else "example.php"
input_ = FileStream(input_file)
lexer = PhpLexer(input_)
stream = CommonTokenStream(lexer)
parser = PhpParser(stream)
e = parser.phpBlock()
v = Visitor()
t = v.visit(e)
