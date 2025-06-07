// Copyright 2025 Claudionor N. Coelho Jr

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "meow.h"

// constructor of Cat
Cat* Cat_Cat(int initialAge) {
    Cat* self = (Cat*)malloc(sizeof(Cat));
    self->itsAge = initialAge;
    self->string = (char*)calloc(10, sizeof(char));
    return self;
}

// copy constructor for making a new copy of a Cat
Cat* Cat_Cat_copy(const Cat* copy_from) {
    Cat* self = (Cat*)malloc(sizeof(Cat));
    self->itsAge = copy_from->itsAge;
    self->string = (char*)calloc(10, sizeof(char));
    memcpy(self->string, copy_from->string, 10);
    return self;
}

// copy assignment for assigning a value from one Cat to another
Cat* Cat_operator_assign(Cat* self, const Cat* copy_from) {
    self->itsAge = copy_from->itsAge;
    memcpy(self->string, copy_from->string, 10);
    return self;
}

// destructor, just an example
void Cat_Destruct(Cat* self) {
    free(self->string);
    free(self);
}

// GetAge, Public accessor function
// returns value of itsAge member
int Cat_GetAge(const Cat* self) {
    return self->itsAge;
}

// Definition of SetAge, public
// accessor function
void Cat_SetAge(Cat* self, int age) {
    // set member variable its age to
    // value passed in by parameter age
    self->itsAge = age;
}

// definition of Meow method
// returns: void
// parameters: None
// action: Prints "meow" to screen
void Cat_Meow(Cat* self) {
    printf("Meow.\n");
}

// create a cat, set its age, have it
// meow, tell us its age, then meow again.
int run(int Age) {
    printf("How old is Frisky? ");
    Cat* Frisky = Cat_Cat(Age);
    Cat_Meow(Frisky);
    printf("Frisky is a cat who is ");
    printf("%d years old.\n", Cat_GetAge(Frisky));
    Cat_Meow(Frisky);
    Age++;
    if ((10 * Age + 1) == 1001) {
        printf("I should not enter here\n");
    }
    Cat_SetAge(Frisky, Age);
    printf("Now Frisky is ");
    printf("%d years old.\n", Cat_GetAge(Frisky));
    Cat_Destruct(Frisky);
    return 0;
}
