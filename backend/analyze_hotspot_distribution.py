
import geopandas as gpd
import pandas as pd
from pathlib import Path

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

# Select significant High-High hotspots
hotspots = points[
    points["cluster_type"] == "High-High"
].copy()

# Count hotspots by boundary distance
distance_order = [
    "0-500m",
    "500m-1km",
    "1-2km",
    "Above 2km"
]

summary = (
    hotspots["distance_group"]
    .value_counts()
    .reindex(distance_order, fill_value=0)
    .rename_axis("distance_group")
    .reset_index(name="hotspot_count")
)

# Calculate percentage
total_hotspots = len(hotspots)

summary["percentage"] = (
    summary["hotspot_count"] / total_hotspots * 100
).round(2)

print("\n========== HIGH-HIGH HOTSPOT DISTRIBUTION ==========")

print(summary.to_string(index=False))

print("\nTotal High-High hotspots:", total_hotspots)

# Calculate boundary vs interior distribution
boundary_hotspots = hotspots[
    hotspots["boundary_distance_m"] <= 1000
]

interior_hotspots = hotspots[
    hotspots["boundary_distance_m"] > 1000
]

print("\n========== BOUNDARY VS INTERIOR ==========")

print("Within 1 km of boundary:", len(boundary_hotspots))
print("More than 1 km inside:", len(interior_hotspots))

print(
    "Boundary percentage:",
    round(len(boundary_hotspots) / total_hotspots * 100, 2),
    "%"
)

print(
    "Interior percentage:",
    round(len(interior_hotspots) / total_hotspots * 100, 2),
    "%"
)

# Save summary
output_path = (
    PROJECT_DIR
    / "data"
    / "population"
    / "high_high_hotspot_distribution.csv"
)

summary.to_csv(output_path, index=False)

print("\nSummary saved to:", output_path)
