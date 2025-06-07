# Copyright 2025 Claudionor N. Coelho Jr

implied_functions_prompt = """You are an expert software engineer, and you need to write an "extern" interface for a C++ program to access a C functions.

The source code is below:

<code>
{source_code}
</code>

Complete the interface below to be put in an extern "C" {{ <interface> }} to contain minimally the structures below.

<interface-structures>
{structures}
</interface-structures>

Your output MUST be in the following format, where you first list your plan of action with very precise instructions, and then list ONLY what goes inside extern "C" {{ <your extern code> }}.

<plan-of-action>
List[str]
</plan-of-action>
Wait
<extern>
str
</extern>

REMEMBER you MUST keep the structures defined within <interface-structures> and </interface-structures>. Do NOT delete any one of them.

REMEMBER you MUST add information to make the extern "C" definition compile with the definitions within <interface-structures> and </interface-structures>.

REMEMBER you MUST NOT include any other file in the extern "C" interface.

REMEMBER you MUST only generate the text that appears enclosed between {{ }} and nothing else.  For example, if the extern interface in C++ is `extern "C" {{ int a; }}`, your output must be `<extern>\nint a;</extern>`.

REMEMBER you the latest C standard for the interface.

REMEMBER you MUST use the following format for the output without any preamble and postamble.

<plan-of-action>
List[str]
</plan-of-action>
Wait
<extern>
str
</extern>

REMEMBER do not escape symbols in the extern definition, such as '<' and '>'.

Again, You MUST not include any files using #include in the interface, unless you are including system files.
"""

symbolic_test_prompt = """You are an expert software engineer writing automated unit tests based on specified test scenarios.

Here is the source code for which you need to generate unit tests:
<code>
{source_code}
</code>

You need to generate unit tests based on the following test directives:
<test_directives>
{test_cases}
</test_directives>

Here are the requirements for your response:
- Generate test code that compiles and executes.
- Generate a separate test for each test case specified in `Test Directives`.
- Do not include the source code from `Source Code` in the generated test case.
- Response: Your response must only contain the generated test case.

Here are  additional guidelines for generating the test code:
- Unit Test Generation:
    - Must always call `{target_type}` `{name}`.
    - Write unit tests in {test_language} using the {test_interface} framework.
    - Specify values to the function according to `Test Directives`.
    - Before executing each test, you must output in stdout what's the test is about, and that the test has completed, just like how PyTest works. For example, if you will execute the test function `test_use_case(<value>, <input>, <output>);`, you must first output `cout << \"Use case <description\" << endl;` before executing test.

- Include: Add include function `{name}` for project under `extern "C" {{}}` with the correct function signature.
- Error Handling:
    - Use try/catch to prevent tests from terminating early.
    - Count the number of failures and report them at the end, similar to pytest.
    - Function `main` should always return 0.
- Test must guarded by a timeout:
    ```cpp
    void run_with_timeout(std::function<void()> func) {{
        const char* timeout_env = std::getenv("UNITTENX_TIMEOUT");
        int timeout_seconds;
        if (timeout_env == nullptr) timeout_seconds = 1;
        else timeout_seconds = std::stoi(timeout_env);
        std::packaged_task<void()> task(func);
        std::future<void> future = task.get_future();
        std::thread(std::move(task)).detach();
        std::chrono::seconds timeout(timeout_seconds);
        if (future.wait_for(timeout) == std::future_status::timeout) {{
            cout << "ERROR: function executed exceeded timeout limit." << endl << flush;
            throw std::runtime_error("error");
        }}
        
        // Check if the future holds an exception and rethrow it
        try {{
            future.get(); // Will rethrow the exception if func threw one
        }} catch (...) {{
            // Optionally, log the exception or take other actions
            throw; // Rethrow the caught exception
        }}
    }}
    ```
- Expected Value Check:
    ```cpp
    if (expected != actual) {{
        cout << "Expected: " << expected << endl;
        cout << "Actual: " << actual << endl;
        throw std::runtime_error("error");
    }}
    ```
    
- Test function:
    ```cpp
    void test_case_1() {{
        cout << \"Starting test case 1\" << endl;
        <initialization of test case 1>
        <assignment of parameters and expected values>
        {name}(<parameters>);
        cout << \"Test case 1 completed\" << endl;
    }}
    ...
    void test_case_2() {{
        ...
        {name}(value);
        ...
    }}
    ```

- Main Function:
    - Generate a `main` function that calls each individual test case.
    - Invocation of test function MUST follow the pattern.
        ```cpp
        try {{
            cout << "Test case 1: <description of test case 1>" << endl;
            run_with_timeout(test_case_1);
        }} catch (...) {{
            number_of_failures++;
            cout << "Exception in test case: <description of test case 1>" << endl;
        }}
        ```
    - number_of_failures is an integer value in `main` function.
    - Do not include inline tests in the `main` function.
    
REMEMBER you MUST print the message "Test case <id>: <description>" before calling `run_with_timeout(test_case_<id>)`.

REMEMBER message printed when test case ends should be "Test case <id> completed.".

REMEMBER, do not change `extern "C" {{ ... }}` unless you need to fix a compilation error.

REMEMBER, you can only use the functions and data structures inside `extern "C" {{ ... }}` in your test.

REMEMBER do not escape symbols in the test code, such as '<' and '>'.

Now output the test code following the requirements above. Do not include any preamble or postamble.
"""


