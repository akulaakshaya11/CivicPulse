
from pathlib import Path
import geopandas as gpd

# Locate the facilities folder automatically
data_dir = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "facilities"
)

files = list(data_dir.glob("*.gpkg"))

if not files:
    raise FileNotFoundError(
        f"No .gpkg file found in: {data_dir}"
    )

gpkg_path = files[0]

print("File:", gpkg_path.name)
print("\nAvailable layers:")

layers = gpd.list_layers(gpkg_path)
print(layers.to_string(index=False))

for layer in layers["name"]:
    print(f"\n--- Layer: {layer} ---")

    gdf = gpd.read_file(
        gpkg_path,
        layer=layer,
        rows=5,
    )

    print("Columns:", list(gdf.columns))
    print("CRS:", gdf.crs)
    print("Geometry types:", gdf.geom_type.unique())
    print("\nSample records:")
    print(gdf.to_string(index=False))


print("\n========== FACILITY CATEGORY SUMMARY ==========")

gdf = gpd.read_file(gpkg_path, layer=layers["name"].iloc[0])

for column in [
    "amenity",
    "healthcare",
    "emergency",
    "public_transport",
    "highway",
    "building",
]:
    if column in gdf.columns:
        print(f"\n{column}:")
        counts = gdf[column].dropna().astype(str).value_counts()
        print(counts.head(20).to_string() if not counts.empty else "No tagged values")

print("\nTotal features:", len(gdf))
print("Features with names:", gdf["name"].notna().sum())
print("Features with valid geometry:", gdf.geometry.notna().sum())

