# Copyright 2025 Claudionor N. Coelho Jr

import os
from argparse import ArgumentParser

from pycparser import parse_file, c_ast
import pycparser_fake_libc
import re
import subprocess
import yaml

try:
    from .utils import fix_relative_paths, create_cpp_args, fatal_error
except:
    from utils import fix_relative_paths, create_cpp_args, fatal_error

try:
    from .cpp_flatten import cpp_flatten
except:
    from cpp_flatten import cpp_flatten


DEBUG = int(os.getenv('DEBUG', 0))

def find_file_to_include(pattern, string_list, group=0):
    '''
        Finds first file included when pattern is found.

        Typically, we will find the following:

            ...
            # 3 "file_to_include.h" ...
            ...
            <pattern>
            ...

        We want to return "path_to_file_to_include.h"

        :param pattern: pattern to be search.
        :param string_list: list of lines to search for pattern.
        :param group: group to check.

        :return: file to include.
    '''
    pat = re.compile(pattern)
    for l in range(len(string_list)):
        if m := pat.search(string_list[l]):
            line = string_list[l]
            if line[0].strip() == '#': # it is a pragma, let's ignore for now
                continue
            l = l - 1
            line = string_list[l].strip()
            while True:
                if line:
                    if line[0] == '#': break
                l = l - 1
                line = string_list[l].strip()
            # at this time, we found the first file that includes the type
            path_to_file = string_list[l].split(' ')[2].split('"')[1]
            return os.path.basename(path_to_file)

    return ""


def is_same(o1, o2):
    '''
        Performs deep comparison if o1 and o2 are equal.

        :param o1: first object to be compared.
        :param o2: second object to be compared.

        :return: True if o1 == o2, False otherwise.
    '''

    # if they have different types, they are not equal.
    if type(o1) != type(o2):
        return False

    # if o1 and o2 are dictionaries, check each key.
    if isinstance(o1, dict):
        if len(o1) != len(o2):
            return False
        keys = o1.keys()
        for k in keys:
            if k not in o2:
                return False
            if not is_same(o1[k], o2[k]):
                return False
        return True
    # if o1 and o2 are lists, check each item.
    elif isinstance(o1, list):
        if len(o1) != len(o2):
            return False

        for i1, i2 in zip(o1, o2):
            if not is_same(i1, i2):
                return False
        return True
    # otherwise, just compare o1 and o2
    else:
        return o1 == o2


def in_obj_list(obj, obj_list):
    '''
        Checks if 'obj' is in a list of objects.

        :param obj: object to be checked.
        :param obj_list: list of objects.

        :return: True is object is contained, False otherwise.
    '''

    # we expect a list, so if it is not a list, just bail out.
    if not obj_list:
        return False

    # performs deep comparison of each object in list.
    for o in obj_list:
        if is_same(obj, o):
            return True
    return False

# evaluates constant expressions like [A + B]

class ConstEval(c_ast.NodeVisitor):
    def __init__(self):
        self.values = {}

    def visit_Constant(self, node):
        if node.type == 'int':
            return int(node.value)
        elif node.type == 'float':
            return float(node.value)
        elif node.type == 'char':
            return ord(node.value.strip("'"))
        else:
            raise ValueError(f"Unsupported constant type: {node.type}")

    def visit_ID(self, node):
        # Assuming identifiers are constants with pre-defined values for this example
        return self.values.get(node.name, 0)

    def visit_BinaryOp(self, node):
        left_val = self.visit(node.left)
        right_val = self.visit(node.right)
        op = node.op
        if op == '+':
            return left_val + right_val
        elif op == '-':
            return left_val - right_val
        elif op == '*':
            return left_val * right_val
        elif op == '/':
            return left_val / right_val
        elif op == '%':
            return left_val % right_val
        elif op == '<<':
            return left_val << right_val
        elif op == '>>':
            return left_val >> right_val
        elif op == '|':
            return left_val | right_val
        elif op == '&':
            return left_val & right_val
        elif op == '^':
            return left_val ^ right_val
        elif op == '&&':
            return int(bool(left_val) and bool(right_val))
        elif op == '||':
            return int(bool(left_val) or bool(right_val))
        else:
            raise ValueError(f"Unsupported binary operator: {op}")

    def visit_UnaryOp(self, node):
        operand_val = self.visit(node.expr)
        op = node.op
        if op == '+':
            return +operand_val
        elif op == '-':
            return -operand_val
        elif op == '~':
            return ~operand_val
        elif op == '!':
            return int(not operand_val)
        else:
            raise ValueError(f"Unsupported unary operator: {op}")

    def visit_Paren(self, node):
        return self.visit(node.expr)

    def evaluate(self, node):
        return self.visit(node)


