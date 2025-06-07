# Copyright 2025 Claudionor N. Coelho Jr

import os.path
import sys

sys.path.append("..")

from utils.interfaces import *


def test_is_c():
    assert is_c("c")
    assert not is_c("cxx")
    assert is_c(".c")


def test_is_cxx():
    assert is_cxx("cxx")
    assert is_cxx("cpp")
    assert is_cxx("cc")
    assert is_cxx(".cxx")
    assert is_cxx(".cpp")
    assert is_cxx(".cc")
    assert not is_cxx("c")


def test_is_c_cxx():
    assert is_c_cxx("c")
    assert is_c_cxx("cxx")
    assert is_c_cxx("cpp")
    assert is_c_cxx("cc")
    assert is_c_cxx(".c")
    assert is_c_cxx(".cxx")
    assert is_c_cxx(".cpp")
    assert is_c_cxx(".cc")
    assert not is_c_cxx("python")

def test_is_python():
    assert is_python("python")
    assert is_python("py")
    assert not is_python("cxx")
    assert is_python(".py")
