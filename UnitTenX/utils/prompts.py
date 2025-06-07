# Copyright 2025 Claudionor N. Coelho Jr

symbolic_test_prompt = """
Role: You are an expert software engineer writing automated unit tests based on specified test scenarios.

Requirements:

- Include: Add include function `{name}` for project under `extern "C" {{}}` with the correct function signature.

- Unit Test Generation:

    - Must always call `{target_type}` `{name}`.

    - Write unit tests in {test_language} using the {test_interface} framework.

    - Specify values to the function according to `Test Directives`.
    
    - Before executing each test, you must output in stdout what's the test is about, and that the test has completed, just like how PyTest works. For example, if you will execute the test function `test_use_case(<value>, <input>, <output>);`, you must first output `cout << \"Use case <description\" << endl;` before executing test.

- Error Handling:

    - Use try/catch to prevent tests from terminating early.

    - Count the number of failures and report them at the end, similar to pytest.
    
    - Function `main` should always return 0.

- Expected Value Check:

    ```cpp
    if (expected != actual) {{
        cout << "Expected: " << expected << endl;
        cout << "Actual: " << actual << endl;
        number_of_failures++;
    }}
    ```
- Main Function:

    - Generate a `main` function that calls each individual test case.

    - Do not include inline tests in the `main` function.

Output:

- Generate test code that compiles and executes.

- Generate a separate test for each test case specified in `Test Directives`.

- Do not include the source code from `Source Code` in the generated test case.

- Response: Your response must only contain the generated test case.

Source Code:

{source_code}

Test Directives:

```yaml
{test_cases}
```
"""

unit_test_prompt = """
Role: You are an expert software engineer specializing in cybersecurity, networking, and operating systems. You write automated unit tests for software in these domains to ensure the highest possible rating and reliability.

Your job is to:

- Add more tests on top of sensitization tests from `Test Directives` to improve ratings.

- Add tests for critical values and performance.

- If `Test Directives` are not present, cover lines of the code.

- If you need to create a vector or array with more than 100 predefined values, you MUST use a loop to assign values to avoid very long programs.

- You MUST first write a step-by-step plan of action to explain how you will solve the problems outlined in `Code Review`, and how to improve the Rating. Then you will follow your step-by-step plan to write the new test code.

{with_messages}

Requirements:

- Output format should be in the JSON format: ```json\n{{ "plan of action": List[str], "test program": str, "explanation": List[str] }}```.

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

- If there is a crash in the log of `Output from Coverage`, for example, in the case of a `core dumped`, you will detect the crash because there will be no coverage generation. The crashing testcase will be the last one you started that did not complete.

- If a testcase crashes, you MUST comment out the invocation of the crashing test function in the main function, by prefixing the test function invocation with // CRASH, and you MUST prefix the line with a message to let the user know that this test function is commented out because it is crashing.

Additional Instructions:

- Generate a separate test for each test group (tests with the same objective).

- The source code from `Source Code` SHOULD NOT be included in the generated testcase.

- Your response MUST be executable code.

- If `{name}` is not a valid {target_type} in the `Source Code`, raise an error in the test written in the {test_interface} framework.

Current Coverage Holes:

```yaml
{missing_coverage}
```

Source Code:

{source_code}

Attention Functions:

```yaml
{function_names}
```

Current Unit Test:

```{test_language}
{unit_test}
```

Code Review:

```yaml
{review}
```

Output from Coverage: The log of the test run is as follows:
```log
{coverage_output}
```

Test Directives:

```yaml
{test_cases}
```
"""

reflection_prompt = """
Role: You are an expert software engineer specializing in cybersecurity, networking, and operating systems. You review all tests written in `Current Unit Test` in these domains to recommend changes to the tests to increase the quality of the tests. The quality is measure in terms of a rating system.

Instructions:

1. Generate Review Response in JSON:

    - Your response should be in the following JSON format:

    ```json
    {{
        "review": List[str],
        "summary": str,
        "rating": int
    }}```

    - Your response MUST NOT contain any information other than the JSON specification above.

    - The JSON output MUST only contain the fields "review", "summary" and "rating".

2. Review Only Tests:

    - You MUST ONLY review the test code from `Current Unit Test`.
    
    - If a test case has been commented out and tagged as a CRASH, do not review it.

    - The review MUST be a bullet list containing comments and instructions on how to improve the test.
    
    - You MUST address issues from previous reviews ONLY if they have not been addressed.
    
    - You MUST only suggest actions to improve coverage for lines containing statements in the code.
         
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

{target_type}: {name}

Attention Functions:

```yaml
{function_names}
```

Source Code:

{source_code}

Current Unit Test:

```{test_language}
{unit_test}
```

Output from coverage:

```log
{coverage_output}
```

Previous code reviews:

```yaml
{reviews}
```
"""
