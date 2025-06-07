# Copyright 2025 Claudionor N. Coelho Jr

import argparse
import json
import subprocess

try:
    from .get_coverage_cc import get_coverage_cc
    from .interfaces import *
    from .utils import *
except:
    from get_coverage_cc import get_coverage_cc
    from interfaces import *
    from utils import *


def get_coverage_python(
    test_dir, src_dir, files, functions, ssh='', debug=False):

    '''
        Runs python coverage on test directory and extracts missing
        coverage lines.

        :param test_dir: test directory where test will be executed.
        :param src_dir: source directory for source code.
        :param files: files to scan for coverage metrics.
        :param functions: maps from function names to files where they are defined.
        :param ssh: '' or <user>:<ip> for ssh connection.
        :param debug: if debug is true, we print the messages for analysis.

        :return: list of missing coverage, one per file inside the
                 functions, and output log for execution if an error
                 occurs.
    '''

    cmd_list = [
        f'cd {test_dir}',
        f'coverage erase',
        f'PYTHONPATH="$PYTHONPATH:{src_dir}" coverage run -m pytest',
        'coverage json'
    ]

    cmd = '(' + ' ; '.join(cmd_list) + ')'

    data = subprocess.run(cmd, capture_output=True, shell=True, text=True)

    if data.stderr:
        if debug:
            print(data.stderr)
            if debug == 4: input('continue:')

        return True, [], data.stderr

    js = json.load(open(f'{test_dir}/coverage.json'))

    # parse coverage.json database

    result = []

    for file in files:
        missing_lines = []
        try:
            if file in js['files']:
                file_report = js['files'][file]
            else:
                file_report = js['files'][src_dir + '/' + file]
        except:
            import pdb; pdb.set_trace()
        for function in functions:
            if function in file_report["functions"]:
                missing_lines = (
                    file_report["functions"][function]["missing_lines"])
                # import pdb; pdb.set_trace()
                if missing_lines:
                    missing_lines = [str(m) for m in missing_lines]
                    result.append(
                        f"{file}:{function}: could not reach lines: " +
                        f"{','.join(missing_lines)}")
    # we need to better capture the errors here
    if 'NameError' in data.stdout:
        fix_this = True
    else:
        fix_this = False

    return fix_this, result, data.stdout

def get_coverage(
    test_dir, src_dir, files, functions, language,
    cflags="", ldflags="", ssh="", debug=False):

    '''
        Function that calls respective python or cc coverage extraction.

        :param test_dir: test directory where test will be executed.
        :param src_dir: source directory for source code.
        :param files: files to scan for coverage metrics.
        :param functions: functions to look for in files.
        :param language: 'c', 'cc' or 'python'.
        :param cflags: arguments to be used in compilation.
        :param ldflags: arguments to be used in linkage.
        :param ssh: '' or <user>:<ip> for ssh connection.
        :param debug: if debug is true, print error messages and wait for 
               result.

        :return: list of missing coverage, one per file inside the
                 functions.
    '''

    if is_c_cxx(language):
        return get_coverage_cc(
            test_dir=test_dir,
            src_dir=src_dir,
            files=files,
            functions=functions,
            cflags=cflags,
            ldflags=ldflags,
            ssh=ssh,
            debug=debug)
    elif is_python(language):
        return get_coverage_python(
            test_dir=test_dir,
            src_dir=src_dir,
            files=files,
            functions=functions,
            ssh=ssh,
            debug=debug)


def parse_args(arg_list: list[str] | None):
    '''
        Argument parser..

        :param arg_list: list of arguments to facilitate testing.
    '''

    parser = argparse.ArgumentParser()

    parser.add_argument('files', nargs='+')
    parser.add_argument('-t', '--test_dir', default='.')
    parser.add_argument('-s', '--src_dir', default='.')
    parser.add_argument('-f', '--functions', default=[], action='append')
    parser.add_argument('-c', '--cflags', default='')
    parser.add_argument('-l', '--ldflags', default='')
    parser.add_argument('--language', default='cc')
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
    # files: Comma separated target files.
    # functions: Function names to be targets.
    # language: python, cxx, c
    # cflags: arguments to be used in compilation.
    # ldflags: arguments to be used in linkage.
    # ssh: '' or <user>@<ip> for ssh connection.

    test_dir = args.test_dir
    src_dir = args.src_dir
    files = args.files
    functions = args.functions
    language = args.language
    cflags = args.cflags
    ldflags = args.ldflags
    ssh = args.ssh
    debug = args.debug

    src_dir = fix_relative_paths(src_dir)
    test_dir = fix_relative_paths(test_dir)
    files = fix_relative_paths(files)

    fix_this, result, log = get_coverage(
        test_dir=test_dir,
        src_dir=src_dir,
        files=files,
        functions=functions,
        language=language,
        cflags=cflags,
        ldflags=ldflags,
        ssh=ssh,
        debug=debug)

    print('\nError in compilation/execution:', fix_this)

    if result:
        print('\nMissing coverage:')
        print('\n'.join(result))

    if log:
        print('\nOutput log:')
        print(log)

    return fix_this, result, log

if __name__ == '__main__':
    main()
