# Copyright 2025 Claudionor N. Coelho Jr

import argparse
import glob
import os
import re
import subprocess
import threading
from typing import List, Mapping, Any

import numpy as np

try:
    from .utils import *
except:
    from utils import *


def generate_makefile(
        work:str, 
        testfile:str, 
        target_files:List[str], 
        cflags: str = "",
        ldflags:str = "",
        ssh:str = "") -> List[str]:
    '''
        Generates a makefile in work directory.

        :param work: Work directory to generate the makefile.
        :param testfile: Testfine name.
        :param target_files: Target files to be compiled together.
        :param cflags:  dictionary with 'original' cflags and 'test' with
            arguments to be used in compilation.
        :param ldflags: arguments to be used in linkage.
        :param ssh: '' or <user>@<ip> for ssh connection.

        :return: New list of target files.
    '''

    dot_o_files = []
    results = []
    cov_files = []
    new_target_files = []

    # version = os.environ.get('AGENT_REMOTE_VERSION', '')

    cflags_list = cflags.split(' ')
    cflags_cpp_list = []
    i = 0
    while i < len(cflags_list):
        if cflags_list[i] == '-include':
            i += 2
            continue
        elif '-std' in cflags_list[i] or '-ansi' in cflags_list[i]:
            i += 1
            continue
        cflags_cpp_list.append(cflags_list[i])
        i += 1
    cflags_cpp = ' '.join(cflags_cpp_list)

    # add compile to Makefile
    results.append('compile:')
    for t in target_files:
        t = os.path.abspath(t)
        new_target_files.append(t)
        basename = os.path.basename(t)
        root, extension = os.path.splitext(basename)
        if extension == '.c':
            if ssh:
                compiler = '$(CC)'
            else:
                compiler = os.environ.get('CC', 'gcc')
        else:
            if ssh:
                compiler = '$(CXX)'
            else:
                compiler = os.environ.get('CXX', 'g++')
        results.append(
            f'\t{compiler} -fPIC -fprofile-update=atomic -fprofile-arcs -ftest-coverage {cflags} ' +
            f'-c {t}')
        dot_o_files.append(root + '.o')
        cov_files.append(basename)

    basename = os.path.basename(testfile)
    root, extension = os.path.splitext(basename)
    if extension == '.c':
        if ssh:
            compiler = '$(CC)'
        else:
            compiler = os.environ.get('CC', 'gcc')
    else:
        if ssh:
            compiler = '$(CXX)'
        else:
            compiler = os.environ.get('CXX', 'g++')
    # -Wall -Werror
    results.append(
        f'\t{compiler} -fPIC -fprofile-update=atomic -fprofile-arcs -ftest-coverage {cflags_cpp} ' +
        f'-c {testfile}')
    dot_o_files.append(root + '.o')

    results.append (
        f'\t{compiler} -fPIC -fprofile-arcs {ldflags} -ftest-coverage -o {root} ' +
        f'{" ".join(dot_o_files)}')

    # add run to Makefile
    results.append('')
    results.append('run:')
    results.append(f'\t@echo "./{root}"')
    results.append(f'\t-@./{root} > output.log 2>&1')
    results.append(f'\t@cat output.log')
    # add coverage to Makefile
    results.append('')
    results.append('coverage:')
    if ssh:
        gcov = '$(COV)'
    else:
        gcov = os.environ.get('COV', 'gcov')
    results.append(f'\t{gcov} {" ".join(cov_files)}')
    results.append(
        f'\tlcov --rc geninfo_unexecuted_blocks=1 --capture --directory . --output-file coverage.info.raw')
    results.append(f'\tc++filt < coverage.info.raw > coverage.info')

    # add clean to Makefile
    results.append('')
    results.append('clean:')
    results.append(
        f'\trm -rf {root} *.o *.so *.gcno *.gcda *.gcov coverage.info* *.log out')

    with open(work + '/Makefile', 'w') as f:
        f.write('\n'.join(results))

    return new_target_files


