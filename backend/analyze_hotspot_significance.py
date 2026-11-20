
import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import chi2_contingency

PROJECT_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = (
    PROJECT_DIR
    / "data"
    / "population"
    / "ghmc_population_lisa.gpkg"
)

# Load LISA results
points = gpd.read_file(
    DATA_PATH,
    layer="local_clusters"
)

# Identify High-High hotspots
points["is_hotspot"] = (
    points["cluster_type"] == "High-High"
)

distance_order = [
    "0-500m",
    "500m-1km",
    "1-2km",
    "Above 2km"
]

# Create observed frequency table
table = pd.crosstab(
    points["distance_group"],
    points["is_hotspot"]
).reindex(distance_order, fill_value=0)

table = table.reindex(columns=[True, False], fill_value=0)
table.columns = ["Hotspots", "Not_Hotspots"]

print("\n========== HOTSPOT FREQUENCY TABLE ==========")
print(table)

# Calculate hotspot rates
rates = pd.DataFrame({
    "total_points": table.sum(axis=1),
    "hotspots": table["Hotspots"]
})

rates["hotspot_rate_percent"] = (
    rates["hotspots"] / rates["total_points"] * 100
).round(2)

print("\n========== HOTSPOT RATES ==========")
print(rates)

# Chi-square test
chi2, p_value, dof, expected = chi2_contingency(table)

n = table.to_numpy().sum()
min_dimension = min(table.shape[0] - 1, table.shape[1] - 1)

cramers_v = np.sqrt(
    chi2 / (n * min_dimension)
)

print("\n========== CHI-SQUARE TEST ==========")
print("Chi-square statistic:", round(chi2, 4))
print("Degrees of freedom:", dof)
print("P-value:", p_value)
print("Cramer's V:", round(cramers_v, 4))

print("\nExpected frequencies:")
print(expected)

if p_value < 0.05:
    print("\nResult: Statistically significant association.")
else:
    print("\nResult: No statistically significant association.")

# Save results
output_path = (
    PROJECT_DIR
    / "data"
    / "population"
    / "hotspot_significance_analysis.csv"
)

rates.to_csv(output_path)

print("\nResults saved to:", output_path)
