
import geopandas as gpd
import numpy as np

from pathlib import Path
from libpysal.weights import DistanceBand
from esda.moran import Moran_Local
from scipy.stats import false_discovery_control

PROJECT_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    PROJECT_DIR / "data" / "population"
    / "ghmc_underserved_clusters.gpkg"
)

OUTPUT_PATH = (
    PROJECT_DIR / "data" / "population"
    / "ghmc_underserved_lisa.gpkg"
)

gdf = gpd.read_file(INPUT_PATH)

# Variable: number of underserved categories
y = gdf["underserved_category_count"].to_numpy()

# Spatial weights
weights = DistanceBand.from_dataframe(
    gdf,
    threshold=750,
    binary=True,
    silence_warnings=True
)

weights.transform = "R"

# Local Moran's I
lisa = Moran_Local(
    y,
    weights,
    permutations=999
)

# Multiple-testing correction
adjusted_p = false_discovery_control(
    lisa.p_sim,
    method="bh"
)

# Identify significant locations
significant = adjusted_p < 0.05

# Quadrant classification
# 1 = High-High
# 2 = Low-High
# 3 = Low-Low
# 4 = High-Low

labels = {
    1: "High-High",
    2: "Low-High",
    3: "Low-Low",
    4: "High-Low"
}

gdf["local_moran"] = lisa.Is
gdf["p_value"] = lisa.p_sim
gdf["adjusted_p"] = adjusted_p
gdf["significant"] = significant

gdf["cluster_type"] = [
    labels[q] if sig else "Not Significant"
    for q, sig in zip(lisa.q, significant)
]

print("\n========== LISA CLUSTER RESULTS ==========")

print(
    gdf["cluster_type"]
    .value_counts()
)

print("\nSignificant locations:", significant.sum())

print(
    "High-High locations:",
    (gdf["cluster_type"] == "High-High").sum()
)

gdf.to_file(
    OUTPUT_PATH,
    layer="underserved_lisa",
    driver="GPKG"
)

print("\nSaved:", OUTPUT_PATH)
