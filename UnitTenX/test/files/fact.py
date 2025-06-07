# Copyright 2025 Claudionor N. Coelho Jr

import fire
from ping_pong import fact_ping, fact_pong

def swap(u:int, v:int) -> (int, int):
    return v, u

def factorial(n:int) -> int:
    return fact_ping(n)

def main(n:int):
    print(factorial(n))

if __name__ == "__main__":
    fire.Fire(main)
