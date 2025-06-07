# Copyright 2025 Claudionor N. Coelho Jr

import os.path
import sys

sys.path.append("..")

from utils.prompts import *

def test_prompts_symbolic_test_prompt():
    symbolic_test_prompt.format(
        target_type="function",
        name="main",
        language="C++",
        test_language="C++",
        test_interface="plain",
        source_code="no source code",
        test_cases="no test cases"
    )

def test_prompts_unit_test_prompt():
    unit_test_prompt.format(
        target_type="function",
        name="main",
        language="C++",
        test_language="C++",
        test_interface="plain",
        source_code="no source code",
        missing_coverage="no missing coverage",
        coverage_output="",
        additional_requirements="no additional requirements",
        with_messages="not with messages",
        unit_test="no current unit test",
        function_names="- main\n- function1\n",
        review="no reviews",
        test_cases=""
    )


def test_reflection_prompt():
    reflection_prompt.format(
        target_type="function",
        name="main",
        source_code="no source code",
        test_language="C++",
        coverage_output="no coverage output",
        function_names="- main\n- function1\n",
        unit_test="no unit tests",
        reviews="no reviews"
    )
