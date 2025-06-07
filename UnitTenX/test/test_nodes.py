# Copyright 2025 Claudionor N. Coelho Jr

import sys

sys.path.append("..")

from utils.nodes import *
from utils.nodes import _get_model
from utils.state import AgentState

from copy import deepcopy
import os
import pytest
import pytest_timeout # place holder to make sure pactest_unit_test_c_meowckage is installed


MODEL_NAME = os.environ.get("MODEL_NAME", "openai")
WORK = os.path.abspath("work")

class StateStorage:
    def __init__(self):
        self.storage = {}

    def add(self, name: str, stage: str, state: AgentState) -> None:
        if not name in self.storage:
            self.storage[name] = []
        self.storage[name].append(
            { "stage": stage, "state": state}
        )

    def get(self, name: str, index: int=-1) -> AgentState:
        return deepcopy(self.storage[name][index]["state"])


master_storage = StateStorage()


def count_number_of_tests(test: str, language="c++") -> int:

    if language == "c++":
        return test.count('test_') // 2
    else:
        return test.count('def test_')

def get_state():
    state = AgentState(
        number_of_iterations=2,
        max_number_of_iterations=3,
        target_type="test",
        language="python",
        test_interface="plain",
        with_messages=True,
        name="run",
        function_names={},
        source_code="",
        test="no test",
        depth=2,
        cflags="",
        ldflags="",
        includes=[],
        ssh="",
        review=[],
        project=".",
        work=WORK,
        missing_coverage="",
        coverage_output="",
        symbolic_sensitization="",
        messages=[]
    )

    return state

def test_extract_core():
    text = "hello"
    assert text == extract_core(text, is_json=False)

    text = "'''\nhello"
    assert text == extract_core(text, is_json=False)

    text = "'''json\n{hello}'''"
    assert "{hello}" == extract_core(text, is_json=True)


def test_get_model():
    # "azure" fails
    try:
        _get_model("azure")
        assert False
    except:
        pass
    assert _get_model("anthropic")
    assert _get_model("ollama:mistral-nemo")
    assert _get_model("mistral-nemo")


def test_should_continue():
    state = AgentState()

    state["number_of_iterations"] = 3
    state["max_number_of_iterations"] = 2
    state["coverage_output"] = "NO ERRORS"

    assert should_continue(state) == "end"

    state["coverage_output"] = "blah blah blah FIX THIS ERROR blah blah blah"

    assert should_continue(state) == "continue"

    state["number_of_iterations"] = 2
    state["coverage_output"] = "NO ERRORS"

    assert should_continue(state) == "continue"

def test_has_symbolic_test():
    state = AgentState()

    state["test"] = "blah blah blah"

    assert has_symbolic_test(state) == "continue"

    state["test"] = ""

    assert has_symbolic_test(state) == "skip"

def test_get_language_interface():
    language = "auto"
    source_files = ["a.cc", "b.cxx"]
    language, framework = get_language_interface(language, source_files=source_files)

    assert is_cxx(language)
    assert "C++" in framework

    language = "auto"
    source_files = ["a.py", "b.py"]
    language, framework = get_language_interface(language, source_files=source_files)

    assert is_python(language)
    assert "pytest" in framework

    language = "python"
    source_files = ["a.py", "b.py"]
    try:
        get_language_interface(language, source_files=source_files)
        assert False
    except:
        pass

def test_implied_functions_c():
    state = AgentState()

    state["depth"] = 2
    state["max_number_of_iterations"] = 3
    state["cflags"] = "-Ifiles/include"
    state["name"] = "run"
    state["project"] = "."
    state["source_files"] = ["files/meow.c"]
    state["includes"] = ["files/include"]
    state["language"] = "auto"
    state["work"] = WORK

    new_state = implied_functions(state=state, config={})

    assert len(new_state["source_files"]) == 1
    assert new_state["language"] == "c"
    assert "C++" in new_state["test_interface"]
    assert len(new_state["function_names"]) == 6
    assert "Cat_Cat" in new_state["function_names"]
    assert "Cat_Destruct" in new_state["function_names"]
    assert "Cat_GetAge" in new_state["function_names"]
    assert "Cat_Meow" in new_state["function_names"]
    assert "Cat_SetAge" in new_state["function_names"]
    assert "run" in new_state["function_names"]

