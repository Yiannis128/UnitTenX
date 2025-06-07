// Copyright 2025 Claudionor N. Coelho Jr

#ifndef __MEOW_H
#define __MEOW_H

typedef struct {
    int itsAge;
    char *string;
} Cat;

Cat* Cat_Cat(int initialAge);
Cat* Cat_Cat_copy(const Cat* copy_from);
Cat* Cat_operator_assign(Cat* self, const Cat* copy_from);
void Cat_Destruct(Cat* self);

int Cat_GetAge(const Cat* self);
void Cat_SetAge(Cat* self, int age);
void Cat_Meow(Cat* self);

extern int run(int);

#endif
