# Copyright 2025 Claudionor N. Coelho Jr

import argparse
import pycparser_fake_libc
import numpy as np
import subprocess

try:
    from .utils import *
except:
    from utils import *


def cpp_flatten(filename, cflags="", includes=[]):

    '''
        Add all include files in source code (but only the ones in the
        user's project path or in includes).
        

        :param filename: file to be read.
        :param cflags: all c/cxx flags to be used at compile time.
        :param includes: all include directories added to cflags.

        :return: string contained file read for llm.
                 
    '''

    cmd = f'clang -E {filename} '

    if filename.endswith('.c'):
        # add fake pycparser lib to reduce amount of garbage in cpp
        cmd += f'-I{pycparser_fake_libc.directory} '

    cmd += cflags

    all_paths = [filename] + includes

    data = subprocess.run(cmd, capture_output=True, shell=True, text=True)

    if data.stderr:
        print(data.stderr)
        raise ValueError

    lines = data.stdout.split('\n')

    result = []
    block = []
    use_this = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if len(line) > 0 and line[0] == '#':
            # check if pragma is '# <number> "<filename>" (<number> )*'
            fields = line.split(' ')
            file_pragma = fields[2]
            if file_pragma[0] != '"':
                i += 1
                block.append(line)
                continue

            dirpath, basename = os.path.split(file_pragma[1:-1])

            if use_this:
                result.append('\n'.join(block))

            block = [line]
            use_this = np.any([dirpath in p for p in all_paths])

        else:
            block.append(line)

        i += 1
    if block and use_this:
        result.append('\n'.join(block))

    return '\n'.join(result)


def parse_args(arg_list: list[str] | None):
    '''
        Argument parser..

        :param arg_list: list of arguments to facilitate testing.
    '''

    parser = argparse.ArgumentParser()

    parser.add_argument('filename')
    parser.add_argument('--cflags', type=str, default='')
    parser.add_argument('-D', default=[], action='append')
    parser.add_argument('-I', default=[], action='append')

    args = parser.parse_args(arg_list)

    return args

def main(arg_list: list[str] | None = None):
    '''
        Test routine for cpp_flatten.

        :param arg_list: list of arguments to facilitate testing.
    '''

    args = parse_args(arg_list)

    args.I = fix_relative_paths(args.I)

    Ds = ' '.join(['-D' + inc for inc in args.D])
    Is = ' '.join(['-I' + inc for inc in args.I])
    args.cflags = args.cflags + ' ' + Ds + ' ' + Is

    dirpath, basename = os.path.split(args.filename)

    dirpath = fix_relative_paths([dirpath])[0]
    args.filename = os.path.join(dirpath, basename)

    source = cpp_flatten(args.filename, args.cflags, args.I)

    print(source)


if __name__ == '__main__':
    main()
    
