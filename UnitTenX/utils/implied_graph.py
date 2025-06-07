# Copyright 2025 Claudionor N. Coelho Jr

import code2flow # placeholder to make sure we installed.
import argparse
import json
import networkx as nx
import os
import subprocess
import tempfile
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

try:
    from .interfaces import *
except:
    from interfaces import *

try:
    from .utils import fix_relative_paths, fatal_error
except:
    from utils import fix_relative_paths, fatal_error

NEG_FILTERS = [
        "std::", "boost::", "gxx", "llvm", "_GLOBAL__", "__cxx_", 
        "operator delete", "operator new", "malloc", "calloc", "free", 
        "printf", "__iso"]
POS_FILTERS = ["::operator delete", "::operator new"]

def discard(sentence):
    '''
        Checks if node names for callgraph should be kept or not.

        :param sentence: sentence to be checked.

        :return: True (discard node) or False (do not discard node).
    '''

    for word in POS_FILTERS:
        if word in sentence:
            return False
    for word in NEG_FILTERS:
        if word in sentence:
            return True
    return False

def process_lines(lines, function):
    '''
        Processes compilation structure of file from clang + opt.

        :param lines: text description of call graph from opt.
        :param function: function to be tested.

        :return: graph (node -> node) and target list from function

        Node that function because of overloading can generate 
        several targets, for example:

        Cat::Meow can be matched with Cat::Meow(int), Cat::Meow(float), 
        etc.
    '''
    targets = []
    graph = {}
    i = 0
    while i < len(lines):
        s = lines[i]
        if not s or "null function" in s:
            i += 1
            continue
        if s[0] == 'C':
            u = s.split("'")[1]
            if discard(u):
                i += 1
                while i < len(lines) and len(lines[i]) > 0 and lines[0] == ' ': 
                    i += 1
                continue
            if function in u:
                targets.append(u)
            graph[u] = []
        else:
            # if it is tagged as an external node, we should disregard 'u'
            #if 'calls external node' in s:
            #    if u in graph:
            #        del graph[u]
            #    i += 1
            #   continue
            try:
                v = s.split("'")[1]
                if discard(v): 
                    i += 1
                    continue
                graph[u].append(v)
            except:
                pass
        i += 1

    return graph, targets

def get_implied_graph_python(project, files, function="main", depth=2):
    '''
        Process a list of files in python and returns 
        function names at a given 'depth' from 'function', 
        and the file names that needs to be parsed.

        :param project: project directory.
        :param files: list of all files to be scanned.
        :param function: function to be tested.
        :param depth: depth of transitive callgraph search.

        :return: map containing function name -> file, where
            file is the file where function name is defined.
    '''

    with tempfile.NamedTemporaryFile(
            delete_on_close=False, suffix=".json") as fp:
        fp.close()
        tmp_filename = fp.name

    cmd_list = [
           f"code2flow {' '.join(files)}",
           f"--target-function {function}",
           "--upstream-depth=0",
           f"--downstream-depth={depth}", 
           f"--output {tmp_filename}",
           "--quiet"
        ]

    cmd = ' '.join(cmd_list)

    data = subprocess.run(cmd, capture_output=True, shell=True, text=True)

    if data.stderr:
        # has error: just return everything
        return { }

    graph = json.load(open(tmp_filename,"r"))
    os.remove(tmp_filename) 

    nodes = graph["graph"]["nodes"]

    target_function_names = []
    target_files = {}
    for n in nodes:
        file_function = nodes[n]["name"].split("::")
        basename = file_function[0]
        function = '::'.join(file_function[1:])

        for file in files:
            if basename in file:
                basename = file
                break

        target_files[function] = basename

    return target_files

class Traverser:
    def __init__(self, target_file, yaml_config):
        self.target_functions = {}
        self.target_file = target_file
        self.yaml_config = yaml_config

    def __traverse(self, target, depth):
        '''
            Traverses the call graph recursively to add attention to the functions
            within the depth.

            :param target: function name.
            :param depth: if depth <= 0, do not recursively traverse.
        '''
        self.target_functions[target] = depth

        if depth <= 0:
            return

        files_dict = self.yaml_config['files'][self.target_file]
        for name in files_dict[target]['functions']:
            if name not in self.yaml_config['functions']: continue

            if (
                    name not in self.target_functions or
                    self.target_functions[target] < depth
            ):
                self.__traverse(name, depth - 1)

    def traverse(self, target, depth):
        '''
            Call __traverse recursively and return the function names in the call
            graph.

            :param target: function name.
            :param depth: target depth for the traversal

            :return: set of function names.
        '''
        self.__traverse(target, depth)
        return set(list(self.target_functions.keys()))


