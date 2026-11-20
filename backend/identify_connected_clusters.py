
import geopandas as gpd
import pandas as pd
import numpy as np

from pathlib import Path
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

PROJECT_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    PROJECT_DIR / "data" / "population"
    / "ghmc_underserved_lisa.gpkg"
)

OUTPUT_GPKG = (
    PROJECT_DIR / "data" / "population"
    / "ghmc_connected_underserved_clusters.gpkg"
)

OUTPUT_CSV = (
    PROJECT_DIR / "data" / "population"
    / "ghmc_connected_cluster_summary.csv"
)

DISTANCE_THRESHOLD = 750

# Load LISA results
gdf = gpd.read_file(INPUT_PATH)

# Select statistically significant High-High locations
hh = gdf[
    gdf["cluster_type"] == "High-High"
].copy()

# Use projected coordinates in metres
hh = hh.to_crs("EPSG:32644").reset_index(drop=True)

print("High-High locations:", len(hh))

if len(hh) == 0:
    raise ValueError("No High-High locations found.")

# Extract point coordinates
coordinates = np.column_stack([
    hh.geometry.x,
    hh.geometry.y
])

# Find neighbouring points within 750m
tree = cKDTree(coordinates)
pairs = list(
    tree.query_pairs(r=DISTANCE_THRESHOLD)
)

# Build an undirected graph
if pairs:
    edges = np.array(pairs)
    rows = np.concatenate([edges[:, 0], edges[:, 1]])
    cols = np.concatenate([edges[:, 1], edges[:, 0]])

    graph = coo_matrix(
        (
            np.ones(len(rows)),
            (rows, cols)
        ),
        shape=(len(hh), len(hh))
    ).tocsr()
else:
    graph = coo_matrix(
        (len(hh), len(hh))
    ).tocsr()

# Find connected components
number_of_clusters, labels = connected_components(
    graph,
    directed=False
)

hh["cluster_id"] = labels + 1

# Calculate cluster sizes
hh["cluster_size"] = (
    hh.groupby("cluster_id")["cluster_id"]
    .transform("size")
)

summary = (
    hh.groupby("cluster_id")
    .agg(
        number_of_locations=("sample_id", "count"),
        avg_underserved_categories=(
            "underserved_category_count", "mean"
        ),
        max_underserved_categories=(
            "underserved_category_count", "max"
        )
    )
    .reset_index()
    .sort_values(
        "number_of_locations",
        ascending=False
    )
)

summary.to_csv(OUTPUT_CSV, index=False)

hh.to_file(
    OUTPUT_GPKG,
    layer="connected_clusters",
    driver="GPKG"
)

print("\n========== CONNECTED CLUSTER RESULTS ==========")

print("Number of connected components:", number_of_clusters)

print("\nCluster size distribution:")
print(
    summary["number_of_locations"]
    .value_counts()
    .sort_index()
)

print("\nLargest 10 clusters:")
print(summary.head(10).to_string(index=False))

print("\nTotal High-High locations:", len(hh))
print("Saved GeoPackage:", OUTPUT_GPKG)
print("Saved summary CSV:", OUTPUT_CSV)
