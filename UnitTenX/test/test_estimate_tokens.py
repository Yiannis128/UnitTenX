# Copyright 2025 Claudionor N. Coelho Jr

import os
import sys

sys.path.append("..")

from utils.estimate_tokens import num_tokens_from_string


def test_estimate_number_of_tokens():
    n = num_tokens_from_string('hello world')
    assert n == 2


