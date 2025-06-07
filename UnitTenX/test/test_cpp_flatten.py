# Copyright 2025 Claudionor N. Coelho Jr

import sys

sys.path.append("..")

from utils.cpp_flatten import cpp_flatten
from utils.cpp_flatten import main


def test_cpp_flatten():
    filename = "files/meow.c"
    includes = ["files/include"]
    cflags = " ".join([f"-I{inc}" for inc in includes])
    source = cpp_flatten(filename, cflags=cflags, includes=includes)

    assert source

    filename = "files/fact.cpp"
    includes = []
    cflags = ""
    source = cpp_flatten(filename, cflags=cflags, includes=includes)

    assert source

def test_main():
    args_list = [
        "-Ifiles/include", "-DDEBUG", "--cflags='-g'", "files/meow.c"
    ]
    main(args_list)

def test_cpp_flatten_with_error():
    filename = "files/meow.c"
    includes = []
    cflags = " ".join([f"-I{inc}" for inc in includes])
    try:
        cpp_flatten(filename, cflags=cflags, includes=includes)
        assert False
    except ValueError:
        pass

