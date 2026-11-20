
import pandas as pd
import geopandas as gpd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

POPULATION_PATH = (
    PROJECT_DIR / "data" / "population"
    / "ghmc_population_exposure_500m.csv"
)

FACILITY_PATH = (
    PROJECT_DIR / "data" / "facilities"
    / "ghmc_facility_proximity.csv"
)

REFERENCE_PATH = (
    PROJECT_DIR / "data" / "boundary"
    / "ghmc_reference_points.gpkg"
)

OUTPUT_CSV = (
    PROJECT_DIR / "data" / "population"
    / "ghmc_combined_spatial_indicators.csv"
)

OUTPUT_GPKG = (
    PROJECT_DIR / "data" / "population"
    / "ghmc_population_enriched.gpkg"
)

# Load datasets
population = pd.read_csv(POPULATION_PATH)
facilities = pd.read_csv(FACILITY_PATH)
reference = gpd.read_file(REFERENCE_PATH)

# Validate identifiers
assert population["sample_id"].is_unique
assert facilities["sample_id"].is_unique
assert reference["sample_id"].is_unique

# Merge using sample_id
combined = population.merge(
    facilities,
    on="sample_id",
    how="left",
    validate="one_to_one"
)

print("========== MERGE VALIDATION ==========")
print("Population rows:", len(population))
print("Facility rows:", len(facilities))
print("Combined rows:", len(combined))

print(
    "Missing facility indicators:",
    combined.filter(
        regex="_500m$|_1000m$|_nearest_m$"
    ).isna().sum().sum()
)

# Attach attributes to reference geometries
enriched = reference.merge(
    combined,
    on="sample_id",
    how="left",
    validate="one_to_one"
)

# Save outputs
combined.to_csv(OUTPUT_CSV, index=False)

enriched.to_file(
    OUTPUT_GPKG,
    layer="spatial_indicators",
    driver="GPKG"
)

print("\n========== COMBINED DATASET ==========")
print("Rows:", len(enriched))
print("Columns:", len(enriched.columns))

print("\nPopulation coverage status:")
print(enriched["status"].value_counts())

print("\nPopulation exposure:")
print(enriched["population_500m"].describe().round(2))

print("\nHealthcare proximity:")
print(
    enriched[
        ["healthcare_500m", "healthcare_1000m",
         "healthcare_nearest_m"]
    ].describe().round(2)
)

print("\nSaved CSV:", OUTPUT_CSV)
print("Saved GeoPackage:", OUTPUT_GPKG)
