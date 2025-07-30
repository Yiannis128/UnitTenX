#!/usr/bin/env python3

"""
Pearson Correlation Test:
- Null hypothesis: No linear correlation (r = 0)
- Test statistic: t = r × √((n-2)/(1-r²))
- Distribution: t-distribution with (n-2) degrees of freedom
- P-value: 2 × P(T > |t|) for two-tailed test

Key validations:
1. Sample size check: n > 2 ensures valid degrees of freedom
2. Data cleaning: Removes NaN/infinite values that would break correlation
3. Correct formula: The t-statistic formula is mathematically correct
4. Two-tailed test: Uses 2 × (1 - stats.t.cdf(abs(t_stat), df)) for bidirectional correlation

Assumptions met:
- Linear relationship (appropriate for scatter plot trends)
- Continuous variables (iterations and success rates)
- Independent observations (different functions)

Potential considerations:
- Small sample bias: With very small n, correlation can be unstable
- Non-normality: Pearson assumes normal distribution, but it's robust for moderate deviations
- Outliers: Success rates bounded [0,1] should be well-behaved

The script correctly implements the standard statistical test for correlation significance."""

import pandas as pd
import numpy as np
from scipy import stats


def validate_rq1_claims():
    """Validate the RQ1 claims about test quality improvement."""
    # Load the data
    df = pd.read_csv("data.csv")
    
    print("=== RQ1 Test Quality Claims Validation ===")
    print(f"Total entries in dataset: {len(df)}")
    
    # Filter to functions that actually executed (had meaningful UnitTenX runs)
    executed_functions = df[df["total_iterations"] > 0]
    print(f"Functions that executed: {len(executed_functions)} ({len(executed_functions)/len(df)*100:.1f}%)")
    
    # Calculate test quality improvements using only executed functions
    initial_quality = executed_functions["initial_rating"].values
    final_quality = executed_functions["final_rating"].values
    
    # Functions that moved above diagonal (test quality improved)
    improved = final_quality > initial_quality
    num_improved = np.sum(improved)
    improvement_percentage = (num_improved / len(executed_functions)) * 100
    
    print(f"\n1. Functions with improved test quality:")
    print(f"   {num_improved}/{len(executed_functions)} functions ({improvement_percentage:.1f}%) moved above the diagonal")
    
    # Calculate test quality gains
    quality_gains = final_quality - initial_quality
    quality_gains_improved = quality_gains[improved]
    
    # Median test quality gain
    median_gain = np.median(quality_gains_improved)
    median_initial = np.median(initial_quality[improved])
    median_final = np.median(final_quality[improved])
    
    print(f"\n2. Median test quality gain:")
    print(f"   Median gain: +{median_gain:.0f} points (from {median_initial:.0f} to {median_final:.0f})")
    
    # Largest single improvement
    max_improvement = np.max(quality_gains)
    max_improvement_idx = np.argmax(quality_gains)
    max_initial = initial_quality[max_improvement_idx]
    max_final = final_quality[max_improvement_idx]
    
    print(f"\n3. Largest single improvement:")
    print(f"   From {max_initial:.0f} to {max_final:.0f} (+{max_improvement:.0f} points)")


def calculate_rq5_statistics():
    """Calculate and display statistical validation for RQ5 correlation."""
    # Load the data
    df = pd.read_csv("data.csv")
    print(f"Dataset shape: {df.shape}")

    # Calculate success rate for RQ5 (same as in make_plots.py)
    df["success_rate"] = (df["total_iterations"] - df["test_cases_crashed"]) / df[
        "total_iterations"
    ]
    df["success_rate"] = df["success_rate"].fillna(0)

    # Extract the variables for correlation
    x = df["total_iterations"].values
    y = df["success_rate"].values

    # Remove any NaN/infinite values
    mask = np.isfinite(x) & np.isfinite(y)
    x_clean = x[mask]
    y_clean = y[mask]

    print(f"Clean data points: {len(x_clean)}")
    print(f"Total iterations range: {x_clean.min():.1f} to {x_clean.max():.1f}")
    print(f"Success rate range: {y_clean.min():.3f} to {y_clean.max():.3f}")

    if len(x_clean) > 2:
        # Calculate Pearson correlation
        r_value, p_value = stats.pearsonr(x_clean, y_clean)

        print(f"\nPearson correlation results:")
        print(f"r = {r_value:.4f}")
        print(f"p = {p_value:.6f}")

        # Manual calculation to show the math
        n = len(x_clean)
        t_stat = r_value * np.sqrt((n - 2) / (1 - r_value**2))
        df_freedom = n - 2
        p_manual = 2 * (1 - stats.t.cdf(abs(t_stat), df_freedom))

        print(f"\nManual calculation:")
        print(f"n = {n}")
        print(f"t-statistic = {t_stat:.4f}")
        print(f"degrees of freedom = {df_freedom}")
        print(f"p-value (manual) = {p_manual:.6f}")

        print(f"\nSignificance:")
        if p_value < 0.001:
            print("*** Highly significant (p < 0.001)")
        elif p_value < 0.01:
            print("** Very significant (p < 0.01)")
        elif p_value < 0.05:
            print("* Significant (p < 0.05)")
        else:
            print("Not significant (p >= 0.05)")


if __name__ == "__main__":
    validate_rq1_claims()
    print("\n" + "="*50 + "\n")
    calculate_rq5_statistics()


"""GeCoIn Conclusion:

Results Interpretation:

  No statistically significant correlation between total iterations and success rate in RQ5.

  What this means:
  - r = 0.0859: Very weak positive correlation (close to zero)
  - p = 0.224: 22.4% chance this correlation occurred by random chance
  - Conclusion: No evidence of a real relationship between iteration count and test success rate

  For your GeCoIn 2025 presentation:
  - Don't show a trend line for RQ5 - it would be misleading
  - This is actually good science - you're correctly avoiding false claims
  - Interpretation: UnitTenX's robustness isn't simply explained by iteration count alone
  - Alternative angles: Focus on recovery actions (bubble sizes) or other robustness metrics

  Why this happened:
  - Success rate might be influenced by factors other than iteration count (code complexity, recovery strategies, etc.)
  - The relationship might be non-linear or have high variance
  - 202 samples is good size, so it's not a power issue

  This validates your earlier decision to comment out trend lines in RQ3 - you're maintaining scientific rigor by only
  showing statistically supported relationships."""
