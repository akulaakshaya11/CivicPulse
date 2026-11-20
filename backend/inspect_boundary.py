import geopandas as gpd

file_path = "../data/boundary/ghmc_boundary.kml"

try:
    gdf = gpd.read_file(file_path, driver="KML")

    print("Number of features:", len(gdf))
    print("CRS:", gdf.crs)
    print("Geometry types:")
    print(gdf.geom_type.value_counts())

    print("\nBounds:")
    print(gdf.total_bounds)

    print("\nGeometry validity:")
    print(gdf.geometry.is_valid.value_counts())

    print("\nColumns:")
    print(gdf.columns.tolist())

except Exception as e:
    print("Error reading KML:", e)


print("\nFeature count:", len(gdf))
print("CRS:", gdf.crs)
print("Geometry types:")
print(gdf.geom_type.value_counts())

print("\nBounds:")
print(gdf.total_bounds)

print("\nGeometry validity:")
print(gdf.geometry.is_valid.value_counts())

print("\nNames:")
print(gdf[["Name", "admin_level", "boundary"]].head(10))

from pathlib import Path

output_path = "../data/boundary/ghmc_boundary.gpkg"

gdf.to_file(
    output_path,
    driver="GPKG",
    layer="ghmc_boundary"
)

print("\nGeoPackage created successfully!")
print("Saved at:", Path(output_path).resolve())