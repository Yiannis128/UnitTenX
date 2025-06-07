/* Copyright 2025 Claudionor N. Coelho Jr */

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
    int n1 = n-1;
    {
	int n2 = n1;
        return fact_ping(n2);
    }
}