def process_coverage_info(
    work: str,
    ssh: str,
    temp_dir: str,
    target_files: List[str],
    verbose: bool=True) -> Mapping[str, Any]:
    '''
        Processes and extract coverage information.

        :param work: Work directory where everything is located.
        :param ssh: '' or <user>@<ip> for ssh connection.
        :param temp_dir: temporary directory used if using ssh.
        :param target_files: list target files to extract coverage from.
        :param verbose: if true, print messages.

    '''

    coverage_data = [
        line.strip()
        for line in open(work + '/coverage.info', 'r').readlines()
    ]

    files = {}

    i = 0
    while i < len(coverage_data):
        line = coverage_data[i]
        # it is a source file
        if line[:3] == 'SF:':
            filename = line[3:]
            if ssh:
                if temp_dir in filename:
                    filename = work + filename[len(temp_dir):]
            if filename not in target_files:
                i += 1
                continue

            if verbose:
                print(f'... processing file {filename}')

            i += 1

            functions = {}
            coverage_lines = {}

            while i < len(coverage_data):
                line = coverage_data[i]
                # it is a new source file
                if line[:3] == 'SF:':
                    i -= 1
                    break

                # it is a function coverage limiting where it is located
                if line[:3] == 'FN:':
                    info = line[3:].split(',')

                    if len(info) == 2:
                        functions[info[1]] = {
                            'lo': int(info[0]),
                            'hi': -1,
                            'count': 0
                        }
                    else:
                        functions[info[2]] = {
                            'lo': int(info[0]),
                            'hi': int(info[1]),
                            'count': 0
                        }

                # it is a function coverage
                elif line[:5] == 'FNDA:':
                    info = line[5:].split(',')
                    count = int(info[0])
                    functions[info[1]]['count'] = count

                # it is a line coverage metric
                elif line[:3] == 'DA:':
                    info = line[3:].split(',')
                    line_no = int(info[0])
                    count = int(info[1])

                    coverage_lines[line_no] = count

                i += 1

            files[filename] = {
                'functions': functions,
                'lines': coverage_lines
            }

        i += 1

    return files