def test_implied_functions_c_invalid_name():
    state = AgentState()

    state["depth"] = 2
    state["max_number_of_iterations"] = 3
    state["cflags"] = "-Ifiles/include"
    state["name"] = "main"
    state["project"] = "."
    state["source_files"] = ["files/meow.c"]
    state["includes"] = ["files/include"]
    state["language"] = "auto"
    state["work"] = WORK

    try:
        implied_functions(state=state, config={})
        assert False
    except:
        pass

def test_implied_functions_py():
    state = AgentState()

    state["depth"] = 2
    state["max_number_of_iterations"] = 3
    state["name"] = "main"
    state["project"] = "files"
    state["source_files"] = ["files/fact.py", "files/ping_pong.py"]
    state["language"] = "python"
    state["work"] = WORK

    new_state = implied_functions(state=state, config={})

    assert len(new_state["source_files"]) == 2
    assert new_state["language"] == "python"
    assert new_state["test_interface"] == "pytest"
    assert len(new_state["function_names"]) == 3
    assert "fact_ping" in new_state["function_names"]
    assert "factorial" in new_state["function_names"]
    assert "main" in new_state["function_names"]

def test_implied_functions_py_error():
    state = AgentState()

    state["depth"] = 2
    state["max_number_of_iterations"] = 3
    state["name"] = "no_run"
    state["project"] = "files"
    state["source_files"] = ["files/fact.py", "files/ping_pong.py"]
    state["language"] = "python"
    state["work"] = WORK

    try:
        implied_functions(state=state, config={})
        assert False
    except:
        pass

def test_implied_functions_unknown_type():
    state = AgentState()

    state["depth"] = 2
    state["max_number_of_iterations"] = 3
    state["name"] = "main"
    state["project"] = "files"
    state["source_files"] = ["files/fact.sql"]
    state["language"] = "sql"
    state["work"] = WORK

    try:
        implied_functions(state=state, config={})
        assert False
    except:
        pass

def test_implied_functions_invalid_file():
    state = AgentState()

    currdir = os.getcwd()
    state["depth"] = 2
    state["max_number_of_iterations"] = 3
    state["name"] = "main"
    state["project"] = "files"
    state["source_files"] = [f"{currdir}/files/invalid.cc"]
    state["language"] = "auto"
    state["work"] = WORK

    try:
        implied_functions(state=state, config={})
        assert False
    except:
        pass

@pytest.mark.timeout(90)
def test_symbolic_c_fact():
    global master_storage

    state = AgentState()

    config = { "configurable": {"thread_id": "1", "model_name": MODEL_NAME} }

    currdir = os.getcwd()
    state["depth"] = 2
    state["max_number_of_iterations"] = 3
    state["name"] = "factorial"
    state["project"] = "."
    state["source_files"] = [f"{currdir}/files/fact.c"]
    state["language"] = "auto"
    state["target_type"] = "function"
    state["work"] = WORK

    state.update(implied_functions(state=state, config=config))

    state.update(symbolic(state=state, config=config))

    number_of_tests = sum([
        1 if l and l[0] == 'T' else 0
        for l in state['symbolic_test_cases'].split('\n')])

    actual_tests_count = count_number_of_tests(state['test'])

    assert actual_tests_count == number_of_tests

    master_storage.add("fact", "symbolic", state)

@pytest.mark.timeout(90)
def test_symbolic_c_meowc():
    global master_storage

    state = AgentState()

    config = { "configurable": {"thread_id": "1", "model_name": MODEL_NAME} }

    currdir = os.getcwd()
    state["depth"] = 2
    state["max_number_of_iterations"] = 3
    state["cflags"] = f"-I{currdir}/files/include"
    state["name"] = "run"
    state["project"] = "."
    state["source_files"] = [f"{currdir}/files/meow.c"]
    state["includes"] = [f"{currdir}/files/include"]
    state["language"] = "auto"
    state["target_type"] = "function"
    state["work"] = WORK

    state.update(implied_functions(state=state, config=config))

    state.update(symbolic(state=state, config=config))

    number_of_tests = sum([
        1 if l and l[0] == 'T' else 0
        for l in state['symbolic_test_cases'].split('\n')])

    actual_tests_count = count_number_of_tests(state['test'])

    assert actual_tests_count == number_of_tests

    master_storage.add("meowc", "symbolic", state)

