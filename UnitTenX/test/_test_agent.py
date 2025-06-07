# Copyright 2025 Claudionor N. Coelho Jr

import sys

sys.path.append("..")

from agent import *

def test_fact_py():
    arg_list = [
        "files/fact.c",
        "--work=../work_c",
        "--project=.",
        "--depth=2",
        "--type=function",
        "--target=factorial",
        "--model_name=openai"
    ]

    main(arg_list)
