#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def load_data() -> pd.DataFrame:
    """Load and return the dataset."""
    return pd.read_csv("data.csv")


def create_square_plot() -> None:
    """Configure plot to be square with consistent styling."""
    plt.figure(figsize=(8, 8))
    plt.gca().set_aspect("equal", adjustable="box")


def save_plot(filename: str) -> None:
    """Save the plot with consistent formatting."""
    plt.tight_layout()
    plt.grid(True, alpha=0.3)
    plt.savefig("images/" + filename, dpi=300, bbox_inches="tight")
    plt.show()


def plot_rq1_coverage_improvement(df: pd.DataFrame) -> None:
    """RQ1: How effectively does UnitTenX generate unit tests that increase code coverage?"""
    create_square_plot()

    # Scatter plot of initial vs final ratings
    plt.scatter(
        df["initial_rating"],
        df["final_rating"],
        alpha=0.7,
        s=60,
        c="steelblue",
        edgecolors="darkblue",
    )

    # Add y=x reference line
    min_val = min(df["initial_rating"].min(), df["final_rating"].min())
    max_val = max(df["initial_rating"].max(), df["final_rating"].max())
    plt.plot(
        [min_val, max_val],
        [min_val, max_val],
        "r--",
        alpha=0.8,
        linewidth=2,
        label="No Improvement Line",
    )

    plt.xlabel("Initial Rating (Coverage)", fontsize=12, fontweight="bold")
    plt.ylabel("Final Rating (Coverage)", fontsize=12, fontweight="bold")
    # plt.title(
    #     "RQ1: UnitTenX Coverage Improvement Effectiveness",
    #     fontsize=14,
    #     fontweight="bold",
    #     pad=20,
    # )
    plt.legend()

    save_plot("rq1_coverage_improvement.png")


def plot_rq2_error_handling(df: pd.DataFrame) -> None:
    """RQ2: How does UnitTenX handle compilation errors, runtime exceptions, and timeouts?"""
    # Use a non-square plot—rectangular is better for bar charts
    plt.figure(figsize=(12, 6))

    error_types = [
        "compilation_errors",
        "segmentation_faults",
        "timeouts",
        "total_iterations",
    ]
    error_data = df[error_types].sum()
    colors = ["#ff6b6b", "#ffd93d", "#6bcf7f", "#4ecdc4"]

    # Create spaced bar positions for better readability
    positions = np.arange(len(error_types))
    bars = plt.bar(positions, error_data, color=colors, alpha=0.8, width=0.5)

    plt.xlabel("Metrics", fontsize=12, fontweight="bold")
    plt.ylabel("Total Count", fontsize=12, fontweight="bold")

    labels = [
        "Compilation\nErrors",
        "Segmentation\nFaults",
        "Timeouts",
        "Total\nIterations",
    ]
    plt.xticks(positions, labels, fontsize=11)

    # Add value labels on bars
    for bar, value in zip(bars, error_data):
        if value > 0:
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.2,  # Slightly higher so it doesn't overlap
                f"{int(value)}",
                ha="center",
                va="bottom",
                fontsize=11,
                fontweight="bold",
            )

    save_plot("rq2_error_handling.png")


def plot_rq3_reflection_feedback(df: pd.DataFrame) -> None:
    """RQ3: How does the reflection and feedback loop contribute to iterative improvement?"""
    plt.figure(figsize=(4, 4))

    # Scatter plot of reflection cycles vs rating improvement
    df["rating_improvement"] = df["final_rating"] - df["initial_rating"]

    plt.scatter(
        df["reflection_cycles"],
        df["rating_improvement"],
        alpha=0.7,
        s=60,
        c="darkorange",
        edgecolors="orangered",
    )

    # Add trend line
    # z = np.polyfit(df["reflection_cycles"], df["rating_improvement"], 1)
    # p = np.poly1d(z)
    # plt.plot(
    #     df["reflection_cycles"],
    #     p(df["reflection_cycles"]),
    #     "g--",
    #     alpha=0.8,
    #     linewidth=2,
    #     label=f"Trend Line",
    # )

    plt.xlabel("Number of Reflection Cycles", fontsize=12, fontweight="bold")
    plt.ylabel("Rating Improvement", fontsize=12, fontweight="bold")
    # plt.title(
    #     "RQ3: Reflection & Feedback Loop Impact", fontsize=14, fontweight="bold", pad=20
    # )

    # Set y-axis to increment by 1
    plt.gca().yaxis.set_major_locator(plt.MultipleLocator(1))

    plt.legend()

    save_plot("rq3_reflection_feedback.png")


def plot_rq5_robustness(df: pd.DataFrame) -> None:
    """RQ5: How robust is UnitTenX in maintaining test suite execution?"""
    plt.figure(figsize=(4, 4))

    # Calculate success rate and plot against total iterations
    df["success_rate"] = (df["total_iterations"] - df["test_cases_crashed"]) / df[
        "total_iterations"
    ]
    df["success_rate"] = df["success_rate"].fillna(0)  # Handle division by zero

    # Create bubble chart where bubble size represents recovery actions
    sizes = (
        df["recovery_actions"] + 1
    ) * 20  # +1 to avoid zero size, *20 for visibility

    scatter = plt.scatter(
        df["total_iterations"],
        df["success_rate"],
        s=sizes,
        alpha=0.6,
        c="green",
        edgecolors="darkgreen",
    )

    plt.xlabel("Total Iterations", fontsize=12, fontweight="bold")
    plt.ylabel("Success Rate (Non-crashed Tests)", fontsize=12, fontweight="bold")
    # plt.title(
    #     "RQ5: UnitTenX Robustness in Test Execution",
    #     fontsize=14,
    #     fontweight="bold",
    #     pad=20,
    # )

    # Add legend for bubble sizes
    plt.text(
        0.02,
        0.90,
        "Bubble size represents\nrecovery actions taken",
        transform=plt.gca().transAxes,
        fontsize=8,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue"),
        verticalalignment="top",
    )

    save_plot("rq5_robustness.png")


def main() -> None:
    """Main function to generate all research question plots."""
    # Load data
    df = load_data()

    print(f"Loaded dataset with {len(df)} functions")
    print(f"Dataset columns: {list(df.columns)}")

    # Generate plots for each research question
    print("\nGenerating plots for research questions...")

    plot_rq1_coverage_improvement(df)
    print("✓ RQ1: Coverage improvement plot generated")

    plot_rq2_error_handling(df)
    print("✓ RQ2: Error handling plot generated")

    plot_rq3_reflection_feedback(df)
    print("✓ RQ3: Reflection feedback plot generated")

    plot_rq5_robustness(df)
    print("✓ RQ5: Robustness plot generated")

    print("\nAll plots have been generated and saved!")


if __name__ == "__main__":
    main()