def get_implied_graph_cc(project, files, function="main", depth=2, cflags=""):
    '''
        Process a list of files and returns function names
        at a given 'depth' from 'function', and the file
        names that needs to be parsed.

        :param project: project directory.
        :param files: list of all files to be scanned.
        :param function: function to be tested.
        :param depth: depth of transitive callgraph search.
        :param cflags: arguments to be passed to the compiler.

        :return: map containing function name -> file, where
            file is the file where function name is defined.
    '''
    g_dict = {}
    files_map = {}

    # if db.yaml is in work directory, our life is easier
    # we may need to refactor this code for C code later on
    # as pycparser is much easier to extract from the db.
    # we only accept if |files| == 1, which is the case for
    # auto-mockup.
    if os.path.isfile(os.path.join(project, 'db.yaml')) and len(files) == 1:
        path = '/'.join(__file__.split('/')[:-2])
        args = [
            'python',
            path + '/scan_c_project.py',
            f"--cflags='{cflags}'",
            '--dont-save-to-cache',
            '<to-be-filled-in-the-loop>'
        ]
        target_files = {}
        targets = {}
        for file in files:
            args[-1] = file
            cmd = ' '.join(args)
            data = subprocess.run(cmd, capture_output=True, shell=True, text=True)
            le = data.stdout.find('files:')
            if le > 0:
                yaml_text = data.stdout[le:]
                yaml_config = yaml.safe_load(yaml_text)

                try:
                    target_fn = yaml_config['functions'][function][0]
                except:
                    # print(function)
                    fatal_error(function)
                    # import pdb; pdb.set_trace()

                target_set = Traverser(
                    target_file=target_fn,
                    yaml_config=yaml_config,
                ).traverse(target=function, depth=depth)

                target_files.update({
                    n: yaml_config['functions'][n][0]
                    for n in yaml_config['functions']
                    if n in target_set
                })

        has_func = function in target_files
        if has_func:
            return target_files

    for filename in files:
        ext = os.path.splitext(filename)[1]
        if ext:
            ext = ext[1:].lower()
        if is_cxx(ext):
            cmd_list = [
                f"clang++ -S -emit-llvm {filename} {cflags} -c -o -",
                "opt --passes=print-callgraph -f -o /dev/null 2>&1",
                "c++filt"
            ]
        else:
            cmd_list = [
                f"clang -S -emit-llvm {filename} {cflags} -c -o -",
                "opt --passes=print-callgraph -f -o /dev/null 2>&1",
            ]
        cmd = ' | '.join(cmd_list)

        data = subprocess.run(cmd, capture_output=True, shell=True, text=True)

        if 'error' in data.stderr:
            print(cmd) 
            print(data.stderr)

            return { }

        lines = data.stdout.split('\n')
        file_dict, targets = process_lines(lines, function)

        files_map.update({node: filename for node in file_dict})

        # add file_dict entries to g_dict
        for u in file_dict:
            if u in g_dict:
                g_dict[u].extend(file_dict[u])
            else:
                g_dict[u] = file_dict[u]

    G = nx.DiGraph()
    for u in g_dict:
        G.add_node(u)
        for v in g_dict[u]:
            G.add_edge(u, v)

    # nx.draw(G, with_labels=True)
    # plt.show()

    targets = set(targets)

    target_functions = {}

    for u in targets:
        P = dict(nx.shortest_path_length(G, source=u))
        P = {k:v for k, v in P.items() if v <= depth}
        target_functions.update(P)

    target_function_names = list(target_functions.keys())

    target_files = { node: files_map[node] for node in target_function_names }

    print(target_files); exit()
    return target_files

def run(project, files, function="main", depth=2, cflags="", language="cc"):
    '''
        Process a list of files and returns function names
        at a given 'depth' from 'function', and the file
        names that needs to be parsed.

        :param project: project directory.
        :param files: list of all files to be scanned.
        :param function: function to be tested.
        :param depth: depth of transitive callgraph search.
        :param cflags: arguments to be passed to the compiler.
        :param language: 'python' or 'cc'.

        :return: list of functions that should be included in
        unit test and subset of file names that needs to be 
        parsed.
    '''
    if is_c_cxx(language):
        return get_implied_graph_cc(project, files, function, depth, cflags)
    elif is_python(language):
        return get_implied_graph_python(project, files, function, depth)
    else:
        raise ValueError(f'Invalid language {language}')

def parse_args(arg_list: list[str] | None):
    '''
        Argument parser..

        :param arg_list: list of arguments to facilitate testing.
    '''

    parser = argparse.ArgumentParser()
    parser.add_argument('files', default=[], action='append')
    parser.add_argument('-p', '--project', type=str, default='.')
    parser.add_argument('-f', '--function', type=str, default='main')
    parser.add_argument('-d', '--depth', type=int, default=2)
    parser.add_argument('--cflags', type=str, default='')
    parser.add_argument('-D', default=[], action='append')
    parser.add_argument('-I', default=[], action='append')
    parser.add_argument('-l', '--language', type=str, default='auto')

    args = parser.parse_args(arg_list)

    if args.cflags and args.cflags[0] in ['"', "'"]:
        args.cflags = args.cflags[1:-1]

    return args

def main(arg_list: list[str] | None = None):
    '''
        Just a proxy for test purpose.        

        :param arg_list: list of arguments for testing purpose..

        :return: list of functions that should be included in
        unit test and subset of file names that needs to be 
        parsed.
    '''

    args = parse_args(arg_list)
    args.I = fix_relative_paths(args.I)

    Ds = ' '.join(['-D' + inc for inc in args.D])
    Is = ' '.join(['-I' + inc for inc in args.I])
    args.cflags = (args.cflags + ' ' + Ds + ' ' + Is).strip()

    files = []
    for file in args.files:
        if file.endswith(".yaml"):
            with open(file, 'r') as fp:
                yaml_config = yaml.load(fp, Loader=Loader)
                files.extend(yaml_config['files'])
        else:
            files.append(file)

    if args.language == "auto":
        _, ext = os.path.splitext(files[0])

        args.language = ext[1:].lower()

    os.chdir(args.project)
    args.project = os.getcwd()
    current = os.getcwd()

    files = [os.path.abspath(f) for f in files]
    print(files)

    files = run(
        project=args.project,
        files=files,
        function=args.function,
        depth=args.depth,
        cflags=args.cflags,
        language=args.language)

    print("target function names:", [k for k in files])
    print("target files:", files)

    os.chdir(current)

    return files

if __name__ == '__main__':
    main()
