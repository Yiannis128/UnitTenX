/* Copyright 2025 Claudionor N. Coelho Jr */

#include <iostream>

using namespace std;

long int SEED = 19823749287;

int fact_pong(int n);

int fact_ping(int n) {
    if (n <= 1) return 1;
    else if ((SEED % 2) != 0 && (SEED % 2) != 1)
        return n * fact_pong(n-1);
    else
        return n * fact_ping(n-1);
}

int fact_pong(int n) {
    if (n <= 1) 
        return 1;
    else
        return n * fact_ping(n-1);
}

int factorial(int n) {
    return fact_ping(n);
}

void run() {
    int n;
    cin >> n;
    cout << factorial(n) << endl;
}
