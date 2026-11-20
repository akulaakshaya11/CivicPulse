import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

CSV_PATH = (
    PROJECT_DIR
    / "data"
    / "population"
    / "ghmc_population_exposure_500m.csv"
)

df = pd.read_csv(CSV_PATH)

print("\n========== DATASET OVERVIEW ==========")

print("Total reference points:", len(df))
print("Missing population values:", df["population_500m"].isna().sum())

print("\n========== COVERAGE STATUS ==========")

print(df["status"].value_counts())

# Use locations with at least 95% valid raster coverage
valid_df = df[
    (df["coverage_percent"] >= 95) &
    (df["population_500m"].notna())
]

print("\n========== VALID DATASET ==========")

print("Points with >= 95% coverage:", len(valid_df))
print("Excluded points:", len(df) - len(valid_df))

print("\n========== POPULATION STATISTICS ==========")

print(
    valid_df["population_500m"].describe(
        percentiles=[0.25, 0.50, 0.75, 0.90, 0.95]
    )
)

print("\n========== SELECTED PERCENTILES ==========")

for percentile in [10, 25, 50, 75, 90, 95, 99]:
    value = valid_df["population_500m"].quantile(
        percentile / 100
    )

    print(f"{percentile}th percentile: {value:.2f}")

print("\n========== COVERAGE STATISTICS ==========")

print(df["coverage_percent"].describe())

print("\nAnalysis completed!")