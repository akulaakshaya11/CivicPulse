
import geopandas as gpd
import numpy as np
from pathlib import Path
from libpysal.weights import DistanceBand
from esda.moran import Moran_Local
from scipy.stats import false_discovery_control

PROJECT_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = (
    PROJECT_DIR / "data" / "population"
    / "ghmc_population_enriched.gpkg"
)

OUTPUT_PATH = (
    PROJECT_DIR / "data" / "population"
    / "ghmc_population_lisa.gpkg"
)

# Load data
points = gpd.read_file(DATA_PATH, layer="population_analysis")
points = points.to_crs(epsg=32644)

values = points["low_coverage"].astype(int).values

coordinates = np.column_stack([
    points.geometry.x,
    points.geometry.y
])

# Create 750m spatial weights
weights = DistanceBand(
    coordinates,
    threshold=750,
    binary=True,
    silence_warnings=True
)

weights.transform = "R"

# Calculate Local Moran's I
np.random.seed(42)

lisa = Moran_Local(
    values,
    weights,
    permutations=999
)

# Store results
points["local_moran_I"] = lisa.Is
points["local_p_value"] = lisa.p_sim
points["quadrant"] = lisa.q

# Correct for multiple local statistical tests
p_values = points["local_p_value"].to_numpy().copy()

# Exclude isolated points from significance testing
island_indices = [
    points.index.get_loc(i) for i in weights.islands
]

p_values[island_indices] = 1.0

adjusted_p = false_discovery_control(
    p_values,
    method="bh"
)

points["adjusted_p_value"] = adjusted_p

# Classify significant locations
labels = {
    1: "High-High",
    2: "Low-High",
    3: "Low-Low",
    4: "High-Low"
}

points["cluster_type"] = [
    labels[q] if p < 0.05 else "Not Significant"
    for q, p in zip(points["quadrant"], adjusted_p)
]

# Export results
points.to_file(
    OUTPUT_PATH,
    layer="local_clusters",
    driver="GPKG"
)

print("\n========== LOCAL MORAN'S I RESULTS ==========")

print("\nCluster counts:")
print(points["cluster_type"].value_counts())

print("\nSignificant low-coverage hotspots:")
hotspots = points[
    (points["cluster_type"] == "High-High")
]

print("Number of hotspots:", len(hotspots))

print("\nOutput saved to:", OUTPUT_PATH)
