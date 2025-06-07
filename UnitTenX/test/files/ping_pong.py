# Copyright 2025 Claudionor N. Coelho Jr

SEED = 19823749287489273498723

def fact_ping(n:int) -> int:
    if n <= 1:
        return 1
    # LLMs cannot solve complex conditionals
    elif (SEED % 2) not in [0, 1]:
        return n * fact_pong(n-1)
    else:
        return n * fact_ping(n-1)

def fact_pong(n:int) -> int:
    if n <= 1:
        return 1
    else:
        return n * fact_ping(n-1)

