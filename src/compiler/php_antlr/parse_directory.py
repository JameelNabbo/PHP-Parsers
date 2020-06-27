import sys
import os
from time import time

from antlr4 import *
from PhpLexer import PhpLexer
from PhpParser import PhpParser
from visitors import Visitor

input_directory = sys.argv[1]
file_paths = []
file_trees = {}
error = {}
for dirpath, dirnames, filenames in os.walk(input_directory):
    for filename in filenames:
        if filename.endswith(".php"):
            file_path = os.path.join(dirpath, filename)
            file_paths.append(file_path)

print(f"Total {len(file_paths)} files found\n")
for i, file_path in enumerate(file_paths):
    print(f"{i+1}-> Parsing {file_path}")
    try:
        input_ = FileStream(file_path, encoding="utf-8")
        lexer = PhpLexer(input_)
        stream = CommonTokenStream(lexer)
        parser = PhpParser(stream)
        file_trees[file_path] = parser.phpBlock()
    except Exception as e:
        print(f"Error parsing {file_path}")
        errors[file_path] = e