unit_test_prompt = """You are an expert software engineer specializing in cybersecurity, networking, and operating systems. You write automated unit tests for software in these domains to ensure the highest possible rating and reliability.

Here are the current coverage holes:
<coverage>
```yaml
{missing_coverage}
```
<coverage>

Here is the source code for which you need to generate unit tests:
<code>
{source_code}
<code>

Here are the attention functions:
<functions>
```yaml
{function_names}
```
</functions>

Here is the current unit test:
<unit-test>
```{test_language}
{unit_test}
```
</unit-test>

Here is a code review:
<review>
```yaml
{review}
```
</review>

Here is the output from coverage:
<coverage-log>
```log
{coverage_output}
```
</coverage-log>

Here are the test directives:
<test-directives>
```yaml
{test_cases}
```
</test-directives>

Your job is to
- Add more tests on top of sensitization tests from `Test Directives` to improve ratings.
- Add tests for critical values and performance.
- If `Test Directives` are not present, cover lines of the code.
- If you need to create a vector or array with more than 100 predefined values, you MUST use a loop to assign values to avoid very long programs.
- You MUST first write a step-by-step plan of action to explain how you will solve the problems outlined in `Code Review`, and how to improve the Rating. Then you will follow your step-by-step plan to write the new test code.
- Your plan of action MUST include strategy to initialize all global variables that are instantiated in `{name}`.
- When you write the test, you MUST follow the instructions from the plan of action.

{with_messages}

Requirements:
- Output format should be:
    <plan-of-action>
    List[str]
    </plan-of-action> 
    Wait
    <test-code>
    str
    </test-code>
    <explanation>
    str
    </explanation>
- All inputs and outputs of the tests should be properly captured.
- Always improve previous unit tests from `Current Unit Test` and `Code Review` by reusing them and applying instructions to raise the rating.
- Fix issues with current tests provided in `Current Unit Test` and add additional tests.
- Remove tests only if they are repetitive or if fixing something. Sensitization conditions from `Test Directives` must always be maintained.
- Compare the result with the actual value you EXPECT.
{additional_requirements}

Laws of Numbers:
- Incrementing positive values MUST ONLY yield positive values (e.g., `INT_MAX + 1` yielding a negative number MUST be an error).
- Decrementing negative values MUST ONLY yield negative values (e.g., `INT_MIN - 1` yielding a positive number MUST be an error).
- Multiplying and dividing positive values MUST ONLY yield positive values (e.g., `INT_MAX * 2` yielding a negative number MUST be an error).
- Multiplying and dividing numbers with different signs MUST ONLY yield negative values (e.g., -INT_MAX * 2 yielding a positive number MUST be an error).

Unit Test Generation:
- You MUST write unit-tests calling {target_type} `{name}`.
- Write unit tests in {test_language} using the {test_interface} framework only for the {target_type} `{name}` in `Source Code`.
- Consider functions listed in `Attention Functions` during your analysis, but always call {target_type} `{name}`.

Rating Criteria:  Your tests will be rated considering the following:
- Test compiles (compilation failure results in a rating of 0).
- Test runs, potentially failing on uncovered aspects by the original programmer.
- Try to reach all lines of code when testing the function `{name}`.
- Test critical values in conditionals:
    1. For scalar `a`, test values around the comparison expression (e.g., if `a == 3`, test 2, 3, and 4).
    2. For scalar `a`, ensure tests observe the laws of numbers.
    3. For vectors, lists, or dictionaries, test critical values, considering data structure size (e.g., if `len(a) == 3`, test 0, 1, 10, 100, etc., in addition to 2, 3, and 4).
- Check if the original algorithm scales poorly in performance tests (performance should not exceed O(n^1.5)).

Handling Issues:
- Fix all parsing, compilation, and unexpected errors, even if they have not described in `Output from Coverage`.
- If there is a 'core dump' crash in the log of `Output from Coverage`, detect which test case caused the crash, and comment the test out in main, by prefixing the test function invocation with `// CRASH`  with a message to let the user know that the test function is commented out because it is crashing.

Additional Instructions:
- Generate a separate test for each test group (tests with the same objective).
- The source code from `Source Code` SHOULD NOT be included in the generated testcase.
- Your response MUST be executable code.
- If `{name}` is not a valid {target_type} in the `Source Code`, raise an error in the test written in the {test_interface} framework.

REMEMBER you MUST first write a step-by-step plan of action explaining how you will solve the problems outlined in `Code Review`, and especially looking at fixing compilation and run-time errors, and improving code coverage.

REMEMBER you MUST follow the step-by-step plan of action when generating the test code.

REMEMBER you MUST ONLY call {target_type} `{name}` and NOT ANY OTHER FUNCTION.

REMEMBER you MUST ONLY call {target_type} `{name}` and NOT ANY OTHER FUNCTION TO TEST THE FUNCTION.  To test `{name}`, you may need to access other functions declared in extern "C" or access global variables to initialize data structures.

REMEMBER, if {target_type} `{name}` uses global variables, you may need to properly assign values to the global variables properly before calling `{name}`.  You MUST look at how other functions assign values to these global variables.

REMEMBER if a test case is crashing, you MUST comment the test case with `// CRASH ` in function `main` to avoid any further crashes if it is not already commented out.
 
REMEMBER message printed when test case begins should be "Test case <id>: <description>".

REMEMBER you MUST print the message "Test case <id>: <description>" before calling `run_with_timeout(test_case_<id>)`.

REMEMBER message printed when test case ends should be "Test case <id> completed.".

REMEMBER your output must be in this format:
    <plan-of-action>
    List[str]
    </plan-of-action> 
    Wait
    <test-code>
    str
    </test-code>
    <explanation>
    str
    </explanation>
    
REMEMBER you MUST not escape symbols in the test code, such as '<' and '>'.  For example, you MUST NOT replace '<' by '&lt;' and you MUST NOT replace '>' by '&gt;'. 

REMEMBER you MUST generate the `test-code` ready for compilation. If you fail to do that, the generated code will not compile.

REMEMBER you MUST output the test program as a string without any preamble or postamble, and no backticks, only a compilation ready program.
    
Ensure your output includes all required keys and does not include any additional keys. Ensure your output is valid format. The system will not work if the output you produce is invalid. Provide no preamble or postamble.

Now return your response following all the provided instructions."""