def get_function_interface(filename, target, cflags=""):

    '''
        Extract function parameters and local variables.

        :param filename: Source file.
        :param work: Work directory.
        :param cflags: Flags for compilation including -I and -D.

        :return: module created.
    '''

    from pycparser import c_parser, c_ast

    def is_user_defined_type(typ):
        return isinstance(typ, (c_ast.Struct, c_ast.Union, c_ast.Enum, c_ast.Typedef))

    def get_only_type_name(typ):
        native_types = [
            'char', 'int', 'short', 'long', 'unsigned', 'long long', 'double',
            'float', 'void']
        if isinstance(typ, c_ast.TypeDecl):
            try:
                type_name = ' '.join(typ.type.names)
                all_native_types = all(t in native_types for t in typ.type.names)
                if all_native_types: return ''
            except:
                type_name = typ.type.name
            return type_name
        elif isinstance(typ, c_ast.PtrDecl):
            return get_only_type_name(typ.type)
        elif isinstance(typ, c_ast.ArrayDecl):
            return get_only_type_name(typ.type)
        elif is_user_defined_type(typ):
            type_name = ' '.join(typ.type.names) if (
                isinstance(typ, c_ast.Typedef)) else typ.name
            if type_name in native_types: return ''
            return type_name
        return '' if typ.name in ['char', 'int', 'float'] else typ.name

    def get_type_name(typ):
        qualifiers = []
        if isinstance(typ, c_ast.TypeDecl):
            if isinstance(typ.quals, list):
                qualifiers.extend(typ.quals)
            try:
                type_name = ' '.join(typ.type.names)
            except:
                type_name = typ.type.name
            return ' '.join(qualifiers) + ' ' + type_name if qualifiers else type_name
        elif isinstance(typ, c_ast.PtrDecl):
            if isinstance(typ.quals, list):
                qualifiers.extend(typ.quals)
            type_name = get_type_name(typ.type) + '*'
            return ' '.join(qualifiers) + ' ' + type_name if qualifiers else type_name
        elif isinstance(typ, c_ast.ArrayDecl):
            evaluator = ConstEval()
            value = 0
            if typ.dim:
                value = evaluator.evaluate(typ.dim)
            size = f'[{value}]' if typ.dim else '[]'
            typ = typ.type
            while isinstance(typ, c_ast.ArrayDecl):
                dim = typ.dim
                typ = typ.type
                if dim:
                    value = evaluator.evaluate(dim)
                    size = size + f'[{value}]'
                else:
                    size = size + '[]'
                    break
            return get_type_name(typ) + size
        elif isinstance(typ, c_ast.Typedef):
            return typ.name
        elif isinstance(typ, c_ast.Struct):
            return f'struct {typ.name}'
        elif isinstance(typ, c_ast.Union):
            return f'union {typ.name}'
        elif isinstance(typ, c_ast.Enum):
            return f'enum {typ.name}'
        return 'unknown'


    # Define a visitor class to extract function parameters and variable names
    class FuncParamVisitor(c_ast.NodeVisitor):
        _return_type = ''
        _return_type_name = ''
        _enable_visit = False
        _global_vars = set()
        _local_params = []
        _func_params = []
        _type_params = []
        _decl_lines = []
        _target = "main"

        def __init__(self, all_global_vars):
            self.enable_visit = False
            self.all_global_vars = all_global_vars

        def visit_FuncDef(self, node):
            if self._target == node.decl.name:
                self._return_type = get_type_name(node.decl.type.type)
                self._return_type_name = get_only_type_name(node.decl.type.type)
                if node.decl.type.args:
                    for decl in node.decl.type.args.params:
                        self._func_params.append(decl.name)
                        try:
                            self._type_params.append(
                                (
                                    get_type_name(decl.type),
                                    get_only_type_name(decl.type)
                                )
                            )
                        except:
                            if isinstance(decl, c_ast.ID):
                                self._type_params.append(
                                    ( decl.name, decl.name )
                                )
                            else:
                                print('--- ERROR ---')
                                print(decl)
                                fatal_error(self._target)
                                # import pdb; pdb.set_trace()
                if node.body.block_items:
                    for item in node.body.block_items:
                        self._local_params += self.get_local_vars("", item)
                self.enable_visit = True
                self.generic_visit(node)
                self.enable_visit = False

        def visit_Decl(self, node):
            if self.enable_visit:
                if node.coord.line not in self._decl_lines:
                    self._decl_lines.append(node.coord.line)
            self.generic_visit(node)

        def visit_ID(self, node):
            try:
                var_name = node.name
                if var_name in self.all_global_vars and var_name not in self._global_vars:
                    self._global_vars.add(var_name)
            except:
                pass

        def visit_Assignment(self, node):
            self.visit_ID(node.lvalue)
            self.visit(node.rvalue)

        def get_local_vars(self, item_id, item):
            if isinstance(item, c_ast.Decl):
                if item_id:
                    return [item_id + "_" + item.name]
                else:
                    return [item.name]
            elif isinstance(item, c_ast.Compound):
                block = item.block_items
                result = []
                for i, item in enumerate(block):
                    result += self.get_local_vars(item_id + f'__{i}', item) 
                return result
            else:
                return []

        def set_target(self, target):
            self._target = target

        def get_func_params(self):
            return self._func_params

        def get_type_params(self):
            return [t[0] for t in self._type_params]

        def get_type_names_params(self):
            return [t[1] for t in self._type_params]

        def get_local_params(self):
            return self._local_params

        def get_return_type(self):
            return self._return_type

        def get_return_type_name(self):
            return self._return_type_name

        def get_decl_lines(self):
            return self._decl_lines

    cpp_args = create_cpp_args(cflags) + ['-E'] + ['-I' + pycparser_fake_libc.directory]

    # Parse the C file
    ast = parse_file(
        filename, 
        use_cpp=True,
        cpp_path='clang',
        cpp_args=cpp_args)

    def get_global_vars(ast):
        global_vars = set()
        global_var_types = {}
        for node in ast.ext:
            if isinstance(node, c_ast.Decl):
                if not isinstance(node.type, c_ast.FuncDecl) and node.name not in global_vars:
                    # print(node.name)
                    try:
                        if not node.name: continue
                        global_vars.add(node.name)
                        global_var_types[node.name] = (
                            get_type_name(node.type),
                            get_only_type_name(node.type)
                        )
                    except:
                        global_var_types[node.name] = ( None, None )
        return global_vars, global_var_types

    global_vars, global_var_types = get_global_vars(ast)

    # Create a visitor instance and visit the AST
    visitor = FuncParamVisitor(global_vars)
    visitor.set_target(target)
    visitor.visit(ast)

    func_params = visitor.get_func_params()
    type_params = visitor.get_type_params()
    type_names_params = visitor.get_type_names_params()
    local_params = visitor.get_local_params()
    return_type = visitor.get_return_type()
    return_type_name = visitor.get_return_type_name()
    decl_lines = visitor.get_decl_lines()

    global_vars = list(visitor._global_vars)
    function_global_var_types = [ global_var_types[n][0] for n in global_vars ]
    function_global_var_type_names = [ global_var_types[n][1] for n in global_vars ]

    return {
        'params': func_params,
        'types': type_params,
        'type_names': type_names_params,
        'locals': local_params,
        'global_vars': global_vars,
        'global_var_types': function_global_var_types,
        'global_var_type_names': function_global_var_type_names,
        'return_type': return_type,
        'return_type_name': return_type_name,
        'decl_lines': decl_lines
    }

