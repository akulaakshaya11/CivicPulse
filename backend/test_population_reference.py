
import geopandas as gpd

from population_exposure import calculate_population_exposure

# Load reference points
points = gpd.read_file(
    "../data/boundary/ghmc_reference_points.gpkg"
)

# Convert coordinates to WGS84
points = points.to_crs("EPSG:4326")

print("Testing population exposure on 5 points...\n")

for _, row in points.head(5).iterrows():

    latitude = row.geometry.y
    longitude = row.geometry.x
    sample_id = int(row["sample_id"])

    print(f"\nReference point: {sample_id}")

    exposure = calculate_population_exposure(
        sample_id,
        latitude,
        longitude
    )

    print(
        "500m population exposure:",
        round(exposure[500]["population"], 2)
    )

print("\nTest completed!")
