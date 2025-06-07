// Copyright 2025 Claudionor N. Coelho Jr

#include <iostream>
#include <stdexcept>
#include <sstream>
#include <string>
#include <cassert>
extern "C" {
    #include "meow.h"
}

using namespace std;

extern "C" {
    int run(int);
}

int failure_count = 0;

void test_run(int test_case_number, int age, const string& expected_output) {
    cout << "Testing use case " << test_case_number << endl << flush;

    // Redirect stdout to capture the output
    streambuf* original_cout = cout.rdbuf();
    ostringstream captured_output;
    cout.rdbuf(captured_output.rdbuf());

    try {
        run(age);
        cout.rdbuf(original_cout); // Restore original cout

        string actual_output = captured_output.str();
        if (actual_output != expected_output) {
            cout << "Test case " << test_case_number << " failed: Output mismatch" << endl;
            cout << "Actual Output: " << actual_output << endl;
            cout << "Expected Output: " << expected_output << endl;
	    throw exception();
        }
    } catch (const exception& e) {
	failure_count++;
        cout.rdbuf(original_cout); // Restore original cout
        cout << "Test case " << test_case_number << " failed with exception: " << e.what() << endl;
    }

    cout << "Completed use case " << test_case_number << endl << flush;
}

int main() {
    // Test case 0
    test_run(0, 2130707444, "How old is Frisky? Meow.\nFrisky is a cat who is 2130707444 years old.\nMeow.\nNow Frisky is 2130707445 years old.\n");

    // Test case 1
    test_run(1, 501, "How old is Frisky? Meow.\nFrisky is a cat who is 501 years old.\nMeow.\nNow Frisky is 502 years old.\n");

    // Test case 2
    test_run(2, -1, "How old is Frisky? Meow.\nFrisky is a cat who is -1 years old.\nMeow.\nNow Frisky is 0 years old.\n");

    // Test case 3
    test_run(3, 99, "How old is Frisky? Meow.\nFrisky is a cat who is 99 years old.\nMeow.\nNow Frisky is 100 years old.\n");

    // Test case 4
    test_run(4, 268435455, "How old is Frisky? Meow.\nFrisky is a cat who is 268435455 years old.\nMeow.\nNow Frisky is 268435456 years old.\n");

    // Test case 5
    test_run(5, 2147483647, "How old is Frisky? Meow.\nFrisky is a cat who is 2147483647 years old.\nMeow.\nNow Frisky is 2147483648 years old.\n");

    cout << "Number of failed tests: " << failure_count << endl;
    return 0;
}
