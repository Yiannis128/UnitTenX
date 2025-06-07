# Copyright 2025 Claudionor N. Coelho Jr

from argparse import ArgumentParser
from fire import Fire
import os
import platform
import subprocess
from utils.utils import execute_remote_command



def get_vmboxmanage() -> str:
    '''
        Gets which VBoxManage to run.

        If we are running this from WSL, we expect WSL to be in the
        name of the platform. Otherwise, we assume VBoxManage is in the
        path.

        :returns: program to execute.
    '''

    hostname = platform.platform()
    if 'WSL' in hostname:
        vmboxmanage = '/mnt/c/Program\\ Files/Oracle/VirtualBox/VBoxManage.exe'
    else:
        vmboxmanage = 'VBoxManage'

    return vmboxmanage


def vm_is_running(vmname: str) -> bool:
    '''
        Checks if VM is running.

        :param vmname: Name of VM, such as FreeBSD.
        :returns: True is 'vmname' is in string of VM's, false otherwise.
    '''

    cmd_list = [
        get_vmboxmanage(),
        'list',
        'runningvms',
    ]

    cmd = ' '.join(cmd_list)
    data = subprocess.run(cmd, capture_output=True, shell=True, text=True)

    return vmname in data.stdout


def vm_login(ip: str, user: str) -> bool:
    '''
        Check if VM is alive. We do that by logging in into the machine.

        :param ip: ip address of machine.
        :param user: user name.
        :returns: True is 'vmname' is in string of VM's, false otherwise.
    '''

    try:
        stdout, stderr = execute_remote_command(
            ssh=f'{user}@{ip}',
            command='ls',
            path='/tmp',
            debug=False)

        if stderr:
            print(stderr)

            return 'not alive'
    except:
        return 'not alive'

    return 'alive'


def start_vm(vmname: str) -> None:
    '''
        Starts VM.

        The VM needs to be executing.

        :param vmname: Name of VM, such as FreeBSD.
    '''

    cmd_list = [
        get_vmboxmanage(),
        'startvm',
        vmname
    ]

    cmd = ' '.join(cmd_list)
    data = subprocess.run(cmd, capture_output=True, shell=True, text=True)


def stop_vm(vmname: str) -> None:
    '''
        Stops VM.

        The VM needs to be executing.

        :param vmname: Name of VM, such as FreeBSD.
    '''

    cmd_list = [
        get_vmboxmanage(),
        'controlvm',
        vmname,
        'poweroff'
    ]

    cmd = ' '.join(cmd_list)
    data = subprocess.run(cmd, capture_output=True, shell=True, text=True)


def get_ip_address(vmname: str, output: bool=True) -> None:
    '''
        Gets an IP address of a live VM.

        The VM needs to be executing.

        :param vmname: Name of VM, such as FreeBSD.
        :param output: if true, prints output. 
    '''

    cmd_list = [
        get_vmboxmanage(),
        'guestproperty',
        'get',
        vmname,
        '/VirtualBox/GuestInfo/Net/0/V4/IP'
    ]

    cmd = ' '.join(cmd_list)
    data = subprocess.run(cmd, capture_output=True, shell=True, text=True)

    ip_address = data.stdout.split(' ')[-1].strip()

    if output:
        print(ip_address)

    return ip_address


def parse_args(arg_list: list[str] | None) -> None:
    '''
        Argument parser.

        :param arg_list: list of arguments to facilitate testing.
    '''

    parser = ArgumentParser()

    parser.add_argument(
        'command', choices=['start', 'stop', 'status', 'ip', 'alive'])
    parser.add_argument('vmname', nargs='?', default='FreeBSD')
    parser.add_argument('--user')

    args = parser.parse_args(arg_list)

    return args

def virtualbox_command(arg_list: list[str] | None=None) -> None:
    '''
        Executes VirtualBox Commands for UnitTenX

        :param arg_list: list of arguments to facilitate testing.
    '''

    args = parse_args(arg_list)

    if args.command == 'start':
        if not vm_is_running(args.vmname):
            start_vm(args.vmname)
    elif args.command == 'stop':
        if not vm_is_running(args.vmname):
            stop_vm(args.vmname)
    elif args.command == 'status':
        if vm_is_running(args.vmname):
            print('running')
        else:
            print('not running')
    elif args.command == 'ip':
        if not vm_is_running(args.vmname):
            start_vm(args.vmname)

        get_ip_address(args.vmname)
    elif args.command == 'alive':
        if not vm_is_running(args.vmname):
            start_vm(args.vmname)
        ip = get_ip_address(args.vmname, output=False)
        result = vm_login(ip, args.user)
        print(result)


if __name__ == '__main__':
    virtualbox_command()
    