@pytest.mark.timeout(90)
def test_symbolic_py_fact():
    global master_storage

    state = AgentState()

    config = { "configurable": {"thread_id": "1", "model_name": MODEL_NAME} }

    state["depth"] = 2
    state["max_number_of_iterations"] = 3
    state["name"] = "main"
    state["project"] = os.getcwd() + '/files'
    state["source_files"] = ["files/fact.py", "files/ping_pong.py"]
    state["language"] = "auto"
    state["target_type"] = "function"
    state["work"] = WORK

    state.update(implied_functions(state=state, config=config))

    state.update(symbolic(state=state, config=config))

    number_of_tests = sum([
        1 if l and l[0] == '-' else 0
        for l in state['symbolic_test_cases'].split('\n')])

    actual_tests_count = count_number_of_tests(state['test'])

    assert actual_tests_count == number_of_tests

    master_storage.add("fact_py", "symbolic", state)


@pytest.mark.timeout(120)
def test_unit_test_c_meowc():
    global master_storage

    state = master_storage.get('meowc')

    state["number_of_iterations"] = 1
    state["review"] = []
    state["missing_coverage"] = ""
    state["coverage_output"] = ""
    state["messages"] = []
    state["with_messages"] = True

    config = { "configurable": {"thread_id": "1", "model_name": MODEL_NAME} }

    current_test = state['test'][:]

    current_tests_count = count_number_of_tests(state['test'])

    state.update(unit_test(state, config))

    new_tests_count = count_number_of_tests(state['test'])

    assert new_tests_count >= current_tests_count

    master_storage.add('meowc', 'unit-test', state)


@pytest.mark.timeout(120)
def test_unit_test_c_fact():
    global master_storage

    state = master_storage.get('fact')

    state["number_of_iterations"] = 1
    state["review"] = []
    state["missing_coverage"] = ""
    state["coverage_output"] = ""
    state["messages"] = []
    state["with_messages"] = False

    config = {"configurable": {"thread_id": "1", "model_name": MODEL_NAME}}

    current_tests_count = count_number_of_tests(state['test'])

    state.update(unit_test(state, config))

    new_tests_count = count_number_of_tests(state['test'])

    assert new_tests_count > current_tests_count

    master_storage.add('fact', 'unit-test', state)


@pytest.mark.timeout(120)
def test_unit_test_py_fact():
    global master_storage

    state = master_storage.get('fact_py')

    state["number_of_iterations"] = 1
    state["review"] = []
    state["missing_coverage"] = ""
    state["coverage_output"] = ""
    state["messages"] = []
    state["with_messages"] = False

    config = { "configurable": {"thread_id": "1", "model_name": MODEL_NAME} }

    current_tests_count = count_number_of_tests(state['test'], language="python")

    state.update(unit_test(state, config))

    new_tests_count = count_number_of_tests(state['test'], language="python")

    assert new_tests_count > current_tests_count

    master_storage.add('fact_py', 'unit-test', state)

@pytest.mark.timeout(120)
def test_coverage_c_meowc():
    global master_storage

    state = master_storage.get('meowc')

    config = { "configurable": {"thread_id": "1", "model_name": MODEL_NAME} }

    state.update(coverage(state, config))

    assert "69" not in state['missing_coverage']

    master_storage.add('meowc', 'coverage', state)

@pytest.mark.timeout(120)
def test_coverage_py_fact():
    global master_storage

    state = master_storage.get('fact_py')

    config = { "configurable": {"thread_id": "1", "model_name": MODEL_NAME} }

    state.update(coverage(state, config))

    assert (
        "ping_pong.py:fact_ping: could not reach lines: 8" in
        state["missing_coverage"]
    )

    # assert not state['missing_coverage']

    master_storage.add('fact_py', 'coverage', state)

@pytest.mark.timeout(120)
def test_reflection_c_meowc():
    global master_storage

    state = master_storage.get('meowc')

    config = { "configurable": {"thread_id": "1", "model_name": MODEL_NAME} }

    state.update(reflection(state, config))

    master_storage.add('meowc', 'reflection', state)

@pytest.mark.timeout(240)
def test_reflection_py_fact():
    global master_storage

    state = master_storage.get('fact_py')

    config = { "configurable": {"thread_id": "1", "model_name": MODEL_NAME} }

    state.update(reflection(state, config))
    state.update(unit_test(state, config))
    state.update(reflection(state, config))

    master_storage.add('fact_py', 'reflection', state)

#def main():
#    test_symbolic_c_meowc() 
#    test_unit_test_c_meowc() 
#    test_coverage_c_meowc()

#if __name__ == '__main__':
#    main()
