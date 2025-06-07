# Copyright 2025 Claudionor N. Coelho Jr

from argparse import ArgumentParser
import glob
import networkx as nx
import os
import re
from scan_c_project import scan_project
import shutil
import subprocess
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


def scan_recursively(u, filename, functions, project_yaml, graph, files, config, debug=False):
    '''
        Scans recursively call graph of function using granularity of files.

        :param u: id (integer) of node calling this function.
        :param filename: filename of function being called.
        :param functions: functions being called.
        :param project_yaml: project yaml.
        :param graph: graph to build call graph.
        :param files: map from files to functions being added.
        :param config: alternate configuration to disambiguate multiple matches to functions.
        :param debug: if true, print messages

        :return: None
    '''

    existing_node = False
    if filename in files:
        w = files[filename]['node_id']
        if u != w:
            graph.add_edge(w, u)
        new_functions = []
        for function in functions:
            if function not in files[filename]['functions']:
                existing_node = True
                files[filename]['functions'].append(function)
                new_functions.append(function)
        if not new_functions:
            return
    else:
        files[filename] = {
            'node_id': graph.number_of_nodes() + 1,
            'functions': functions
        }
        new_functions = functions

    if u > 0:
        u_label = [f for f in files if files[f]['node_id'] == u][0]
    else:
        u_label = '<sink>'

    if debug: print(f'... adding {filename} {','.join(new_functions)} from {u_label}')
    v = files[filename]['node_id']

    graph.add_node(v, name=filename)
    if not existing_node and u > 0 and u != v:
        graph.add_edge(v, u)
        if debug: print(f'... adding node {v} : {filename} to {u} : {u_label}')

    proj_filenames = project_yaml['files']
    proj_functions = project_yaml['functions']

    functions = set()
    for function in new_functions:
        functions = functions.union(proj_filenames[filename][function]['functions'])
    functions = list(functions)

    for func in functions:
        if func not in proj_functions:
            if debug: print(f'... skipping {func}')
            continue
        filenames = proj_functions[func]
        if len(filenames) == 1:
            fn = filenames[0]
        else:
            # has more than one match, prefer to use 'local' version
            fn = None
            for f in filenames:
                if f.endswith(filename):
                    fn = filename
                    break
            if isinstance(fn, type(None)):
                if config and config.get(func, None):
                    for f in filenames:
                        if config[func] in f:
                            fn = f
                            print(f'... using function {func} from {f} in configuration file.')
                            break
                if isinstance(fn, type(None)):
                    raise ValueError(
                        f'More than a candidate for {func} in ' +
                        f'{' '.join(filenames)}')

        scan_recursively(
            u=v,
            filename=fn,
            functions=[func],
            project_yaml=project_yaml,
            graph=graph,
            files=files,
            config=config,
            debug=debug)


def find_all_functions_using_static_globals(file_class, function, dont_use_static_functions=False):
    '''
        Find all functions that use or set global variables of function 'function'.

        :param file_class: file class from project-yaml.
        :param function: function name that we will compare.
        :param dont_use_static_functions: if true, we do not add static functions as they do not
            have external visibility.

        :return: list of functions.
    '''

    all_functions = set([function])
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

def find_configuration(project_yaml, filename, function, config):
    '''
        Test routine for get_symbolic_test.

        :param project_yaml: yaml project containing maps of files to functions.
        :param filename: filename to be scanned.
        :param function: function name to be scanned.
        :param config: alternate configuration to disambiguate multiple matches to functions.
    '''

    if filename in project_yaml['files']:
        filenames = [filename]
    else:
        # fix filename to be one of the filenames
        filenames = [f for f in project_yaml['files'] if f.endswith(filename)]

    all_functions = find_all_functions_using_static_globals(
        project_yaml['files'][filenames[0]], function)

    # find functions in current file

    assert len(filenames) == 1 # we should only have one

    filename = filenames[0]

    graph = nx.DiGraph()

    files = {}
    # add all functions accessing global variables
    scan_recursively(0, filename, all_functions, project_yaml, graph, files, config, debug=False)

    nodes_to_files = {
        files[f]["node_id"] : {
            "name": f,
            "functions": list(set(files[f]["functions"]))
        }
        for f in files
    }

    top_sort = list(nx.topological_sort(graph))

    result = []
    for i in top_sort:
        result.append(nodes_to_files[i])

    return {
        "project": project_yaml,
        "instrumented": result
    }


