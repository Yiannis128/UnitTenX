#!/usr/bin/env python3
"""
extract_unittenx_log_enhanced.py
-------------------------------
Comprehensive parser for UnitTenX execution logs to extract research metrics.

This script extracts data for all five research questions:
1. Coverage effectiveness
2. Error handling capabilities  
3. Reflection loop contribution
4. Edge case identification
5. Robustness to failures
"""

import re
import csv
import sys
from pathlib import Path


def parse_log(text: str):
    """Parse UnitTenX log and extract comprehensive metrics per function execution."""
    rows = []
    current_execution = None

    # Track state across iterations
    in_symbolic_engine = False

    for line_num, line in enumerate(text.splitlines(), 1):
        line = line.strip()

        # ── New function execution start ──────────────────────────
        if match := re.search(r"make -f \S+ (i_[\w]+)", line):
            # Save previous execution if exists
            if current_execution:
                rows.append(current_execution)

            current_execution = {
                "function_name": match.group(1),
                "start_line": line_num,
                "total_iterations": 0,
                "max_iterations_reached": 0,
                "initial_rating": None,
                "final_rating": None,
                "rating_improvement": 0,
                "compilation_errors": 0,
                "segmentation_faults": 0,
                "timeouts": 0,
                "test_cases_generated": 0,
                "test_cases_crashed": 0,
                "symbolic_test_cases": 0,
                "edge_cases_detected": 0,
                "boundary_values_tested": 0,
                "missing_coverage_lines": 0,
                "coverage_success": 0,
                "recovery_actions": 0,
                "reflection_cycles": 0,
                "esbmc_successful": 0,
                "compilation_attempts": 0,
                "successful_compilations": 0,
                "runtime_errors": 0,
                "impossible_cache_calls": 0,
                "cache_size_boundary_tests": 0,
                "null_pointer_tests": 0,
                "performance_timeouts": 0,
                "reflection_feedback_provided": 0,
            }
            continue

        if current_execution is None:
            continue

        # ── Iteration tracking ────────────────────────────────────
        if match := re.search(r"Doing iteration (\d+)", line):
            iteration_num = int(match.group(1))
            current_execution["total_iterations"] = max(
                current_execution["total_iterations"], iteration_num
            )
            current_execution["reflection_cycles"] += 1

        # ── Symbolic engine phase ─────────────────────────────────
        if "entering symbolic engine" in line:
            in_symbolic_engine = True
        elif "entering coverage hole extraction" in line:
            in_symbolic_engine = False

        # ── Test case generation from symbolic engine ─────────────
        if in_symbolic_engine and re.search(r"Test case \d+:", line):
            current_execution["symbolic_test_cases"] += 1
            current_execution["test_cases_generated"] += 1

        # ── Regular test case generation ──────────────────────────
        if not in_symbolic_engine and re.search(r"Test case \d+:", line):
            current_execution["test_cases_generated"] += 1

        # ── Reflection ratings ────────────────────────────────────
        if match := re.search(r"rating: (\d+)", line):
            rating = int(match.group(1))
            if current_execution["initial_rating"] is None:
                current_execution["initial_rating"] = rating
            current_execution["final_rating"] = rating

        # ── Error detection ───────────────────────────────────────
        if "error:" in line.lower() and (
            "make[" in line or "compilation" in line.lower()
        ):
            current_execution["compilation_errors"] += 1

        if "compilation" in line.lower() and "attempt" in line.lower():
            current_execution["compilation_attempts"] += 1

        if "Segmentation fault" in line:
            current_execution["segmentation_faults"] += 1
            current_execution["runtime_errors"] += 1

        if "ERROR: function executed exceeded timeout limit" in line:
            current_execution["timeouts"] += 1
            current_execution["performance_timeouts"] += 1

        # ── Recovery actions ──────────────────────────────────────
        if "commenting out test_case" in line:
            current_execution["test_cases_crashed"] += 1
            current_execution["recovery_actions"] += 1

        # ── Coverage analysis ─────────────────────────────────────
        if "no missing coverage found" in line:
            current_execution["coverage_success"] = 1
            current_execution["missing_coverage_lines"] = 0
        elif match := re.search(r"could not reach lines: ([0-9,\s]+)", line):
            lines_str = match.group(1).replace(" ", "")
            if lines_str:
                current_execution["missing_coverage_lines"] = len(
                    [x for x in lines_str.split(",") if x]
                )

        # ── Edge case and boundary value detection ────────────────
        edge_values = {
            0,
            1,
            99,
            100,
            101,
            999,
            1000,
            1001,
            999999999,
            1000000000,
            1000000001,
        }
        numbers_in_line = [int(x) for x in re.findall(r"\b\d+\b", line) if x.isdigit()]

        for num in numbers_in_line:
            try:
                num_int = int(num)
                if num_int in edge_values:
                    current_execution["edge_cases_detected"] += 1
                    if num_int in {99, 100, 101, 999999999, 1000000000, 1000000001}:
                        current_execution["boundary_values_tested"] += 1
                        if "cache" in line.lower() and "size" in line.lower():
                            current_execution["cache_size_boundary_tests"] += 1
            except ValueError:
                continue

        # ── Special case detections ───────────────────────────────
        if "cache_impossible" in line:
            current_execution["impossible_cache_calls"] += 1

        if "null" in line.lower() and "pointer" in line.lower():
            current_execution["null_pointer_tests"] += 1

        # ── ESBMC success ─────────────────────────────────────────
        if "esbmc" in line.lower() and "success" in line.lower():
            current_execution["esbmc_successful"] += 1

        # ── Compilation success ───────────────────────────────────
        if "compilation successful" in line.lower() or (
            "gcc" in line and "error" not in line.lower()
        ):
            current_execution["successful_compilations"] += 1

        # ── Reflection feedback ───────────────────────────────────
        if "review:" in line or "summary:" in line:
            current_execution["reflection_feedback_provided"] += 1

    # Add final execution
    if current_execution:
        # Calculate derived metrics
        if current_execution["initial_rating"] and current_execution["final_rating"]:
            current_execution["rating_improvement"] = (
                current_execution["final_rating"] - current_execution["initial_rating"]
            )

        current_execution["max_iterations_reached"] = (
            1 if current_execution["total_iterations"] >= 4 else 0
        )
        rows.append(current_execution)

    return rows


