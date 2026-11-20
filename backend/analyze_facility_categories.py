
import geopandas as gpd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

FACILITY_PATH = (
    PROJECT_DIR / "data" / "facilities"
    / "Hyderabad_Civic_Facilities.gpkg"
)

facilities = gpd.read_file(FACILITY_PATH)

print("\n========== GEOMETRY TYPES ==========")
print(facilities.geometry.geom_type.value_counts())

columns = [
    "amenity",
    "healthcare",
    "emergency",
    "shop",
    "building",
    "public_transport",
    "highway",
    "railway"
]

for column in columns:
    print(f"\n========== {column.upper()} ==========")

    values = facilities[column].dropna().value_counts()

    print("Unique values:", len(values))
    print(values.head(20).to_string())

print("\nTotal features:", len(facilities))