def find_all_functions_using_static_globals(file_class, function, dont_use_static_functions=False):
    '''
        Find all functions that use or set global variables of function 'function'.
        We want to use the functions with the same static storage class as 'function.

        :param file_class: file class from project-yaml.
        :param function: function name that we will compare.
        :param dont_use_static_functions: if true, we do not add static functions as they do not
            have external visibility.

        :return: list of functions.
    '''

    all_functions = set()
    # get all static globals used in function
    static_globals = set(file_class['__static__globals']).intersection(file_class[function]['globals'])
    function_is_static = 'static' in file_class[function]['storage']
    has_changed = True
    while has_changed:
        has_changed = False
        for fn in file_class:
            # we remove 'main' here.
            if fn.endswith('__globals') or fn == function or fn == 'main': continue
            fn_is_static = 'static' in file_class[fn]['storage']
            if dont_use_static_functions and fn_is_static: continue
            # we want to make sure the 'staticness' is the same for both functions
            if function_is_static != fn_is_static: continue
            if static_globals.intersection(file_class[fn]['globals']):
                all_functions.add(fn)
                diff = set(file_class[fn]['globals']).difference(static_globals)
                if diff:
                    static_globals = static_globals.union(diff)
                    has_changed = True
    return list(all_functions)


def get_extern_interface(file_class, filename, target, cflags, includes):
    '''
        Extract interface for extern in unit-test. This is needed because LLMs are
        getting confused when parameters to a function are user-defined types that
        are present in include files.

        Since we have to do here a complete scan of the AST, we also retrieve
        the declaration lines to avoid having to report false missing coverage
        targets on variable declarations later.

        :param file_class: Dictionary containing file information about target based on original file.
        :param filename: Source file.
        :param target: Target function name.
        :param cflags: Flags for compilation including -I and -D.
        :param includes: All include directories from -I.

        :return: "extern" declaration, list of declarations to be filtered out,
                and additional files needed.
    '''

    all_functions = find_all_functions_using_static_globals(file_class, target)

    declaration_lines = set()
    functions_interface = []
    for f in all_functions + [target]:
        params = get_function_interface(
            filename=filename,
            cflags=cflags,
            target=f)

        return_type = params["return_type"]

        param_interface = ", ".join(
            [f'{t}' for t in params["types"]])

        functions_interface.append(
            f"    {return_type} {f}({param_interface});"
        )

        declaration_lines = declaration_lines.union(params["decl_lines"])

    # last function name should be the target for this to work.
    # we look at the global variables set/gotten by target function.

    interface = ""
    for i in range(len(params['global_vars'])):
        name = params['global_vars'][i]
        if name not in file_class[target]['globals']: continue
        type = params['global_var_types'][i]
        interface += f"    {type} {name};\n"

    interface += "\n" + "\n".join(functions_interface)

    source_flatten_lines = cpp_flatten(
        filename=filename, cflags=cflags, includes=includes).split('\n')

    files_to_include = []

    all_type_names = (
            params["type_names"] +
            [t
             for v, t in zip(params["global_vars"], params["global_var_type_names"])
             if v in file_class[target]['globals']] +
            [params["return_type_name"]]
    )

    for type_name in all_type_names:
        if not type_name: continue
        if file := find_file_to_include(r'' + type_name, source_flatten_lines):
            files_to_include.append(file)

    return interface, list(declaration_lines), files_to_include


