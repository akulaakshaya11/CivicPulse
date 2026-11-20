
import geopandas as gpd
import numpy as np
from pathlib import Path
from libpysal.weights import DistanceBand
from esda.moran import Moran

# Project paths
PROJECT_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = (
    PROJECT_DIR
    / "data"
    / "population"
    / "ghmc_population_enriched.gpkg"
)

# Load spatial dataset
points = gpd.read_file(DATA_PATH, layer="population_analysis")

# Ensure projected CRS (metres)
points = points.to_crs(epsg=32644)

# Convert low_coverage boolean values into 0 and 1
points["low_coverage"] = points["low_coverage"].astype(int)

# Extract coordinates
coordinates = np.column_stack([
    points.geometry.x,
    points.geometry.y
])

# Test multiple neighbourhood distances
thresholds = [600, 750, 1000]

np.random.seed(42)

print("\n========== MORAN'S I SENSITIVITY ANALYSIS ==========")

values = points["low_coverage"].values

for threshold in thresholds:

    weights = DistanceBand(
        coordinates,
        threshold=threshold,
        binary=True,
        silence_warnings=True
    )

    weights.transform = "R"

    moran = Moran(
        values,
        weights,
        permutations=999
    )

    print(f"\nDistance threshold: {threshold} metres")
    print("Moran's I:", round(moran.I, 4))
    print("Expected I:", round(moran.EI, 4))
    print("P-value:", round(moran.p_sim, 6))
    print("Z-score:", round(moran.z_sim, 4))
    print("Neighbour pairs:", weights.s0)
    print("Isolated points:", len(weights.islands))

    if moran.p_sim < 0.05 and moran.I > moran.EI:
        print("Interpretation: Significant positive spatial autocorrelation.")
    elif moran.p_sim < 0.05:
        print("Interpretation: Significant negative spatial autocorrelation.")
    else:
        print("Interpretation: No significant spatial autocorrelation.")
