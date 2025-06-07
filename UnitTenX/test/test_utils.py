# Copyright 2025 Claudionor N. Coelho Jr

import os
import sys

sys.path.append("..")

from utils.utils import execute_remote_command
from utils.utils import copy_from_remote
from utils.utils import copy_to_remote
from utils.utils import fix_relative_paths
from virtualbox import virtualbox_command


def test_fix_relative_paths():
    expected_abs_path = os.path.abspath('..')
    path = fix_relative_paths('..')
    assert path == expected_abs_path


def test_fix_relative_paths_for_list():
    paths = ['/usr/local/work/../bin/..']
    expected_paths = [
        os.path.abspath(f) for f in paths
    ]
    paths = fix_relative_paths(paths)
    assert paths == expected_paths


def test_copy_remote():
    remote_connection = os.environ.get('TEST_REMOTE_EXECUTION', '')

    assert remote_connection

    with open("from_file.txt", "w") as f:
        f.write("1,2,3\n")

    assert not copy_to_remote(
        ssh="",
        local_path="from_file.txt",
        remote_path="/tmp",
        debug=True)

    assert copy_to_remote(
        ssh=remote_connection,
        local_path="from_file.txt",
        remote_path="/tmp",
        debug=True)

    assert not copy_from_remote(
        ssh="",
        remote_path="/tmp/from_file.txt",
        local_path="to_file.txt",
        debug=True
    )

    assert copy_from_remote(
        ssh=remote_connection,
        remote_path="/tmp/from_file.txt",
        local_path="to_file.txt",
        debug=True
    )

    text = open("to_file.txt","r").read()

    assert text == "1,2,3\n"

def test_execute_remote_command():
    remote_connection = os.environ.get('TEST_REMOTE_EXECUTION', '')

    assert remote_connection

    stdout, stderr = execute_remote_command(
        ssh=remote_connection,
        command='ls',
        path='/tmp',
        debug=True)

    assert not stderr
    assert 'from_file.txt' in stdout

    stdout, stderr = execute_remote_command(
        ssh=remote_connection,
        command='rm /tmp/from_file.txt',
        debug=False)

    assert not stderr
    assert 'from_file.txt' not in stdout

    _, stderr = execute_remote_command(
        ssh="",
        command='ls',
        debug=True)

    assert stderr


