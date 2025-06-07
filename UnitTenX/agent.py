# Copyright 2025 Claudionor N. Coelho Jr

import argparse
from langgraph.graph import StateGraph, END
from langgraph.errors import GraphRecursionError
from langchain_core.runnables.graph import CurveStyle, MermaidDrawMethod, NodeStyles
from langgraph.checkpoint.memory import MemorySaver
import os
import textwrap
from typing import List, Tuple
from utils.utils import fix_relative_paths
from utils.nodes import *
from utils.state import *
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


def parse_args(arg_list: list[str] | None):
    '''
        Reads parameters passed to invokation.


        :return: map containing values for all parameters read.

    '''

    print('Set UNITTENX_TIMEOUT=<time-in-sec> to set maximum timeout for test execution.')
    print('Set ESBMC_UNWIND=<value> to set maximum unrolling parameter.')
    print('Set ESBMC_TIMEOUT=<time>[s|m|h] to set maximum timeout parameter.')
    print('Set ESBMC_FLAGS="<flags>" to set additional flags to esbmc.')
    print('Set AGENT_REMOTE_VERSION=<version-number> if --ssh is used to')
    print('    use the right remote toolset.')

    model_name = os.getenv('MODEL_NAME', 'openai')

    parser = argparse.ArgumentParser()

    parser.add_argument('filename')
    parser.add_argument('-p', '--project', default='.')
    parser.add_argument('-w', '--work', default='.')
    parser.add_argument('--cflags', default='')
    parser.add_argument('--ldflags', default='')
    parser.add_argument('-D', default=[], action='append')
    parser.add_argument('-I', default=[], action='append')
    parser.add_argument('-d', '--depth', type=int, default=2)
    parser.add_argument('-l', '--language', default='auto')
    parser.add_argument('--type', choices=["function", "class"], default="function")
    parser.add_argument('-t', '--target', default='main')
    parser.add_argument('-m', '--model_name', default=model_name)
    parser.add_argument('--with_messages', default=False, action="store_true")
    parser.add_argument('--ssh', default="")
    parser.add_argument('--draw', default="")
    parser.add_argument('--max_number_of_iterations', default=3, type=int)

    args = parser.parse_args(arg_list)

    args.I = fix_relative_paths(args.I)

    args.cflags = (
        args.cflags + 
        ' '.join(['-D' + inc for inc in args.D]) +
        ' '.join(['-I' + inc for inc in args.I])
    )

    # let's make sure the include files are there
    cflags_list = args.cflags.split(' ')
    for c in cflags_list:
        c = c.strip()
        if c[:2] == '-I' and c[2:] not in args.I:
            args.I.append(c[2:])

    return args

