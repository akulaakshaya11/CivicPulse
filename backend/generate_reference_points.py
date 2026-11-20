
import geopandas as gpd
import numpy as np
from shapely.geometry import Point

# Load GHMC boundary
boundary_path = "../data/boundary/ghmc_boundary.gpkg"
boundary = gpd.read_file(boundary_path)

# Project to UTM 44N
boundary = boundary.to_crs("EPSG:32644")

# Get the complete GHMC geometry
ghmc_polygon = boundary.geometry.union_all()

# Get projected bounds
min_x, min_y, max_x, max_y = ghmc_polygon.bounds

# Grid spacing: 500 metres
grid_spacing = 500

points = []

# Generate grid points at cell centres
x_values = np.arange(
    min_x + grid_spacing / 2,
    max_x,
    grid_spacing
)

y_values = np.arange(
    min_y + grid_spacing / 2,
    max_y,
    grid_spacing
)

for x in x_values:
    for y in y_values:
        point = Point(x, y)

        # Retain points inside GHMC
        if ghmc_polygon.covers(point):
            points.append(point)

# Convert to GeoDataFrame
reference_points = gpd.GeoDataFrame(
    {"sample_id": range(1, len(points) + 1)},
    geometry=points,
    crs="EPSG:32644"
)

# Save reference points
output_path = "../data/boundary/ghmc_reference_points.gpkg"

reference_points.to_file(
    output_path,
    driver="GPKG",
    layer="reference_points"
)

print("Reference grid generated successfully!")
print("Grid spacing:", grid_spacing, "metres")
print("Total reference points:", len(reference_points))
print("CRS:", reference_points.crs)
print("Saved at:", output_path)