def generate_code(project_yaml, instruction_list, target_function=''):
    '''
        Generates code following instruction list.

        :param project_yaml: project yaml.
        :param instruction_list: list of files to add and functions to keep.
        :param target_function: do not change if this is the target name, unless it is main.
        :return:
    '''
    # read all files in instruction list
    files = [
        open(f['name'], 'r').read() for f in instruction_list
    ]

    # print()
    for i in range(len(files)):
        fn = instruction_list[i]['name']

        assert fn in project_yaml['files']

        if 'redirect__globals' not in project_yaml['files'][fn]:
            project_yaml['files'][fn]['redirect__globals'] = {}

        which_functions_to_keep = instruction_list[i]['functions']
        prefix, suffix = os.path.splitext(os.path.basename(fn))
        prefix = re.sub(r'[^a-zA-Z0-9]', '_', prefix)
        static_variables = project_yaml['files'][fn]['__static__globals']

        def replacement(_from, _to):
            def _replacement(match):
                start, end = match.span()
                if re.search(
                    r"#include\s*\<\s*" + re.escape(_from) + r"[^\>]*\>",
                    files[i][start-20:end+30]
                ):
                    return match.group()
                return match.group().replace(_from, _to)
            return _replacement

        for j, var in enumerate(static_variables):
            pattern = r"(?:^|[^'\"\<A-Za-z0-9_])" + re.escape(var) + r"(?:[^'\"\>A-Za-z0-9_]|$)"
            new_name = '__' + prefix + '_' + var
            if var.startswith('__' + prefix): continue
            print(f'... replacing static variable {var} by {new_name}')
            files[i] = re.sub(pattern, replacement(var, new_name), files[i])
            project_yaml['files'][fn]['redirect__globals'][var] = new_name
        for func in project_yaml['files'][fn]:
            if func.endswith('__globals'): continue
            func_class = project_yaml['files'][fn][func]
            if 'static' in func_class['storage'] or func == 'main':
                pattern = r"(?:^|[^'\"A-Za-z0-9_])" + re.escape(func) + r"(?:[^'\"A-Za-z0-9_]|$)"
                new_name = '__' + prefix + '_' + func
                if func != 'main' and new_name == target_function: continue
                print(f'... replacing {func} by {new_name} in {target_function}')
                files[i] = re.sub(pattern, replacement(func, new_name), files[i])
                project_yaml['files'][fn]['redirect__globals'][func] = new_name
        files[i] = files[i].split('\n')
        what_to_delete = []
        for this_function in project_yaml['files'][fn]:
            # we store globals in this area
            if this_function.endswith('__globals'):
                continue
            if this_function not in which_functions_to_keep:
                what_to_delete.append(project_yaml['files'][fn][this_function]['coord'])

        what_to_delete = list(reversed(sorted(what_to_delete)))

        # print(f'...keeping {which_functions_to_keep}')
        # print(f'...{fn}: deleting lines {what_to_delete}')

        for coord in what_to_delete:
            le, ri = coord[0]-1, coord[1]-1
            files[i] = (
                    files[i][:le] +
                    [f'/* unit-tenx {ri+2} "{fn}" 2 */'] +
                    files[i][ri+1:]
            )

        files[i] = (
            f'/* ----- {fn} ----- */\n\n' +
            f'/* unit-tenx 1 "{fn}" 1 */\n' +
            '\n'.join(files[i])
        )

        instrumented_code = '\n\n'.join(files)

    return instrumented_code


def instrument_c(project_yaml, filename, function, config, target_function):
    '''
        Test routine for get_symbolic_test.

        :param project_yaml: yaml project containing maps of files to functions.
        :param filename: filename to be scanned.
        :param function: function name to be scanned.
        :param config: alternate configuration to disambiguate multiple matches to functions.
        :param target_function: do not change name of target_function.

        :returns: db with project_yaml and instrumented db.
    '''

    db = find_configuration(
        project_yaml=project_yaml,
        filename=filename,
        function=function,
        config=config
    )

    print()
    print(f'DB for instrumented code of {filename}:{function}')
    for i, item in enumerate(db["instrumented"]):
        print(i, item['name'], ':', ' '.join(item['functions']))

    instrumented_code = generate_code(
        project_yaml=project_yaml,
        instruction_list=db['instrumented'],
        target_function=target_function
    )

    return instrumented_code, db


