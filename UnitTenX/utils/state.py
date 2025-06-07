# Copyright 2025 Claudionor N. Coelho Jr

from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage
from typing import TypedDict, Annotated, Sequence, List, Dict

# Pydantic agent state to be used by the agent

class AgentState(TypedDict):
    # number of reflection iterations
    number_of_iterations: int

    # max number of iterations
    max_number_of_iterations: int

    # target_type for the unit test generation (test function or class)
    target_type: str

    # programming language to use
    language: str

    # test language to use
    test_language: str

    # which test interface to use
    test_interface: str

    # if true, we care about messages
    with_messages: bool

    # name of the function/class name to be tested
    name: str

    # list of source files
    source_files: List[str]

    # list of function names to guide LLM 
    function_names: Dict[str, str]

    # bundled source code of all files in the transitive
    # closure of the function (to a given depth)
    source_code: str

    # test generation in GoogleTest or pytest format
    test: str

    # depth of search
    depth: int

    # arguments to be passed to the compiler
    cflags: str
    ldflags: str
    includes: List[str]

    # ssh configuration
    ssh: str

    # reflection reviews of LLM
    review: List[str]

    # project source directory
    project: str

    # project target directory
    work: str

    # missing coverage metrics
    missing_coverage: str
    coverage_output: str

    # symbolic sensitization condition
    symbolic_sensitization: str

    # full history of messages
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # symbolic test cases
    symbolic_test_cases: str

    # external interface to assist LLM
    extern_interface: Dict[str, str | List[str]]

    # list of lines in C-declaration
    declaration_lines: List[int]
