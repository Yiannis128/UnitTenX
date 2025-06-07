# Copyright 2025 Claudionor N. Coelho Jr

import sys

sys.path.append("..")

from utils.symbolic import *


def test_main():
    arg_list = [
        "files/meow.c",
        "-Ifiles/include",
        "--target", "run",
        "--work", "work",
        "--project", "files",
        "--debug=3"
    ]

    result = main(arg_list)

    arg_list = [
        "files/fact.c",
        "--target", "run",
        "--work", "work",
        "--project", "files",
        "--debug=3"
    ]

    result = main(arg_list)

def test_is_same_value():
    o1 = 3
    o2 = "test"

    assert not is_same(o1, o2)

def test_is_same_dict():
    o1 = { "test": 1 }
    o2 = { 1 : 2, 3: 4 }

    assert not is_same(o1, o2)

    o1 = { "test": 1 }
    o2 = { 1 : 2 }

    assert not is_same(o1, o2)

    o1 = { "test": 1 }
    o2 = { "test": 1 }

    assert is_same(o1, o2)

def test_is_same_list():
    o1 = [ "test" ]
    o2 = [ 1, 2 ]

    assert not is_same(o1, o2)

    o1 = [ "test", 2 ]
    o2 = [ 1, 2 ]

    assert not is_same(o1, o2)

    o1 = [ 1, 2 ]
    o2 = [ 1, 2 ]

    assert is_same(o1, o2)

def test_in_obj_list():
    obj = [ 1 ]
    obj_list = [ [ 2 ], [ 4 ], [ 1 ] ]

    assert in_obj_list(obj, obj_list)