def get_global_variables(project_yaml):
    '''
        Extracts maps of all global environment for project.

        :param project_yaml:
        :return: map from visible global variables to files.
    '''
    _globals = {}
    for f in project_yaml['files']:
        if not project_yaml['files'][f]: continue
        for g in project_yaml['files'][f]['__globals']:
            if g not in _globals:
                _globals[g] = [f]
            else:
                _globals[g].append(f)

    return _globals


def add_to_file(project_yaml, filename, global_filenames, functions_list=[], target_function=''):
    '''
        Prefixes global variables from global_filenames to filename.

        :param project_yaml: project yaml.
        :param filename: filename to be prefixed.
        :param global_filenames: filenames to extract global variables
            or final missing functions.
        :param functions_list: optional functions list.
        :param target_function: do not change this function.

        :return: None
    '''

    code = []
    for gfn in global_filenames:
        code.append(generate_code(
            project_yaml=project_yaml,
            instruction_list=[{'name': gfn, 'functions': functions_list}],
            target_function=target_function
        ))

        code = '\n\n'.join(code) + '\n\n'

        source = code + open(filename, 'r').read()

        with open(filename, 'w') as fp:
            fp.write(source)


def parse_args(arg_list: list[str] | None):
    '''
        Argument parser..

        :param arg_list: list of arguments to facilitate testing.
    '''

    parser = ArgumentParser()

    parser.add_argument('--work', default='work')
    parser.add_argument('project', nargs='+')
    parser.add_argument('--filename', type=str, default='*')
    parser.add_argument('--function', type=str, default='*')
    parser.add_argument('--cflags', default='')
    parser.add_argument('-D', default=[], action='append')
    parser.add_argument('-I', default=[], action='append')
    parser.add_argument('-d', '--debug', type=int, default=0)
    parser.add_argument('--depth', default=0, type=int)
    parser.add_argument('--config', default='config')
    parser.add_argument('--use-cache', default=False, action='store_true')
    parser.add_argument('--stop-on-error', default=False, action='store_true')
    parser.add_argument('--with-ssh', default=False, action='store_true')

    args = parser.parse_args(arg_list)

    if args.cflags and args.cflags[0] in ['"', "'"]:
        args.cflags = args.cflags[1:-1]

    return args


def find_c_files(start_directory):
    '''
        Finds recursively all c-files starting from start_directory.

        :param start_directory: staring directory to search.

        :return: list of relative paths to start_directory.
    '''

    start_directory = os.path.abspath(start_directory)
    sd_len = len(start_directory.split('/'))
    c_files = []
    for root, _, _ in os.walk(start_directory):
        for file in glob.glob(os.path.join(root, '*.c')):
            file = '/'.join(file.split('/')[sd_len-1:])
            c_files.append(file)

    return c_files


def create_work(args):
    '''
        Create all information inside work directory..

        :param args: parameter list from argparse.
    '''

    os.makedirs(os.path.join(args.work, 'mockups'), exist_ok=True)
    os.makedirs(os.path.join(args.work, 'info'), exist_ok=True)
    os.makedirs(os.path.join(args.work, 'logs'), exist_ok=True)

    if not os.path.isfile(os.path.join(args.work, 'Makefile')):
        shutil.copyfile(
            os.path.join(args.work, 'makefile.header'),
            os.path.join(args.work, 'Makefile'))

        with open(os.path.join(args.work, 'Makefile'), 'a') as fp:
            fp.write(f'DEPTH = {args.depth}\n')
            fp.write(f'WORK = {args.work}\n\n')

    with open(os.path.join(args.work, 'i_main.c'), 'w') as fp:
        fp.write(
            'int main() { return 0; }\n'
        )

    try:
        project_yaml = scan_project(
            project_list=args.project,
            cflags=args.cflags,
            use_cache=True,
            save_to_cache=True,
            stop_on_error=args.stop_on_error
        )

        with open(os.path.join(args.work, 'db.yaml'), 'w') as fp:
            fp.write(yaml.dump(project_yaml))

    except:
        print('... Please fix errors')
        exit()

    if args.filename == '*':
        filenames = []
        for project in args.project:
            filenames.extend(find_c_files(project))
    else:
        if os.path.isfile(args.filename):
            filenames = [args.filename]
        else:
            filenames = []
            for p in args.project:
                p_filename = os.path.join(p, args.filename)
                if os.path.isfile(p_filename):
                    filenames.append(p_filename)

    config = {}
    functions = {}

    for fn in filenames:
        # check if config file is available because sometimes there are name clashes in directory.
        config_of_file = os.path.join(
            args.config,
            os.path.splitext(os.path.basename(fn))[0] + '.yaml'
        )
        if os.path.isfile(config_of_file):
            print(f'... found config file {config_of_file}')
            try:
                with open(config_of_file, 'r') as fp:
                    config[fn] = yaml.load(fp, Loader=Loader)
            except:
                print(f'... cannot open config file {args.config}')
                exit()
        else:
            config[fn] = {}

        if args.function == '*':
            functions[fn] = [name for name in project_yaml['files'][fn]
                         if not name.endswith('__globals')]
        else:
            functions[fn] = [args.function]

    # now we need to check for global variables
    _globals = get_global_variables(project_yaml)
    with open(os.path.join(args.work, 'globals.yaml'), 'w') as f:
        yaml.dump(_globals, f, default_flow_style=False)

    return project_yaml, filenames, config, functions, _globals