reflection_prompt = """You are an expert software engineer specializing in cybersecurity, networking, and operating systems. You review all tests written in `Current Unit Test` in these domains to recommend changes to the tests to increase the quality of the tests. The quality is measure in terms of a rating system.

Here is the current unit test to review:
<unit-test>
```{test_language}
{unit_test}
```
</unit-test>

Here are the attention functions:
<fuctions>
```yaml
{function_names}
```
</functions>

Here is the relevant source code:
<code>
{source_code}
</code>

Here is the output from coverage:
<coverage-output>
```log
{coverage_output}
```
</coverage-output>

Here are previous code reviews:
<reviews>
```yaml
{reviews}
```
</reviews>

{target_type}: {name}

Instructions:
1. Generate Review Response in JSON:
    - Your response should be in the following JSON format:
    {{
        "review": List[str],
        "summary": str,
        "rating": int
    }}
    - Your response MUST NOT contain any information other than the JSON specification above.
    - The JSON output MUST only contain the fields "review", "summary" and "rating".
    - You MUST not output any preamble or postamble.
2. Review Only Tests:
    - You MUST ONLY review the test code from `Current Unit Test`.
    - You SHOULD NOT review any tests tagged with CRASH.
    - You SHOULD NOT recommend to remove CRASH comments from testcase. If there are no tests left, make the recommendation to create new tests that do not case the same problems as previous tests.
    - The review MUST be a bullet list containing comments and instructions on how to improve the test.
    - You MUST address issues from previous reviews ONLY if they have not been addressed.
    - You MUST only suggest actions to improve coverage for lines containing statements in the code.
    - You MUST ensure that all global variables instantiated in `{name}` are initialized.
    - You MUST recommend coverage lines that the test should address by recommending testing the first line of a basic block.
3. Rate the Test:
    - At the end of the review, write a sentence giving a rate between 0 and 10 on how good the test is.
    - Rate based on the following characteristics:
        - If the test compiles. If there are compilation errors (e.g., "make: *** [Makefile:3: compile] Error 1"), set the rating to 0 and flag it.
        - It is the MOST SERIOUS error to leave a compilation error or NameError in the test routine.
        - If the test runs, excluding missing cases the original programmer did not consider.
        - If the test attempts to reach all statements of the code when exercising the function `{name}`.
        - If the test tries critical values on any expression of a conditional:
            - For scalar `a`, test values around the comparison expression (e.g., if code has `if a == 3`, test 2, 3, 4).
            - For vector, list, or dictionary `a`, test critical values considering data structure size (e.g., `if len(a) == 3`, test 0, 1, 2, 3, 4, 10, 100, 1000, 10000, ...).
        - If the test checks if the original algorithm scales badly in some cases of performance tests. Performance should not increase more than O(n^1.5) as parameters increase.

4. Handling Failures:
    - If the test encounters a software failure (e.g., not handling negative numbers), keep the test as the software developer will need to handle that case later.
    - NEVER recommend adjusting the test because the current implementation does not handle a specific case (like a negative number).

5. Previous Reviews:
    - If `Previous code reviews` are present, write sentences in different ways to assist the developer in following the proper recommendations.
    - Your rating must consider if the recommendations have been observed and provide new feedback.

6. Good Examples of Reviews:
    - You must generate a testcase to reach line `line-number` of `{name}`.
    - You must test the critical values of 4, 5, and 6 for the integer parameter `a`, as you have the comparison `a == 5` in the code.
    - You must test the negative number -1 for the integer parameter.
    - You must test a vector size of 100 and 1000 for the parameter.

7. Summary and Review Requirements:
    - Your `summary` and `review` should not be repetitive.
    - The `summary` should be a concise summary of the `review` section, using assertive language. Do not repeat what has been said before.

REMEMBER, if the test is not invoking {target_type} {name}, your review must clearly state to rewrite the test to invoke {target_type} `{name}`.

REMEMBER, if the testcase is crashing with segmentation fault or core dump, your review MUST contain only one item instructing the software engineer to comment it out.

REMEMBER, do not change `extern "C" {{ ... }}` unless you need to fix a compilation error.

REMEMBER, you can only use the functions and data structures inside `extern "C" {{ ... }}` in your test.

REMEMBER your output must be in this JSON format:
{{
    "review": List[str],
    "summary": str,
    "rating": int
}}

REMEMBER you MUST limit your output to 1000 tokens or less, and do not be repetitive.

REMEMBER, you MUST NOT duplicate comments in your "review".

Ensure to recommend coverage lines that the test should address by testing the first line of a basic block.

Ensure your output includes all required keys and does not include any additional keys. Ensure your output is valid JSON and be sure to escape characters appropriately. The system will not work if the JSON you produce is invalid. Provide no preamble or postamble.

Now output your review for the current unit test following the requirements above in the JSON object described."""
