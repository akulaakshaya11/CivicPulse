
import geopandas as gpd
import pandas as pd

from pathlib import Path
from libpysal.weights import DistanceBand
from esda.moran import Moran

PROJECT_DIR = Path(__file__).resolve().parent.parent

INPUT_CSV = (
    PROJECT_DIR / "data" / "population"
    / "ghmc_underserved_analysis.csv"
)

REFERENCE_PATH = (
    PROJECT_DIR / "data" / "boundary"
    / "ghmc_reference_points.gpkg"
)

OUTPUT_PATH = (
    PROJECT_DIR / "data" / "population"
    / "ghmc_underserved_clusters.gpkg"
)

# Load reliable population observations
df = pd.read_csv(INPUT_CSV)

# Load reference point geometries
points = gpd.read_file(REFERENCE_PATH)

# Merge indicators with geometries
gdf = points.merge(
    df,
    on="sample_id",
    how="inner",
    validate="one_to_one"
)

# Use projected coordinates in metres
gdf = gdf.to_crs("EPSG:32644")

# Spatial variable: number of underserved categories
y = gdf["underserved_category_count"].to_numpy()

print("Observations:", len(gdf))
print("Mean underserved category count:", round(y.mean(), 3))
print("Locations with 3+ categories:", (y >= 3).sum())
print("Locations with all 5 categories:", (y == 5).sum())

# Create spatial weights using a 750m distance band
weights = DistanceBand.from_dataframe(
    gdf,
    threshold=750,
    binary=True,
    silence_warnings=True
)

weights.transform = "R"

# Calculate Global Moran's I
moran = Moran(
    y,
    weights,
    permutations=999
)

print("\n========== GLOBAL MORAN'S I ==========")
print("Moran's I:", round(moran.I, 4))
print("Expected I:", round(moran.EI, 4))
print("Z-score:", round(moran.z_norm, 4))
print("Permutation p-value:", moran.p_sim)

# Save the data for QGIS
gdf.to_file(
    OUTPUT_PATH,
    layer="underserved_clusters",
    driver="GPKG"
)

print("\nSaved to:", OUTPUT_PATH)
