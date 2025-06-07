# Copyright 2025 Claudionor N. Coelho Jr

import argparse
import glob
import numpy as np
import os
import re
import subprocess
import threading
from typing import List, Mapping, Any
from utils.get_coverage_cc import get_coverage_cc
import yaml


def parse_args(arg_list: list[str] | None):
    '''
        Argument parser..

        :param arg_list: list of arguments to facilitate testing.
    '''

    parser = argparse.ArgumentParser()

    parser.add_argument('-t', '--test_dir', default='.')
    parser.add_argument('-s', '--src_dir', default='.')
    parser.add_argument('-f', '--functions', default=[], action='append')
    parser.add_argument('-c', '--cflags', default='')
    parser.add_argument('-l', '--ldflags', default='')
    parser.add_argument('--ssh', default='')
    parser.add_argument('--debug', type=int, default=0)

    args = parser.parse_args(arg_list)

    # sometimes cflags and ldflags may contain quotes in the beginning.
    # if that's the case, remove them.
    if args.cflags and args.cflags[0] in ["'", '"']:
        args.cflags = args.cflags[1:]
        if args.cflags and args.cflags[-1] in ["'", '"']:
            args.cflags = args.cflags[:-1]

    if args.ldflags and args.ldflags[0] in ["'", '"']:
        args.ldflags = args.ldflags[1:]
        if args.ldflags and args.ldflags[-1] in ["'", '"']:
            args.ldflags = args.ldflags[:-1]

    # if user did not specify functions, use 'main'
    if not args.functions:
        args.functions = ['main']

    return args


def main(arg_list: list[str] | None=None):
    '''
        Argument parser..

        :param arg_list: list of arguments to facilitate testing.
    '''

    args = parse_args(arg_list)

    # test_dir: Work directory to generate the makefile.
    # src_dir: Project directory where source code is locatd.
    # cflags: arguments to be used in compilation.
    # ldflags: arguments to be used in linkage.
    # ssh: '' or <user>@<ip> for ssh connection.

    test_dir = args.test_dir
    src_dir = args.src_dir
    cflags = args.cflags
    ldflags = args.ldflags
    ssh = args.ssh
    debug = args.debug

    src_dir = os.path.abspath(src_dir)
    test_dir = os.path.abspath(test_dir)

    db = yaml.safe_load(open(os.path.join(test_dir, 'db.yaml'), 'r').read())

    files = db['files']

    for f in files:
        prefix, ext = os.path.splitext(os.path.basename(f))
        print(f)
        for function in files[f]:
            if function.endswith('__globals'): continue
            mockup = 'i_' + prefix + '_' + function 
            test_head  = 'test_' + mockup 
            test_file = test_head + '.cc'
            mockup += ext

            coord = files[f][function]['coord']
            number_of_lines = coord[1] - coord[0]

            mockup_test_dir = os.path.join(test_dir, 'test', test_head)

            if not os.path.exists(mockup_test_dir): continue

            print(f'    {function} : ', end='')

            all_files = [
                os.path.join(test_dir, 'mockups', mockup)
            ]

            try:
                fix_this, result, log = get_coverage_cc(
                    test_dir=mockup_test_dir,
                    src_dir=src_dir,
                    files=all_files,
                    functions=function,
                    cflags=cflags,
                    ldflags=ldflags,
                    ssh=ssh,
                    create_makefile=False,
                    debug=debug)
            except:
                print('could not get coverage')
                continue

            log_lower = log.lower()

            if fix_this or 'core dump' in log_lower or 'timeout' in log_lower:
                lines = []
                print('could not get coverage')
            else:
                try:
                    lines_str = result[0].split(' ')[-1]
                    lines = [int(l) for l in lines_str.split(',')]
                    print(f'{np.round(100 * (1 - len(lines) / number_of_lines), 2)}%')
                except:
                    print('could not get coverage')
                    # log = [f'    {l}' for l in log.split('\n')]
                    # print('\n'.join(log))

if __name__ == '__main__':
    main()
