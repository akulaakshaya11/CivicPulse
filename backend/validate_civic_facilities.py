
import geopandas as gpd
import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

PATH = (
    PROJECT_DIR / "data" / "facilities"
    / "Hyderabad_Selected_Civic_Facilities.gpkg"
)

gdf = gpd.read_file(PATH)

print("========== VALIDATION ==========")

print("Total records:", len(gdf))
print("Missing OSM IDs:", gdf["osm_id"].isna().sum())
print("Missing names:", gdf["name"].isna().sum())

print("\nDuplicate OSM objects across categories:")
print(
    gdf.groupby(["osm_type", "osm_id"])["facility_category"]
    .nunique()
    .gt(1)
    .sum()
)

print("\nDuplicate OSM objects within categories:")
print(
    gdf.duplicated(
        subset=["osm_type", "osm_id", "facility_category"]
    ).sum()
)

print("\nInvalid geometries:", (~gdf.geometry.is_valid).sum())
print("Empty geometries:", gdf.geometry.is_empty.sum())

print("\nCategory-wise missing names:")
print(
    gdf.assign(name_missing=gdf["name"].isna())
    .groupby("facility_category")["name_missing"]
    .agg(["count", "sum"])
)

print("\nCRS:", gdf.crs)
