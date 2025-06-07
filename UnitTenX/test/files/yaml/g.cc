// Copyright 2025 Claudionor N. Coelho Jr

#include "main.h"

void Y() { D(); }
void X() { Y(); }
void S() { D(); }
void P() { S(); }
void O() { P(); }
void N() { O(); }
void M() { N(); }
void G() { M(); }

