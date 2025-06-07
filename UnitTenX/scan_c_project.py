# Copyright 2025 Claudionor N. Coelho Jr

from argparse import ArgumentParser
import glob
import hashlib
import os
from pycparser import parse_file, c_ast
import pycparser_fake_libc
import re
import subprocess
from utils.utils import fix_relative_paths
from utils.utils import create_cpp_args
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

# need to scan for -I in project directory
#import glob
#for file in glob.glob("/path/to/directory/**/*.txt", recursive=True):
#    print(file)

def get_unique_hashed_filename(data):
    '''
        Gets unique hashed filename.

        :param data: list of files.

        :return: unique hashed filename.
    '''

    my_tuple = tuple(sorted(data))
    hash_object = hashlib.sha256(str(my_tuple).encode())
    hex_dig = hash_object.hexdigest()

    return hex_dig

def search_files(directory, pattern):

    '''
        Extracts recursively directories from root directory with pattern.

        :param directory: root directory.
        :param pattern: pattern to search for.

        :return: files
    '''
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(pattern):
                yield os.path.join(root, file)

def get_files_with_mask(project_list, ignore_list=[]):
    '''
        Extracts all C files from a project, except from ignore_list.

        :param project_list: list of project directories or files.
        :param ignore_list: list of project directories or files to ignore.

        :return: list of files
    '''

    files = []
    for entry in project_list:
        if os.path.isdir(entry):
            for file_path in search_files(entry, '.c'):
                files.append(file_path)
        elif entry.endswith('.c'):
            not_in_ignore = True
            for ignore in ignore_list:
                if ignore.find(entry):
                    not_in_ignore = False
                    break
            if not_in_ignore:
                files.append(entry)
    return files


def get_global_variables_defined_in_file(ast, filename):
    '''
        Extracts global variables for a file.

        :param ast: pycparser AST.
        :param filename: Source file.

        :return: global and statically global variables defined in file.
    '''
    global_vars = []
    static_global_vars = []
    for node in ast.ext:
        if node.coord.file == filename: # this only looks for locally defined variables
            if isinstance(node, c_ast.Decl) and not isinstance(node.type, c_ast.FuncDecl):
                # we do not look for static as they are hidden.
                if node.storage == [] or ('extern' in node.storage and 'static' not in node.storage):
                    if node.name:
                        global_vars.append(node.name)
                if 'static' in node.storage:
                    if node.name:
                        static_global_vars.append(node.name)
    return global_vars, static_global_vars

def get_global_variables(ast):
    '''
        Extracts global variables for a file, regardless if they are locally defined or not.

        :param ast: pycparser AST.

        :return: all global variables in file.
    '''

    global_vars = set()
    for node in ast.ext:
        if (
                isinstance(node, c_ast.Decl) and
                not isinstance(node.type, c_ast.FuncDecl)
        ):
            if node.name:
                global_vars.add(node.name)
    return global_vars


