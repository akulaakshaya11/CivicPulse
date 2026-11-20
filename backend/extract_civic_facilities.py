
import geopandas as gpd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    PROJECT_DIR / "data" / "facilities"
    / "Hyderabad_Civic_Facilities.gpkg"
)

OUTPUT_PATH = (
    PROJECT_DIR / "data" / "facilities"
    / "Hyderabad_Selected_Civic_Facilities.gpkg"
)

gdf = gpd.read_file(INPUT_PATH)

# Candidate categories based on the available OSM tags
category_rules = {
    "healthcare": (
        gdf["amenity"].isin([
            "hospital", "health_post", "clinic",
            "pharmacy", "doctors", "dentist"
        ])
        | gdf["healthcare"].isin([
            "hospital", "clinic", "pharmacy",
            "doctor", "dentist", "blood_bank"
        ])
    ),

    "education": gdf["amenity"].isin([
        "school", "college", "university",
        "kindergarten", "language_school", "childcare"
    ]),

    "emergency": (
        gdf["amenity"].isin(["police", "fire_station"])
        | gdf["emergency"].isin(["ambulance_station"])
    ),

    "community": gdf["amenity"].isin([
        "community_centre", "library", "childcare"
    ]),

    "public_transport": (
        gdf["amenity"].isin(["bus_station"])
        | gdf["public_transport"].isin(["station", "halt"])
        | gdf["railway"].isin(["station", "halt"])
    )
}

selected = []

for category, condition in category_rules.items():
    subset = gdf.loc[condition].copy()
    subset["facility_category"] = category
    selected.append(subset)

result = gpd.GeoDataFrame(
    gpd.pd.concat(selected, ignore_index=True),
    geometry="geometry",
    crs=gdf.crs
)

# Remove duplicate OSM objects within the same category
result = result.drop_duplicates(
    subset=["osm_type", "osm_id", "facility_category"]
)

# Keep only point and polygon features for now.
# We'll handle line geometries separately if needed.
result = result[
    result.geometry.geom_type.isin(["Point", "Polygon", "MultiPolygon"])
].copy()

result.to_file(
    OUTPUT_PATH,
    layer="selected_facilities",
    driver="GPKG"
)

print("========== SELECTED FACILITIES ==========")
print("Total:", len(result))
print("\nCategory counts:")
print(result["facility_category"].value_counts())

print("\nGeometry counts:")
print(result.geometry.geom_type.value_counts())

print("\nSaved to:", OUTPUT_PATH)
