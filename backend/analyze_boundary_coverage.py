
import geopandas as gpd
import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

POINTS_PATH = (
    PROJECT_DIR / "data" / "population"
    / "ghmc_population_coverage_map.gpkg"
)

BOUNDARY_PATH = (
    PROJECT_DIR / "data" / "boundary"
    / "ghmc_boundary.gpkg"
)

OUTPUT_PATH = (
    PROJECT_DIR / "data" / "population"
    / "boundary_coverage_analysis.csv"
)

# Load datasets
points = gpd.read_file(POINTS_PATH)
boundary = gpd.read_file(BOUNDARY_PATH)

# Project both datasets into metres
points = points.to_crs("EPSG:32644")
boundary = boundary.to_crs("EPSG:32644")

# Get GHMC boundary geometry
boundary_geometry = boundary.geometry.union_all()
boundary_line = boundary_geometry.boundary

# Calculate distance of each point from boundary
points["boundary_distance_m"] = (
    points.geometry.distance(boundary_line)
)

# Create distance groups
points["distance_group"] = pd.cut(
    points["boundary_distance_m"],
    bins=[-1, 500, 1000, 2000, float("inf")],
    labels=[
        "0-500m",
        "500m-1km",
        "1-2km",
        "Above 2km"
    ]
)

# Identify points with less than 95% coverage
points["low_coverage"] = (
    points["coverage_percent"] < 95
)

# Calculate group statistics
summary = (
    points.groupby("distance_group", observed=False)
    .agg(
        total_points=("sample_id", "count"),
        low_coverage_points=("low_coverage", "sum"),
        average_coverage=("coverage_percent", "mean")
    )
    .reset_index()
)

summary["low_coverage_percent"] = (
    summary["low_coverage_points"]
    / summary["total_points"] * 100
)

print("\n========== BOUNDARY COVERAGE ANALYSIS ==========")
print(summary.to_string(index=False))

# Export enriched spatial dataset

ENRICHED_PATH = (
    PROJECT_DIR
    / "data"
    / "population"
    / "ghmc_population_enriched.gpkg"
)

points.to_file(
    ENRICHED_PATH,
    layer="population_analysis",
    driver="GPKG"
)

print("\nEnriched spatial dataset saved to:", ENRICHED_PATH)

# Save results
summary.to_csv(OUTPUT_PATH, index=False)

print("\nAnalysis saved to:", OUTPUT_PATH)



from scipy.stats import chi2_contingency

# Build contingency table
contingency_table = []

for _, row in summary.iterrows():
    low = int(row["low_coverage_points"])
    good = int(row["total_points"] - low)

    contingency_table.append([low, good])

# Perform Chi-square test
chi2, p_value, degrees_of_freedom, expected = (
    chi2_contingency(contingency_table)
)

print("\n========== STATISTICAL VALIDATION ==========")

print("Chi-square statistic:", round(chi2, 4))
print("Degrees of freedom:", degrees_of_freedom)
print("P-value:", p_value)

if p_value < 0.05:
    print("Result: Statistically significant association.")
else:
    print("Result: No statistically significant association.")

print("\nExpected frequencies:")
print(expected)


import numpy as np

total = np.sum(contingency_table)

cramers_v = np.sqrt(
    chi2 / (total * min(
        len(contingency_table) - 1,
        len(contingency_table[0]) - 1
    ))
)

print("Cramer's V:", round(cramers_v, 4))