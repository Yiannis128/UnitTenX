#include <iostream>
#include <stdexcept>
#include <cstdio>
#include <cassert>
#include "files/include/meow.h"

using namespace std;

extern "C" {
    int run(int);
}

void test_run(int test_case_number, int age, const string& expected_output) {
    cout << "Testing use case " << test_case_number << endl << flush;

    // Redirect stdout to a string
    FILE* original_stdout = stdout;
    FILE* temp_stdout = tmpfile();
    stdout = temp_stdout;

    try {
        int result = run(age);
        fflush(stdout);

        // Restore stdout
        stdout = original_stdout;

        // Read the output from the temporary file
        fseek(temp_stdout, 0, SEEK_SET);
        string actual_output;
        char buffer[256];
        while (fgets(buffer, sizeof(buffer), temp_stdout) != nullptr) {
            actual_output += buffer;
        }
        fclose(temp_stdout);

        // Check the result
        if (result != 0) {
            cerr << "Test case " << test_case_number << " failed: Expected 0, got " << result << endl;
            assert(result == 0);
        }

        // Check the output
        if (actual_output != expected_output) {
            cerr << "Test case " << test_case_number << " failed: Expected output:\n" << expected_output << "\nActual output:\n" << actual_output << endl;
            assert(actual_output == expected_output);
        }
    } catch (const std::exception& e) {
        cerr << "Test case " << test_case_number << " failed with exception: " << e.what() << endl;
        assert(false);
    }

    cout << "Test case " << test_case_number << " completed" << endl << flush;
}

int main() {
    int failure_count = 0;

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

    cout << "Number of failed test cases: " << failure_count << endl << flush;
    return failure_count;
}