def parse_examples(examples, params, cex_list=[], debug=0):

    '''
        Parse example file.

        :param examples: examples' file.
        :param params: parameters to function (including locals).
        :param cex_list: list of counter-examples.
        :param debug: if > 0, print debug messages..

        :return: test values.
    '''

    drop_vars = ["goto_symex::guard"]

    if debug >= 3 or DEBUG >= 3:
        print('=' * 80)
        print(examples)
        print('=' * 80)
        if debug == 4 or DEBUG == 4: input('continue: ')

    func_params = set(params['params'])
    local_params = set(params['locals'])

    cex_token = '[Counterexample]'
    le = examples.find(cex_token)

    if le != -1:
        le = le + len(cex_token) + 1

    while le != -1:
        has_value = False
        input_map = {}
        param_map = { v: None for v in func_params }
        local_map = { v: None for v in local_params }
        examples = examples[le:]
        ri = examples.find(cex_token)
        if ri == -1:
            cex = examples
            le = ri
        else:
            cex = examples[:ri]
            le = ri + len(cex_token) + 1

        if debug >= 3 or DEBUG >= 3:
            print('#' * 80)
            print(cex)
            print('#' * 80)

        lines = cex.split('\n')
        for line in lines:
            if line.find(' = ') != -1:
                has_value = True
                if debug >= 3 or DEBUG >= 3:
                    print('>>>', line)

                ri = line.rfind('(')
                if ri != -1:
                    cex_line = line[:ri]
                else:
                    cex_line = line

                var_assignment = cex_line.split('=')
                try:
                    var = var_assignment[0].strip()
                    value = var_assignment[1].strip()
                except:
                    print(f'... cannot find assignment for line {line} [contact support]')
                    continue

                if value == 'ARRAY_OF':
                    value = line[ri+1:].split(')')[0]

                if var in param_map:
                    if isinstance(param_map[var], type(None)):
                        param_map[var] = value
                elif var in local_map:
                    if isinstance(local_map[var], type(None)):
                        local_map[var] = value
                elif var not in drop_vars:
                    if var in input_map:
                        input_map[var].append(value)
                    else:
                        input_map[var] = [value]

        cex = {
            'params': param_map,
            'inputs': input_map,
            'locals': local_map
        }

        if has_value and not in_obj_list(cex, cex_list):
            cex_list.append(cex)

            if debug >= 3 or DEBUG >= 3:
                print(len(cex_list), '-' * 60)
                print(cex_list[-1])
                if debug == 4 or DEBUG == 4: input('continue: ')

    return cex_list