def get_functions(filename, cflags=""):

    '''
        Extract function signatures, with lines, params and calls.

        :param filename: Source file.
        :param cflags: Flags for compilation including -I and -D.

        :return: module created.
    '''

    # Define a visitor class to extract function parameters and variable names

    class FunctionCallVisitor(c_ast.NodeVisitor):
        def __init__(self):
            self.callees = []

        def visit_FuncCall(self, node):
            self.callees.append(node.name.name)

            if node.args:
                self.visit(node.args)

    class FileVisitor(c_ast.NodeVisitor):
        file_signature = { '__globals': [], '__static__globals': [] }
        file = None

        def __init__(self, filename, all_global_vars, globals_in_file, static_globals_in_file):
            self.file = filename
            self.all_global_vars = all_global_vars
            self.file_signature['__all__globals'] = list(all_global_vars)
            self.file_signature['__globals'] = globals_in_file
            self.file_signature['__static__globals'] = static_globals_in_file

        def _find_end_line(self, node):
            max_line = node.coord.line
            for child in node.body.block_items:
                max_line = max(max_line, self._get_node_max_line(child))
            return max_line

        def _get_node_max_line(self, node):
            if isinstance(node, c_ast.Compound):
                max_line = node.coord.line
                for child in node.block_items:
                    max_line = max(max_line, self._get_node_max_line(child))
                return max_line
            else:
                return node.coord.line

        def visit_ID(self, node):
            try:
                var_name = node.name
                if (
                        var_name in self.all_global_vars and
                        var_name not in self.file_signature[self.func_name]['globals']
                ):
                    self.file_signature[self.func_name]['globals'].append(var_name)
            except:
                pass

        def visit_FuncDef(self, node, in_current_function=None):
            if not in_current_function:
                self.func_name = node.decl.name
                fcv = FunctionCallVisitor()
                fcv.visit(node)
                line_end = self._find_end_line(node)
                self.file_signature[self.func_name] = {
                    'coord': [node.coord.line, line_end],
                    'params': [],
                    'storage': node.decl.storage,
                    'functions': list(set(fcv.callees)),
                    'globals': [],
                }
                if node.decl.type.args:
                    for decl in node.decl.type.args.params:
                        if decl.name:
                            self.file_signature[node.decl.name][
                                'params'].append(decl.name)

                # get global variable usage
                for child in node.children():
                    if child[0] == 'body':
                        self.generic_visit(child[1])
            else:
                if hasattr(node, 'coord') and hasattr(node.coord, 'line'):
                    max_line = self.file_signature[in_current_function][
                        'coord'][1]
                    self.file_signature[in_current_function][
                        'coord'][1] = max(max_line, node.coord.line)

            if not in_current_function:
                in_current_function = node.decl.name

            for child in node.children():
                self.visit_FuncDef(child[1],
                                   in_current_function=in_current_function)

        def visit_Assignment(self, node):
            self.visit_ID(node.lvalue)
            self.visit(node.rvalue)

        def get_file_signature(self):
            return self.file_signature

    cpp_args = create_cpp_args(cflags) + ['-E'] + ['-I' + pycparser_fake_libc.directory]

    # run first cpp to check if there are any errors as we are in exploratory mode
    cmd = 'clang ' + ' ' + ' '.join(cpp_args) + ' ' + filename
    print(f'... processing {filename}')
    data = subprocess.run(cmd, capture_output=True, shell=True, text=True)

    if data.stderr:
        print(cmd)
        print(data.stderr)
        raise ValueError('Compilation error')

    # Parse the C file
    try:
        ast = parse_file(
            filename,
            use_cpp=True,
            cpp_path='clang',
            cpp_args=cpp_args)
    except Exception as e:
        print(e)
        print(cmd)
        print('parse file crashed')
        raise ValueError('Unknown construct in C')

    # Get all global vars in this scope
    all_global_vars = get_global_variables(ast)
    globals_in_file, static_globals_in_file = get_global_variables_defined_in_file(ast, filename)

    # let's not block now to see what the LLM and formal will do
    # if len(all_global_vars) != len(globals) + len(static_globals):
    #    print(filename)
    #    print(all_global_vars)
    #    print(globals)
    #    print(static_globals)
    #    assert len(all_global_vars) == len(globals) + len(static_globals)

    # Create a visitor instance and visit the AST
    visitor = FileVisitor(filename, all_global_vars, globals_in_file, static_globals_in_file)
    file_signature = visitor.get_file_signature()

    visitor.visit(ast)

    # we need to fix the end of line as it does not include }
    code_str = open(filename,"r").read()
    code = code_str.split('\n')
    for function in file_signature:
        if function.endswith('__globals'):
            continue
        coords = file_signature[function]['coord']
        first_line, last_line = coords
        possible_name = code[first_line-1].strip().split('(')
        pattern = r'//.*?$|/\*.*?\*/'
        possible_name[0] = re.sub(pattern, '', possible_name[0], flags=re.MULTILINE | re.DOTALL)
        if len(possible_name) > 1 and data.stdout.find(possible_name[0]) < 0:
            # let's leave it as name is a macro
            continue
        open_brackets = ''.join(code[first_line:last_line]).count('{')
        close_brackets = ''.join(code[first_line:last_line]).count('}')
        last_line += 1
        while last_line < len(code):
            close_brackets += code[last_line-1].count('}')
            open_brackets += code[last_line-1].count('{')
            if open_brackets > close_brackets:
                last_line += 1
            else:
                break
        assert open_brackets == close_brackets
        coords[1] = last_line

    return file_signature


