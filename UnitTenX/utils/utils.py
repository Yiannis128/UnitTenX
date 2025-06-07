# Copyright 2025 Claudionor N. Coelho Jr

import glob
import paramiko
import os
import pycparser_fake_libc
from scp import SCPClient


def fatal_error(test_name: str = ""):
    '''
    Just exits with error message you can track later

    :param test_name: any information you can print before a fatal error.
    '''

    print('\n' + '-' * 80 + '\n')
    print(f'Fatal error on {test_name}. Exiting')
    exit()

def create_cpp_args(cflags):
    '''
        Create cpp_args for pycparser.

        :param cflags: cflags to be used by pycparser.

        :return: cpp_args list.

    '''
    cpp_args = cflags.split(' ')
    fake_dirs = [
        os.path.basename(fn)
        for fn in glob.glob(pycparser_fake_libc.directory + '/*.h')
    ]

    for i, arg in enumerate(cpp_args):
        if '/usr/include' in arg:
            basename = os.path.basename(arg)
            if basename in fake_dirs:
                cpp_args[i] = pycparser_fake_libc.directory + '/' + basename

    return cpp_args


def execute_remote_command(ssh, command, path='', port=22, debug=False):

    '''
        Copies files to an ssh client.

        :param ssh: <user>@<ip>.
        :param command: command to execute.
        :param path: remote path to execute command.
        :param port: port to use.
        :param debug: True if we should print messages.

        :return: True/False.
                 
    '''

    try:
        if path:
            command = f'( cd {path} ; {command} )'
        username, remote_host = ssh.split('@')
        password = os.getenv('REMOTE_PASSWORD')

        if debug:
            print(f'... executing {command} in {username}@{remote_host}.')

        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh_client.connect(
            remote_host,
            port=port,
            username=username,
            password=password,
            look_for_keys=False
        )

        stdin, stdout, stderr = ssh_client.exec_command(command)

        # Read output and error streams
        output = stdout.read().decode()
        error = stderr.read().decode()

        return output, error

    except Exception as e:
        if debug:
            print(f'... execution could not complete:')

        return None, f"Error: {e}"

    finally:
        try:
            ssh_client.close()
        except Exception as e:
            return None, f"Error: {e}"



def copy_to_remote(ssh, local_path, remote_path, port=22, debug=True):

    '''
        Copies files to an ssh client.

        :param ssh: <user>@<ip>.
        :param local_path: local path of file.
        :param remote_path: remote path to copy file.
        :param port: port to use.
        :param debug: True if we should print messages.

        :return: True/False.
                 
    '''

    try:
        username, remote_host = ssh.split('@')
        password = os.getenv('REMOTE_PASSWORD')

        print(f'... copying {local_path} in {remote_path}:')
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(
            remote_host, 
            port=port,
            username=username, 
            password=password,
            look_for_keys=False
        )

        with SCPClient(ssh_client.get_transport()) as scp:
            scp.put(local_path, remote_path)
    except Exception as e:
        print(f'... execution could not complete: {e}')
        return False

    return True


def copy_from_remote(ssh, remote_path, local_path, port=22, debug=False):

    '''
        Copies files to an ssh client.

        :param ssh: <user>@<ip>.
        :param remote_path: remote path to copy file.
        :param local_path: local path of file.
        :param port: port to use.
        :param debug: True if we should print messages.

        :return: True/False.
                 
    '''

    try:
        username, remote_host = ssh.split('@')
        password = os.getenv('REMOTE_PASSWORD')

        if debug:
            print(f'... copying {remote_path} to {local_path}:')
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(
            remote_host,
            port=port,
            username=username, 
            password=password,
            look_for_keys=False
        )


        with SCPClient(ssh_client.get_transport()) as scp:
            scp.get(remote_path, local_path)
    except Exception as e:
        print(f'... execution could not complete: {e}')
        return False

    return True


def fix_relative_paths(paths):

    '''
        Converts relative path to full path. If paths is not a list,
        convert it back to just a string.

        :param paths: list of paths to be converted to full path.

        :return: full paths.
                 
    '''

    if not isinstance(paths, list):
        paths = [paths]
        use_string = True
    else:
        use_string = False

    for i, p in enumerate(paths):
        paths[i] = os.path.abspath(p)

    if use_string:
        paths = paths[0]

    return paths


