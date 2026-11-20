
import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    PROJECT_DIR / "data" / "population"
    / "ghmc_combined_spatial_indicators.csv"
)

OUTPUT_PATH = (
    PROJECT_DIR / "data" / "population"
    / "ghmc_underserved_analysis.csv"
)

df = pd.read_csv(INPUT_PATH)

# Retain reliable population estimates
data = df[df["coverage_percent"] >= 95].copy()

# Calculate population thresholds
population_threshold = data["population_500m"].quantile(0.75)

data["high_population"] = (
    data["population_500m"] >= population_threshold
)

categories = [
    "healthcare",
    "education",
    "emergency",
    "community",
    "public_transport"
]

print("Population threshold (75th percentile):",
      round(population_threshold, 2))

print("\nReliable observations:", len(data))

for category in categories:

    facility_column = f"{category}_500m"

    facility_threshold = data[facility_column].quantile(0.25)

    data[f"{category}_low_access"] = (
        data[facility_column] <= facility_threshold
    )

    data[f"{category}_potentially_underserved"] = (
        data["high_population"]
        & data[f"{category}_low_access"]
    )

    print(f"\n========== {category.upper()} ==========")

    print("Facility 25th percentile:",
          round(facility_threshold, 2))

    print("High population locations:",
          int(data["high_population"].sum()))

    print("Low facility availability locations:",
          int(data[f"{category}_low_access"].sum()))

    print("Potentially underserved locations:",
          int(data[f"{category}_potentially_underserved"].sum()))

# Overall indicator: underserved in at least one category
underserved_columns = [
    f"{category}_potentially_underserved"
    for category in categories
]

data["underserved_category_count"] = (
    data[underserved_columns].sum(axis=1)
)

data["underserved_in_any_category"] = (
    data["underserved_category_count"] > 0
)

data.to_csv(OUTPUT_PATH, index=False)

print("\n========== OVERALL RESULTS ==========")
print(
    data["underserved_category_count"]
    .value_counts()
    .sort_index()
)

print("\nLocations underserved in at least one category:",
      int(data["underserved_in_any_category"].sum()))

print("\nSaved to:", OUTPUT_PATH)