def update_project(project_yaml):
    '''
        Update project based on name changes.

        :param project_yaml: project database.
    '''

    for fn in project_yaml['files']:
        redirect_globals = project_yaml['files'][fn].get('redirect__globals', {})
        i = 0
        to_delete = []
        to_add = {}
        for key in project_yaml['files'][fn]:
            if key == 'redirect__globals': continue
            obj = project_yaml['files'][fn][key]
            if key.endswith('__globals'):
                for i in range(len(obj)):
                    if obj[i] in redirect_globals:
                        obj[i] = redirect_globals[obj[i]]
            else:
                for i in range(len(obj['globals'])):
                    if obj['globals'][i] in redirect_globals:
                        obj['globals'][i] = redirect_globals[obj['globals'][i]]
                for i in range(len(obj['functions'])):
                    if obj['functions'][i] in redirect_globals:
                        obj['functions'][i] = redirect_globals[obj['functions'][i]]
            if key in redirect_globals:
                new_name = redirect_globals[key]
                to_add[new_name] = project_yaml['files'][fn][key]
                to_delete.append(key)
        # let's keep both names for now, as mockup targets will use the original name
        #for k in to_delete:
        #    del project_yaml['files'][fn][k]
        for k in to_add:
            project_yaml['files'][fn][k] = to_add[k]


