# Copyright 2025 Claudionor N. Coelho Jr

import os
import subprocess
import sys

sys.path.append("../files")

from utils.get_coverage_cc import main as cc_main
from utils.get_coverage import main as all_main

import os

def test_get_coverage_direct():
    os.environ['AGENT_REMOTE_VERSION'] = ""
    args_list = [
        "-t", "gold",
        "-s", "gold",
        "-f", "run",
        "-c", "'-Ifiles/include'",
        "--ldflags", "''",
        "gold/meow.c"
    ]

    fix_this, result, _ = all_main(args_list)

    cmd = "(cd gold ; make clean); rm gold/Makefile"
    _ = subprocess.run(cmd, capture_output=True, shell=True, text=True)

    assert not fix_this
    assert "70" in '\n'.join(result)


def test_get_coverage_ssh():
    os.environ['AGENT_REMOTE_VERSION'] = "10"
    ssh = os.environ.get("TEST_REMOTE_EXECUTION", "")

    assert ssh

    args_list = [
        "-t", "gold",
        "-s", "gold",
        "-f", "run",
        "-c", "'-Ifiles/include'",
        "--ssh", ssh,
        "gold/meow.c"
    ]

    fix_this, result, _ = cc_main(args_list)

    cmd = "(cd gold ; make clean); rm gold/Makefile"
    _ = subprocess.run(cmd, capture_output=True, shell=True, text=True)

    assert not fix_this
    assert "70" in '\n'.join(result)

def test_get_coverage_python():
    test_program = """
    from fact import *
    from ping_pong import *
     
    def test_factorial_one():
        # Test for n = 1, expecting factorial of 1 to be 1
        assert factorial(1) == 1
    
    def test_factorial_small_number():
        # Test for a small number, n = 5, expecting factorial of 5 to be 120
        assert factorial(5) == 120
    
    def test_factorial_large_number():
        # Test for a larger number, n = 10, expecting factorial of 10 to be 3628800
        assert factorial(10) == 3628800
    """

    with open("gold/test_fact.py", "w") as f:
        lines = test_program.split('\n')
        for line in lines:
            if line:
                line = line[4:]

            f.write(line + '\n')

    args_list = [
        "-t", "gold",
        "-s", "files",
        "-f", "main",
        "--language", "python",
        "--debug", "1",
        "files/fact.py"
    ]

    fix_this, result, log = all_main(args_list)

    os.remove("gold/test_fact.py")

    assert not fix_this
    assert "11" in '\n'.join(result)