def execute_makefile(
        work: str,
        target_files: str,
        ssh: str="",
        verbose: bool=True,
        debug: bool=False):
    '''
        Executes makefile to generate coverage.

        :param work: Work directory to generate the makefile.
        :param target_files: Target files to be compiled together.
        :param ssh: '' or <user>@<ip> for ssh connection.
        :param verbose: if true print messages.
        :param debug: if true, print error messages and wait for output.

        :return: a map of target files indicating which lines were covered,
                 and logs of outputs.
    '''
    temp_dir = ''

    if ssh:
        temp_dir, stderr = execute_remote_command(
            ssh, command=f'mktemp -d', debug=debug)

        if stderr:
            logs = f'{stderr}\n\n{temp_dir}'

            print(f'    stopping at `mktemp -d` because of an error:\n\n')
            print(logs)

            if debug == 4:
                input('continue:')

            return {}, logs

        temp_dir = temp_dir.strip()

        if verbose:
            print(f'... creating remote directory {temp_dir}')

        stdout, stderr = execute_remote_command(
            ssh, command=f'cp -rf {work}/* {temp_dir}', debug=debug)

        if stderr:
            logs = f'{stderr}\n\n{temp_dir}'

            if verbose:
                print(
                    f'    stopping at `cp -rf {work}/* {temp_dir}` because of ' +
                    'an error:\n\n')
                print(logs)

                if debug == 4:
                    input('continue:')

            return {}, logs

    logs = []

    target_files = { t: {} for t in target_files }

    current_path = os.getcwd()

    os.chdir(work)

    cmd_list = [
        "make clean",
        "make compile",
        "make run",
        "make coverage",
    ]

    for cmd in cmd_list:
        if ssh:
            cmd = '/bin/sh -c ". ~/compilers.sh ; ' + cmd + '"'
            stdout, stderr = execute_remote_command(
                ssh,
                path=temp_dir,
                command=cmd,
                debug=debug,
            )
        else:
            try:
                data = subprocess.run(
                    cmd,
                    capture_output=True,
                    shell=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
            except Exception as e:
                print(e)
                fatal_error(work)
                # import pdb; pdb.set_trace()

            stdout = data.stdout
            stderr = data.stderr

        if (
                (stderr and 'error' in stderr.lower() and not 'Number of failures' in stdout) or
                ('core dump' in stderr)
        ):
            os.chdir(current_path)
            logs.append(f'\n\nstopping at {cmd} because of an error\n\n')
            logs.append(stdout)
            logs.append(stderr)

            logs = '\n\n'.join(logs)

            # has error: just return everything

            if verbose:
                print(f'    stopping at {cmd} because of an error:\n\n')
                print(logs)

                if debug == 4:
                    input('continue:')

            return {}, logs

        logs.append(stdout)

    if ssh:
        stdout, stderr = execute_remote_command(
            ssh, command=f'ls {temp_dir}', debug=debug)

        if stderr:
            os.chdir(current_path)
            logs.append(stdout)
            logs.append(stderr)

            logs = '\n\n'.join(logs)

            # has error: just return everything
            if verbose:
                print(
                    '    stopping at `executing_remote_command` '
                    'because of an error:\n\n'
                )
                print(logs)

                if debug == 4:
                    input('continue:')

            return {}, logs

        to_files = [file[len(work)+1:] for file in glob.glob(work + '/*')]
        from_files = [file.strip() for file in stdout.split('\n')]
        for file in from_files:
            if file and file not in to_files:
                if verbose:
                    print(f'... copying {file} from {ssh}/{temp_dir}')
                copy_from_remote(
                    ssh, f'{temp_dir}/{file}', work, debug=debug)
        execute_remote_command(ssh, command=f'rm -rf {temp_dir}', debug=debug)

    files = process_coverage_info(
        work=work,
        ssh=ssh,
        temp_dir=temp_dir,
        target_files=target_files,
        verbose=verbose
    )

    if not ssh:
        _ = subprocess.run(
            "make clean", capture_output=True, shell=True,
            text=True)

    os.chdir(current_path)

    return files, '\n\n'.join(logs)


def _get_coverage_cc(
        test_dir, 
        src_dir, 
        files, 
        functions,
        cflags="", 
        ldflags="",
        ssh="",
        declaration_lines=[],
        create_makefile=True,
        debug=False):

    '''
        Get coverage information for files and functions.

        :param test_dir: test directory where test will be executed.
        :param src_dir: source directory for source code.
        :param files: files to scan for coverage metrics.
        :param functions: functions to look for in files.
        :param cflags: arguments to be used in compilation.
        :param ldflags: arguments to be used in linkage.
        :param ssh: '' or <user>@<ip> for ssh connection.
        :param declaration_lines: list of lines that should be filtered as they
                are C-style variable declarations.
        :param create_makefile: if true, generate makefile. otherwise, just run.
        :param debug: if true, help debug output messages.

        :return: list of missing coverage, one per file inside the
                 functions, and logs of outputs.
    '''

    # need to make sure -I has absolute paths
    cflags_list = cflags.split(' ')
    for i in range(len(cflags_list)):
        if cflags_list[i][:2] == '-I':
            cflags_list[i] = '-I' + os.path.abspath(cflags_list[i][2:])
    cflags = ' '.join(cflags_list)

    if isinstance(functions, dict):
        # let's just make sure we count all files and all functions
        # in the list
        files = list(set(list(functions.values()) + files))

    elif not isinstance(functions, list):
        functions = [functions]

    testfiles = glob.glob(f'{test_dir}/test_*.c*')

    assert len(testfiles) == 1

    testfile = os.path.basename(testfiles[0])

    if create_makefile:
        verbose = True
        target_files = generate_makefile(
                work=test_dir,
                testfile=testfile,
                target_files=files,
                cflags=cflags,
                ldflags=ldflags,
                ssh=ssh)

    else:
        verbose = False
        target_files = files

    files, logs = execute_makefile(
        test_dir, target_files, ssh=ssh, verbose=verbose, debug=debug)

    result = []

    r = re.compile(r'[\[\]\(\);=]')  # \{

    for f in files:
        # Some versions of lcov does not set hi field, so we need to estimate
        # it.
        source = open(f, "r").readlines()
        hi_max =len(source)
        functions_in_files = files[f]['functions']
        lines = files[f]['lines']

        lo = [functions_in_files[fct]['lo'] for fct in functions_in_files]
        hi = [functions_in_files[fct]['hi'] for fct in functions_in_files]

        indexes = np.argsort(lo)
        los = np.array(lo)[indexes]
        his = np.array(hi)[indexes]

        for i in range(len(lo)):
            # if 'hi' == -1, we could not detect this information from FN:
            # in lcov.
            if his[i] == -1:
                if i+1 >= len(his):
                    his[i] = hi_max
                else:
                    his[i] = lo[i+1] - 1

        for fct in functions_in_files:
            stripped_fct = fct.split('(')[0]
            if fct not in functions and stripped_fct not in functions:
                continue

            if isinstance(functions, dict):
                # check if f is inside dictionary functions for the
                # function call
                if not (
                        functions.get(stripped_fct, "") == f or 
                        functions.get(fct, "") == f 
                    ):
                    continue

            lo = functions_in_files[fct]['lo']
            hi = functions_in_files[fct]['hi']
            if hi == -1:
                index = list(los).index(lo)
                hi = his[index]
            count = functions_in_files[fct]['count']

            if count == 0:
                if verbose:
                    print(f'... function {fct} is not called')

                missing_lines = [
                    str(m)
                    for m in list(range(lo, hi+1))
                        # filter some lines that we know gcov will
                        # continuously flag as missed coverage
                        if r.search(source[m-1]) and m not in declaration_lines
                        # and source[m-1].strip() not in ['{','}']
                ]

                result.append(
                    f"{f}:{stripped_fct}: could not reach lines: " +
                    f"{','.join(missing_lines)}")
                continue

            missing_lines = []
            for l in range(lo, hi):
                if l not in lines or not lines[l]:
                    if r.search(source[l-1]) and l not in declaration_lines:
                        # and source[l-1].strip() not in ['{','}']:
                        missing_lines.append(str(l))

            if missing_lines:
                result.append(
                    f"{f}:{stripped_fct}: could not reach lines: " +
                    f"{','.join(missing_lines)}")

    fix_this = False
    for line in logs.split('\n'):
        line = line.lower()
        if 'makefile' in line and 'compile' in line and 'error' in line:
            fix_this = True
            break
        elif 'make' in line and 'coverage' in line and 'error' in line:
            fix_this = True
            break

    return fix_this, result, logs


def get_coverage_cc(
        test_dir,
        src_dir,
        files,
        functions,
        cflags="",
        ldflags="",
        ssh="",
        declaration_lines=[],
        create_makefile=True,
        debug=False):

    '''
        Get coverage information for files and functions.  This version of get_coverage_cc
        overcomes a limitation of the Agentic flow that the reflection step takes too long
        to stabilize in case one of the tests core dumps, as in a core dump, we do not have
        any additional information about the test.

        So, whenever a core dump happens, we comment out the test, rerun get_coverage_cc,
        and inform the reflection by the means of CRASH tags in the testcase.

        :param test_dir: test directory where test will be executed.
        :param src_dir: source directory for source code.
        :param files: files to scan for coverage metrics.
        :param functions: functions to look for in files.
        :param cflags: arguments to be used in compilation.
        :param ldflags: arguments to be used in linkage.
        :param ssh: '' or <user>@<ip> for ssh connection.
        :param declaration_lines: list of lines that should be filtered as they
                are C-style variable declarations.
        :param create_makefile: if true, generate makefile. otherwise, just run.
        :param debug: if true, help debug output messages.

        :return: list of missing coverage, one per file inside the
                 functions, and logs of outputs.
    '''

    run_once_more = True
    while run_once_more:
        run_once_more = False

        fix_this, result, logs  = _get_coverage_cc(
            test_dir=test_dir,
            src_dir=src_dir,
            files=files,
            functions=functions,
            cflags=cflags,
            ldflags=ldflags,
            ssh=ssh,
            declaration_lines=declaration_lines,
            create_makefile=create_makefile,
            debug=debug
        )

        core_dump = re.compile(r'core dump')
        has_core_dump = False
        logs_list = logs.split('\n')
        testcase = ''
        for l in range(len(logs_list)):
            if core_dump.search(logs_list[l]):
                has_core_dump = True
                ll = l
                # LLMs do not obey instructions sometimes, so testca
                while ll > 0 and not re.search('(Test|Use).+:', logs_list[ll-1]):
                    ll -= 1
                if ll == 0:
                    # we could not find a matching "Test" because
                    # of LLM not following instructions
                    # just pick up previous line
                    ll = l
                message = logs_list[ll-1]
                testfile = glob.glob(f'{test_dir}/test_*.c*')[0]
                code = open(testfile, "r").read().split('\n')
                # search for testcase number
                testcase = ""
                c = 0
                while c < len(code):
                    if message in code[c]:
                        c += 1
                        testcase = code[c]
                        break
                    c += 1
                # name should be 'void test_case_1() {'
                try:
                    # run_with_timeout(test_case_n);
                    testcase = testcase.split('(')[1].split(')')[0].strip()
                except:
                    # cannot find it, we will try to throw this to the LLM to solve
                    if verbose:
                        print('... cannot find testcase. We will try to use the LLM to do it.')
                    return fix_this, result, logs

        if has_core_dump:
            # comment it out in main
            if create_makefile and 'CRASH' not in code[c]:
                code[c] = (
                    f"        // CRASH: {message.strip()}\n"
                    f"        // {code[c].strip()}\n"
                    f"        throw std::runtime_error(\"crash\");"
                )
                with open(testfile, "w") as f:
                    f.write('\n'.join(code))
                print()
                print(f"Regenerated testcase {os.path.basename(testfile)} commenting out {testcase}")
                print()

    return fix_this, result, logs

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
    # cflags: arguments to be used in compilation.
    # ldflags: arguments to be used in linkage.
    # ssh: '' or <user>@<ip> for ssh connection.

    test_dir = args.test_dir
    src_dir = args.src_dir
    files = args.files
    functions = args.functions
    cflags = args.cflags
    ldflags = args.ldflags
    ssh = args.ssh
    debug = args.debug

    src_dir = fix_relative_paths(src_dir)
    test_dir = fix_relative_paths(test_dir)
    files = fix_relative_paths(files)

    fix_this, result, log = get_coverage_cc(
        test_dir=test_dir,
        src_dir=src_dir,
        files=files,
        functions=functions,
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