def run(
        sources: List[str],
        project: str = ".",
        work: str = "",
        cflags: str = "",
        ldflags: str = "",
        includes: List[str] = [],
        depth:int = 2,
        max_number_of_iterations=3,
        language: str = "auto",
        target_type: str="function",
        target_name: str="main", 
        model_name="openai",
        with_messages=False,
        ssh="",
        draw=""):

    '''
        Runs the langgraph agent for unit test generation.

        :param sources: source file names comma separate or yaml file.
        :param project: project directory.
        :param work: testcase generation directory. If none, use project.
        :param cflags: arguments to be passed to the compiler.
        :param ldflags: arguments to be passed to the linker.
        :param includes: list of all paths to be included.
        :param depth: depth of search for unit test generation.
        :param max_number_of_iterations: max number of attempts to generate test.
        :param language: language to generate and analyze tests.
        :param target_type: function or class (type of target).
        :param target_name: name of target.
        :param model_name: model name (openai or anthropic).
        :param with_messages: make sure we capture messages.
        :param ssh: remote connection to machine for coverage extraction.
        :param draw: just draw the graph and quits.

        :return: initial state dictionary.
    '''

    if target_type not in ["class", "function"]:
        raise ValueError(f"target_type must be one of 'class' or 'function'")

    all_sources = []
    for source in sources:
        if source.endswith(".yaml"):
            with open(source, 'r') as fp:
                yaml_config = yaml.load(fp, Loader=Loader)
                all_sources.extend(yaml_config['files'])
        else:
            all_sources.append(source)

    sources = fix_relative_paths(all_sources)

    os.chdir(project)
    project = os.getcwd()

    if not work:
        work = project
    else:
        if not os.path.exists(work):
            os.makedirs(work)
        # if we will run it remotely, we need to give permission for everyone.
        if ssh:
            os.chmod(work, 0o777)

    # Define a new graph
    workflow = StateGraph(AgentState)

    # Define the two nodes we will cycle between
    # implied_functions -> symbolic -> (unit-test -> coverage -> reflection)*
    workflow.add_node("implied_functions", implied_functions)
    workflow.add_node("symbolic", symbolic)
    workflow.add_node("unit_test", unit_test)
    workflow.add_node("coverage", coverage)
    workflow.add_node("reflection", reflection)

    # Set the entrypoint as `agent`
    # This means that this node is the first one called
    workflow.set_entry_point("implied_functions")

    # We now add a conditional edge
    workflow.add_conditional_edges(
        "reflection",
        should_continue,
        {
            "continue": "unit_test",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "symbolic",
        has_symbolic_test,
        {
            "continue": "coverage",
            "skip": "unit_test"
        }
    )

    workflow.add_edge("implied_functions", "symbolic")
    workflow.add_edge("unit_test", "coverage")
    workflow.add_edge("coverage", "reflection")

    checkpointer = MemorySaver()

    graph = workflow.compile(checkpointer=checkpointer)

    if draw:
        with open(draw, "wb") as fp:
            fp.write(graph.get_graph().draw_png())
            exit()


    config = { "configurable": {"thread_id": "1", "model_name": model_name, "recursion_limit": 100} }

    state =  {
        "number_of_iterations": 1,
        "max_number_of_iterations": max_number_of_iterations,
        "depth": depth,
        "source_files": sources,
        "language": language,
        "cflags": cflags,
        "ldflags": ldflags,
        "includes": includes,
        "target_type": target_type,
        "name": target_name,
        "test": "",
        "project": project,
        "work": work,
        "missing_coverage": "",
        "coverage_output": "",
        "review": [],
        "with_messages": with_messages,
        "ssh": ssh

    }

    try:
        final_state = graph.invoke(state, config)
    except GraphRecursionError:
        try:
            final_state = [
                h for h in graph.get_state_history(config)
                if h.next == ('reflection',)
            ][-1].values
        except:
            print(f'... could not find a usable reflection in {name}')
            exit(1)

    extension = final_state["language"]
    if extension == "python":
        extension = "py"

    #with open(f'{work}/test_{target_name}.{extension}', 'w') as fp:
    #    fp.write(final_state["test"])

    if not os.path.isdir(f'{work}/logs'):
        os.makedirs(f'{work}/logs')

    with open(f'{work}/logs/test_{target_name}.reviews', 'w') as fp:
        for review in final_state["review"]:
            fp.write("{\n")
            fp.write("    review:\n")
            for s in review['review']:
                for sub_s in textwrap.wrap(s):
                    fp.write(f"        {sub_s}\n")
                fp.write("\n")
            fp.write(f"    summary:\n")
            for s in textwrap.wrap(review['summary']):
                fp.write(f"        {s}\n\n")
            fp.write(f"    rating: {review['rating']}\n")
            fp.write("}\n\n")

    messages = final_state['messages']
    for i in range(0, len(messages), 2):
        with open(f'{work}/logs/test_{target_name}.p{i // 2}', 'w') as fp:
            fp.write(messages[i].content)


def main(arg_list: list[str] | None=None):
    args = parse_args(arg_list)

    run(
        sources=[args.filename],
        project=args.project,
        work=args.work,
        cflags=args.cflags,
        ldflags=args.ldflags,
        includes=args.I,
        depth=args.depth,
        max_number_of_iterations=args.max_number_of_iterations,
        language=args.language,
        target_type=args.type,
        target_name=args.target,
        model_name=args.model_name,
        with_messages=args.with_messages,
        ssh=args.ssh,
        draw=args.draw,
    )


if __name__ == '__main__':
    main()
