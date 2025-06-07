# Copyright 2025 Claudionor N. Coelho Jr

import os.path
import sys

sys.path.append("..")

from utils.state import AgentState

def test_agent_state():
    state = AgentState(
        number_of_iterations=2,
        target_type="test",
        language="python",
        test_language="python",
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
        work="",
        missing_coverage="",
        coverage_output="",
        symbolic_sensitization="",
        messages=[]
    )

    assert state.get("test", "") == "no test"
    assert state.get("source_files", ["no"]) == ["no"]