def has_symbolic_failed(logs):
    '''
        Checks if symbolic engine failed.

        :param logs: log of execution.

        :return: True if symbolic has failed.
    '''

    got_an_error = False
    while True:
        le = logs.find("ERROR:")
        if le == -1:
            break
        logs = logs[le:]
        le = logs.find("\n")
        if le == -1:
            break
        if "Timed out" not in logs[:le]:
            got_an_error = True
            break
        logs = logs[le:]

    return got_an_error


def parse_cex(cex_list):
    '''
        Parses cex and return testcase in YAML format.

        :param cex_list: list of CEX's.

        :return: YAML representing instructions that one can use.
    '''
    # Generate directive for generation of test.
    test_cases = {}
    for i, test in enumerate(cex_list):
        label = f'Test case {i}'
        for field in test:
            # we do not process locals right now.
            if field == "locals": continue
            for var in test[field]:
                is_none = True
                var_list = []
                if isinstance(test[field][var], list):
                    for l in range(1, len(test[field][var])):
                        v = test[field][var][l]
                        if v == 'invalid-object': v = '`any pointer`'
                        if not isinstance(v, type(None)):
                            is_none = False
                        var_list.append(v)
                else:
                    v = test[field][var]
                    if v == 'invalid-object': v = '`any pointer`'
                    if not isinstance(v, type(None)):
                        is_none = False
                    var_list.append(v)

                if not is_none:
                    if label not in test_cases:
                        test_cases[label] = {}
                    if len(var_list) == 1:
                        test_cases[label][var] = var_list[0]
                    else:
                        test_cases[label][var] = var_list
    return yaml.safe_dump(test_cases, default_style=None)


