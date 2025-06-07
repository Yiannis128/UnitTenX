# Copyright 2025 Claudionor N. Coelho Jr

import sys

sys.path.append("..")

from utils.implied_graph import main
from utils.implied_graph import discard


def test_discard():
    assert not discard("::operator new")


def test_main_cc():
    args_list = [
        "-p.",
        "-frun",
        "-d", "2",
        "--cflags",
        "'-g'",
        "-Ifiles/include",
        "-lauto",
        "files/meow.c"
    ]

    files = main(args_list)

    args_list = [
        "-p.",
        "-frun",
        "-d", "1",
        "-lauto",
        "files/fact.cpp"
    ]

    files = main(args_list)

    assert "run()" in files
    assert "factorial(int)" in files
    assert "fact.cpp" in files["run()"]
    assert "fact.cpp" in files["factorial(int)"]
    assert len(files) == 2


def test_main_python():
    args_list = [
        "-p.",
        "-fmain",
        "-d", "2",
        "-lauto",
        "files/fact.py"
    ]

    files = main(args_list)

    assert "factorial" in files
    assert "main" in files

    assert "fact.py" in files["factorial"]
    assert "fact.py" in files["main"]

    assert len(files) == 2

def test_main_yaml():
    args_list = [
        "-p.",
        "-frun",
        "-d", "2",
        "-lauto",
        "files/files.yaml"
    ]

    files = main(args_list)

    assert 'run(int)' in files
    assert 'A(int)' in files
    assert 'B()' in files
    assert 'G()' in files

    assert 'main.cc' in files['run(int)']
    assert 'main.cc' in files['A(int)']
    assert 'b.cc' in files['B()']
    assert 'g.cc' in files['G()']

    assert len(files) == 4

def test_main_invalid_language():
    args_list = [
        "-p.",
        "-frun",
        "-d", "2",
        "-Ifiles/include",
        "-lauto",
        "files/invalid.p"
    ]

    try:
        main(args_list)
        assert False
    except ValueError:
        pass


def test_main_cc_error():
    args_list = [
        "-p.",
        "-frun",
        "-d", "2",
        "-Ifiles/include",
        "-lauto",
        "files/invalid.cxx"
    ]

    files = main(args_list)

    assert len(files) == 0

def test_main_cc_name_error():
    args_list = [
        "-p.",
        "-fmain",
        "-d", "2",
        "-Ifiles/include",
        "-lauto",
        "files/meowc.c"
    ]

    files = main(args_list)

    assert len(files) == 0


def test_main_python_error():
    args_list = [
        "-p.",
        "-frun",
        "-d", "2",
        "-Ifiles/include",
        "-lauto",
        "files/invalid.py"
    ]

    files = main(args_list)

    assert len(files) == 0