def main(arg_list: list[str] | None = None):
    '''
        Test routine for get_symbolic_test.

        :param arg_list: list of arguments to facilitate testing.
    '''

    script_path = os.path.dirname(os.path.abspath( __file__ ))

    args = parse_args(arg_list)

    args.work = os.path.abspath(args.work)

    CC = os.environ.get('CC', 'gcc-10')

    project_yaml, filenames, config, functions, _globals = create_work(args)

    Ds = ' '.join(['-D' + inc for inc in args.D])
    Is = ' '.join(['-I' + os.path.abspath(inc) for inc in args.I])
    args.cflags = (args.cflags + ' ' + Ds + ' ' + Is).strip()

    for fn in filenames:
        # get relative name w.r.t. project directory
        filename = os.path.basename(fn)
        prefix, suffix = os.path.splitext(fn)

        if len(args.project) == 1:
            offset = 1
        else:
            offset = 0
        prefix = '_'.join(prefix.split('/')[offset:])

        print()
        print(f'... processing file {filename}')

        for function in functions[fn]:
            print()
            print(f'... processing function {function} in {filename}')

            target_function = '__' + prefix + '_' + function
            target_function = re.sub(r'[^a-zA-Z0-9]', '_', target_function)

            target_prefix = 'i_' + prefix + '_' + function
            basename = ''.join([target_prefix, suffix])
            info = target_prefix + '.info'

            try:
                code, db = instrument_c(
                    project_yaml=project_yaml,
                    filename=fn,
                    function=function,
                    config=config[fn],
                    target_function=target_function
                )
            except Exception as e:
                print(e)
                continue

            with open(os.path.join(args.work, 'info', info), 'w') as fp:
                fp.write(yaml.dump(db['instrumented']))

            has_main = False
            for i in range(len(db['instrumented'])):
                entry = db['instrumented'][i]
                if 'main' in entry['functions']:
                    has_main = True

            final_code_filename = os.path.join(args.work, 'mockups', basename)
            with open(final_code_filename, 'w') as fp:
                fp.write(code)

            # try to fix all errors
            # this needs to be refactored
            while True:
                if not has_main:
                    cmd = (
                        CC + f' -o {args.work}/main ' +
                        args.cflags + f' -include {final_code_filename} ' +
                        ' ' + f' {args.work}/i_main.c '
                    )
                else:
                    cmd = (
                        CC + f' -o {args.work}/main ' +
                        args.cflags + ' ' + final_code_filename
                    )

                data = subprocess.run(cmd, capture_output=True, shell=True, text=True)

                if 'error' not in data.stderr:
                    break

                error_str = 'undefined reference to '
                le = data.stderr.find(error_str)
                name = data.stderr[le + len(error_str):]
                name = name.strip()[1:]
                if le == -1:
                    # check for conflicting types
                    error_str = 'conflicting types for '
                    le = data.stderr.find(error_str)
                    if le != -1:
                        name = data.stderr[le + len(error_str):]
                        name = name.strip()[1:]
                        ri = name.find("\n")
                        print(name[:ri-1], 'conflicting');
                        print(data.stderr)
                        exit()

                    print()
                    print(f'... could not find error in {basename}')
                    print(data.stderr)
                    break
                ri = name.find("\n")
                name = name[:ri-1]

                # check if this is a function
                if project_yaml['functions'].get(name, None):
                    try:
                        files_to_add = project_yaml['functions'][name]
                        if len(files_to_add) > 1:
                            if config[fn].get(name, None):
                                files_to_add = config[name]
                            else:
                                files_to_add = None
                        else:
                            files_to_add = files_to_add[0]
                    except:
                        import pdb; pdb.set_trace()

                    if files_to_add:
                        print(f'... need to add file(s) {files_to_add} because of {name}')

                        add_to_file(
                            project_yaml=project_yaml,
                            filename=final_code_filename,
                            global_filenames=[files_to_add],
                            functions_list=[name],
                            target_function=target_function)
                    else:
                        # one last check if name exists in functions
                        print(f'... could not find {name} in global context')
                        print(data.stderr)
                        break
                elif name in _globals:
                    files_to_add = ' '.join(_globals[name])

                    print(f'... need to add file(s) {files_to_add} because of {name}')

                    add_to_file(
                        project_yaml=project_yaml,
                        filename=final_code_filename,
                        global_filenames=_globals[name],
                        target_function=target_function)
                else:
                    # one last check if name exists in functions
                    print(f'... could not find {name} in global context')
                    print(cmd)
                    print(data.stderr)
                    break

            source = open(final_code_filename, 'r').read()
            pattern = r"\b" + re.escape('static') + r"\b"
            source = re.sub(pattern, '', source)

            print(cmd)

            with open(final_code_filename, 'w') as f:
                f.write(source)

            with open(os.path.join(args.work, 'Makefile'), 'a') as f:
                function_name = function if function != 'main' else target_function
                cmd_list = [
                    # f'PYTHONPATH="$$PYTHONPATH:{script_path}"', - no need, added PYTHONPATH to .bashrc
                    'python',
                    f'{script_path}/agent.py',
                    os.path.join('$(WORK)', 'mockups', basename),
                    '--work=' + os.path.abspath(os.path.join(args.work, 'test', f'test_{target_prefix}')),
                    '--project=' + os.path.abspath(args.work),
                    f"--cflags='{args.cflags}'",
                    '--depth=$(DEPTH)',
                    '--type=function',
                    f'--target={function_name}',
                    '--model_name=$(MODEL_NAME)',
                    '--max_number_of_iterations=$(MAX_RETRIES)',
                    # f'2>&1 | tee logs/test_{target_prefix}.log'
                ]
                if args.with_ssh:
                    cmd_list.append(f'--ssh=$(USER)@$(IP)')
                cmd = ' '.join(cmd_list)
                print(cmd)
                f.write(f'{target_prefix}:\n')
                f.write(f'\t{cmd}\n')
                f.write('\n')

    # update db.yaml with new names (static names are replaced and 'static' removed for variables).
    update_project(project_yaml)

    # save database to test directory
    with open(os.path.join(args.work, 'db.yaml'), 'w') as fp:
        fp.write(yaml.dump(project_yaml))

    try:
        os.remove(f'{args.work}/main')
    except:
        pass

    try:
        os.remove(f'{args.work}/i_main.c')
    except:
        pass


if __name__ == '__main__':
    main()
