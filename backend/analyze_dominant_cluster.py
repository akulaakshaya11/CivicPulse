
import geopandas as gpd
import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    PROJECT_DIR / "data" / "population"
    / "ghmc_connected_underserved_clusters.gpkg"
)

OUTPUT_PATH = (
    PROJECT_DIR / "data" / "population"
    / "dominant_cluster_analysis.csv"
)

gdf = gpd.read_file(INPUT_PATH)

# Select the largest connected cluster
largest_size = gdf["cluster_size"].max()

cluster = gdf[
    gdf["cluster_size"] == largest_size
].copy()

print("========== DOMINANT CLUSTER ==========")
print("Number of locations:", len(cluster))
print("Cluster ID:", cluster["cluster_id"].iloc[0])

print("\n========== UNDERSERVED CATEGORY COUNTS ==========")

print(
    cluster["underserved_category_count"]
    .value_counts()
    .sort_index()
)

categories = [
    "healthcare",
    "education",
    "emergency",
    "community",
    "public_transport"
]

print("\n========== FACILITY GAPS ==========")

for category in categories:

    col_500 = f"{category}_500m"
    col_1000 = f"{category}_1000m"

    if col_500 not in cluster.columns:
        print(f"{category}: missing 500m column")
        continue

    print(f"\n{category.upper()}")
    print("Zero within 500m:", (cluster[col_500] == 0).sum())

    if col_1000 in cluster.columns:
        print("Zero within 1km:", (cluster[col_1000] == 0).sum())

    nearest_col = f"{category}_nearest_m"

    if nearest_col in cluster.columns:
        print(
            "Median nearest distance:",
            round(cluster[nearest_col].median(), 2),
            "metres"
        )

print("\n========== POPULATION EXPOSURE ==========")

if "population_500m" in cluster.columns:
    print(
        cluster["population_500m"].describe()
    )

print("\n========== GEOGRAPHICAL EXTENT ==========")

projected = cluster.to_crs("EPSG:32644")
minx, miny, maxx, maxy = projected.total_bounds

print("Bounding-box width:", round((maxx-minx)/1000, 2), "km")
print("Bounding-box height:", round((maxy-miny)/1000, 2), "km")

cluster.drop(columns="geometry").to_csv(
    OUTPUT_PATH,
    index=False
)

print("\nSaved:", OUTPUT_PATH)