def get_symbolic_test(
        filename,
        cflags,
        target,
        project,
        work,
        debug=False):

    '''
        Run esbmc to get symbolic tests.

        :param source_files: source files to run symbolic test.
        :param cflags: flags used to compile program.
        :param target: function/class name of target.
        :param project: project directory.
        :param work: directory where test will be generated.
        :param debug: if True, print debugging messages..

        :return: test program
    '''
    # get function interface parameters
    params = get_function_interface(
        filename=filename,
        cflags=cflags,
        target=target)

    current_path = os.getcwd()
    os.chdir(work)

    UNWIND = int(os.getenv('ESBMC_UNWIND', 20))
    UNWIND_STR = f'--unwind {UNWIND}'

    TIMEOUT = os.getenv('ESBMC_TIMEOUT', '10s')
    TIMEOUT_STR = '--timeout ' + TIMEOUT

    ESBMC_FLAGS = os.getenv('ESBMC_FLAGS', '')

    cflags_list = cflags.split(' ')
    for i in range(len(cflags_list)):
        if '-std=' in cflags_list[i] or '-ansi' in cflags_list[i]:
            cflags_list[i] = ''
        elif cflags_list[i] == '-include':
            cflags_list[i] = '--include-file'
    cflags = ' '.join(cflags_list)

    cmd_list = [
		f'esbmc {filename}',
        cflags,
        TIMEOUT_STR,
        UNWIND_STR,
        ESBMC_FLAGS,
		f'--function {target}',
		'--condition-coverage',
        #'--compact-trace', #'--no-slice',
		#'--generate-testcase',
		f'--cex-output {target}'
    ]

    cmd = ' '.join(cmd_list)

    if (debug): print(cmd)

    if debug == 4 or DEBUG == 4: input('continue: ')

    logs = [cmd]

    print(cmd)
    print()

    data = subprocess.run(cmd, capture_output=True, shell=True, text=True)

    if "ERROR:" in data.stderr:
        logs.append(data.stderr)

    cex_list = parse_examples(data.stderr, params, debug=debug)

    # check other errors

    cmd_list = [
		f'esbmc {filename}',
        cflags,
        TIMEOUT_STR,
		UNWIND_STR,
        ESBMC_FLAGS,
		f'--function {target}',
        '--multi-property',
		#'--compact-trace',
		'--overflow-check',
        '--force-malloc-success',
		'--memory-leak-check',
		'--struct-fields-check',
		'--ub-shift-check',
		'--unsigned-overflow-check',
		#'--generate-testcase',
		f'--cex-output {target}'
    ]

    cmd = ' '.join(cmd_list)

    if (debug): print(cmd)

    if debug == 4 or DEBUG == 4: input('continue: ')

    logs.append(cmd)

    print(cmd)
    print()

    data = subprocess.run(cmd, capture_output=True, shell=True, text=True)

    cex_list = parse_examples(data.stderr, params, cex_list, debug=debug)

    if "ERROR:" in data.stderr:
        logs.append(data.stderr)

    os.chdir(current_path)

    return cex_list, logs


def parse_args(arg_list: list[str] | None):
    '''
        Argument parser..

        :param arg_list: list of arguments to facilitate testing.
    '''

    parser = ArgumentParser()

    parser.add_argument('filename')
    parser.add_argument('-t', '--target', default='main')
    parser.add_argument('-w', '--work', default='.')
    parser.add_argument('-p', '--project', default='.')
    parser.add_argument('--cflags', default='')
    parser.add_argument('-D', default=[], action='append')
    parser.add_argument('-I', default=[], action='append')
    parser.add_argument('-d', '--debug', type=int, default=0)

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

    args.filename = os.path.abspath(args.filename)

    test_assignments, logs = get_symbolic_test(
        filename=args.filename, 
        cflags=args.cflags, 
        target=args.target,
        work=args.work,
        project=args.project,
        debug=args.debug
    )

    print(test_assignments)


if __name__ == '__main__':
    main()