def write_csv(rows, outfile):
    """Write extracted data to CSV file."""
    if not rows:
        print("No UnitTenX executions found in log.")
        return

    fieldnames = [
        "function_name",
        "total_iterations",
        "max_iterations_reached",
        "initial_rating",
        "final_rating",
        "rating_improvement",
        "compilation_errors",
        "segmentation_faults",
        "timeouts",
        "test_cases_generated",
        "test_cases_crashed",
        "symbolic_test_cases",
        "edge_cases_detected",
        "boundary_values_tested",
        "cache_size_boundary_tests",
        "missing_coverage_lines",
        "coverage_success",
        "recovery_actions",
        "reflection_cycles",
        "esbmc_successful",
        "compilation_attempts",
        "successful_compilations",
        "runtime_errors",
        "impossible_cache_calls",
        "null_pointer_tests",
        "performance_timeouts",
        "reflection_feedback_provided",
    ]

    with open(outfile, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            # Only write fields that exist in fieldnames
            filtered_row = {k: v for k, v in row.items() if k in fieldnames}
            writer.writerow(filtered_row)

    print(f"Successfully extracted data for {len(rows)} function executions")
    print(f"Wrote results to {outfile}")

    # Print summary statistics
    print("\n=== EXTRACTION SUMMARY ===")
    total_functions = len(rows)
    successful_coverage = sum(1 for r in rows if r["coverage_success"])
    total_errors = sum(
        r["compilation_errors"] + r["segmentation_faults"] + r["timeouts"] for r in rows
    )
    total_recovery = sum(r["recovery_actions"] for r in rows)

    print(f"Functions processed: {total_functions}")
    print(
        f"Coverage success rate: {successful_coverage}/{total_functions} ({100*successful_coverage/total_functions:.1f}%)"
    )
    print(f"Total errors handled: {total_errors}")
    print(f"Total recovery actions: {total_recovery}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python extract_unittenx_log_enhanced.py <logfile> <output.csv>")
        print(
            "\nThis script extracts comprehensive metrics for UnitTenX research questions:"
        )
        print("1. Coverage effectiveness")
        print("2. Error handling capabilities")
        print("3. Reflection loop contribution")
        print("4. Edge case identification")
        print("5. Robustness to failures")
        sys.exit(1)

    logfile = Path(sys.argv[1])
    output_csv = Path(sys.argv[2])

    if not logfile.exists():
        print(f"Error: Log file {logfile} not found")
        sys.exit(1)

    try:
        text = logfile.read_text(encoding="utf-8", errors="ignore")
        rows = parse_log(text)
        write_csv(rows, output_csv)
    except Exception as e:
        print(f"Error processing log file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