def scan_project(project_list, cflags, use_cache, save_to_cache, stop_on_error):
    '''
        Test routine for get_symbolic_test.

        :param project_list: list of files or project directories.
        :param cflags: cflags in string format.
        :param use_cache: if true, caches everything to avoid duplication.
        :param save_to_cache: if true, save result in cache.
        :param stop_on_error: if true, stops on error.

        :return: project db
    '''

    has_errors = False
    cache_dir = os.environ.get('UNIT_TENX_CACHE', '.cache')

    os.makedirs(cache_dir, exist_ok=True)

    files = get_files_with_mask(project_list=project_list, ignore_list=[])

    cache_filename = (
            cache_dir + '/' +
            get_unique_hashed_filename(files) + '.yaml'
    )

    if use_cache:
        try:
            with open(cache_filename, 'r') as fp:
                project_db = yaml.load(fp, Loader=Loader)

            # just do a sanity check :-)
            if sorted(project_db['files'].keys()) == sorted(files):
                print(f'... using cached file {cache_filename}')
                print()
                return project_db
        except:
            pass

    project_yaml = {}

    for filename in files:
        try:
            functions_signature = get_functions(
                filename=filename,
                cflags=cflags
            )
        except ValueError:
            functions_signature = {}
            has_errors = True

        project_yaml[filename] = functions_signature

    if stop_on_error and has_errors:
        raise ValueError('Could not finish')

    functions_yaml = {}

    for prj_filename in project_yaml:
        for prj_function in project_yaml[prj_filename]:
            if prj_function.endswith('__globals'):
                continue
            if prj_function not in functions_yaml:
                functions_yaml[prj_function] = [prj_filename]
            else:
                functions_yaml[prj_function].append(prj_filename)

    project_db = {
        'files': project_yaml,
        'functions': functions_yaml
    }

    if save_to_cache:
        with open(cache_filename, 'w') as f:
            yaml.dump(project_db, f, default_flow_style=False)

    return project_db


def parse_args(arg_list: list[str] | None):
    '''
        Argument parser..

        :param arg_list: list of arguments to facilitate testing.
    '''

    parser = ArgumentParser()

    parser.add_argument('project', nargs='+')
    parser.add_argument('--cflags', default='')
    parser.add_argument('-D', default=[], action='append')
    parser.add_argument('-I', default=[], action='append')
    parser.add_argument('-d', '--debug', type=int, default=0)
    parser.add_argument('--use-cache', default=False, action='store_true')
    parser.add_argument('--dont-save-to-cache', default=False, action='store_true')
    parser.add_argument('--stop-on-error', default=False, action='store_true')

    args = parser.parse_args(arg_list)

    if args.cflags and args.cflags[0] in ['"', "'"]:
        args.cflags = args.cflags[1:-1]

    return args


def main(arg_list: list[str] | None = None):
    '''
        Test routine for get_symbolic_test.

        :param arg_list: list of arguments to facilitate testing.
    '''

    args = parse_args(arg_list)

    args.I = fix_relative_paths(args.I)

    Ds = ' '.join(['-D' + inc for inc in args.D])
    Is = ' '.join(['-I' + inc for inc in args.I])
    args.cflags = (args.cflags + ' ' + Ds + ' ' + Is).strip()

    try:
        result = scan_project(
            project_list=args.project,
            cflags=args.cflags,
            use_cache=args.use_cache,
            save_to_cache=not args.dont_save_to_cache,
            stop_on_error=args.stop_on_error)

        print(yaml.dump(result))
    except ValueError as e:
        print(e)
        print('Please fix errors')


if __name__ == '__main__':
    main()



