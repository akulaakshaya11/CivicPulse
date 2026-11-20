
import geopandas as gpd
import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

REFERENCE_PATH = (
    PROJECT_DIR / "data" / "boundary"
    / "ghmc_reference_points.gpkg"
)

FACILITY_PATH = (
    PROJECT_DIR / "data" / "facilities"
    / "Hyderabad_Selected_Civic_Facilities.gpkg"
)

OUTPUT_PATH = (
    PROJECT_DIR / "data" / "facilities"
    / "ghmc_facility_proximity.csv"
)

CRS = "EPSG:32644"
RADII = [500, 1000]

# Load datasets
points = gpd.read_file(REFERENCE_PATH)
facilities = gpd.read_file(FACILITY_PATH)

# Project both datasets into metres
points = points.to_crs(CRS)
facilities = facilities.to_crs(CRS)

# Keep only valid, non-empty geometries
facilities = facilities[
    facilities.geometry.notna()
    & (~facilities.geometry.is_empty)
    & facilities.geometry.is_valid
].copy()

categories = [
    "healthcare",
    "education",
    "emergency",
    "community",
    "public_transport"
]

# Preserve the original reference point order
results = pd.DataFrame({
    "sample_id": points["sample_id"].values
})

# Calculate counts and nearest distance category by category
for category in categories:

    print(f"\nProcessing: {category}")

    category_facilities = facilities[
        facilities["facility_category"] == category
    ].copy()

    # Count facilities inside each radius
    for radius in RADII:

        buffers = points[["sample_id", "geometry"]].copy()
        buffers["geometry"] = buffers.geometry.buffer(radius)

        joined = gpd.sjoin(
            buffers,
            category_facilities[["osm_id", "osm_type", "geometry"]],
            how="left",
            predicate="intersects"
        )

        counts = (
            joined.groupby("sample_id")["osm_id"]
            .count()
        )

        column = f"{category}_{radius}m"

        results[column] = (
            results["sample_id"]
            .map(counts)
            .fillna(0)
            .astype(int)
        )

    # Calculate distance to nearest mapped facility
    nearest = gpd.sjoin_nearest(
        points[["sample_id", "geometry"]],
        category_facilities[["geometry"]],
        how="left",
        distance_col="distance_m"
    )

    nearest_distances = (
        nearest.groupby("sample_id")["distance_m"]
        .min()
    )

    results[f"{category}_nearest_m"] = (
        results["sample_id"].map(nearest_distances)
    )

    print("Facilities:", len(category_facilities))
    print("Completed:", category)

# Save output
results.to_csv(OUTPUT_PATH, index=False)

print("\n========== PROXIMITY ANALYSIS COMPLETE ==========")
print("Reference points:", len(results))
print("Output columns:", results.columns.tolist())
print("\nSummary:")
print(results.describe().round(2).to_string())

print("\nSaved to:", OUTPUT_PATH)
