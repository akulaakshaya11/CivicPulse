
from pathlib import Path

import geopandas as gpd
import psycopg
from dotenv import load_dotenv
import os

load_dotenv()

DATA_DIR = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "facilities"
)

# Explicit categories: do not import every map feature.
AMENITY_CATEGORIES = {
    "hospital": "healthcare",
    "clinic": "healthcare",
    "health_post": "healthcare",
    "doctors": "healthcare",
    "pharmacy": "healthcare",
    "dentist": "healthcare",
    "blood_bank": "healthcare",
    "blood_donation": "healthcare",
    "laboratory": "healthcare",
    "school": "education",
    "college": "education",
    "university": "education",
    "kindergarten": "education",
    "language_school": "education",
    "police": "emergency",
    "fire_station": "emergency",
    "ambulance_station": "emergency",
    "community_centre": "community",
    "library": "community",
}

HEALTHCARE_CATEGORIES = {
    "hospital",
    "clinic",
    "health_post",
    "doctor",
    "pharmacy",
    "dentist",
    "blood_bank",
    "blood_donation",
    "laboratory",
    "ambulance_station",
}


def get_db_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def classify(tags):
    amenity = str(tags.get("amenity", "")).strip().lower()
    healthcare = str(tags.get("healthcare", "")).strip().lower()
    emergency = str(tags.get("emergency", "")).strip().lower()

    # Prefer specific, recognized facility tags.
    if amenity in AMENITY_CATEGORIES:
        return AMENITY_CATEGORIES[amenity]

    if healthcare in HEALTHCARE_CATEGORIES:
        return "healthcare"

    if emergency == "ambulance_station":
        return "emergency"

    # Avoid interpreting generic yes/no tags as a facility type.
    return None


def main():
    files = list(DATA_DIR.glob("*.gpkg"))

    if not files:
        raise FileNotFoundError(
            f"No GeoPackage found in {DATA_DIR}"
        )

    gpkg_path = files[0]
    layers = gpd.list_layers(gpkg_path)
    layer_name = layers["name"].iloc[0]

    print(f"Reading: {gpkg_path.name}")
    print(f"Layer: {layer_name}")

    gdf = gpd.read_file(gpkg_path, layer=layer_name)

    required = {"osm_id", "osm_type", "geometry"}
    missing = required - set(gdf.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    imported = 0
    skipped = 0
    category_counts = {}

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for _, feature in gdf.iterrows():
                if feature.geometry is None:
                    skipped += 1
                    continue

                if feature.geometry.geom_type != "Point":
                    skipped += 1
                    continue

                if feature.geometry.is_empty:
                    skipped += 1
                    continue

                lon = float(feature.geometry.x)
                lat = float(feature.geometry.y)

                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    skipped += 1
                    continue

                tags = feature.to_dict()
                category = classify(tags)

                if category is None:
                    skipped += 1
                    continue

                osm_id = str(feature["osm_id"])
                osm_type = str(feature["osm_type"])
                source_id = f"{osm_type}/{osm_id}"

                name_value = feature.get("name")
                name = (
                    str(name_value).strip()
                    if name_value is not None
                    and not gpd.pd.isna(name_value)
                    else None
                )

                cur.execute(
                    """
                    INSERT INTO civic_facilities (
                        name,
                        category,
                        latitude,
                        longitude,
                        data_source,
                        source_id,
                        verified
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, FALSE)
                    ON CONFLICT (data_source, source_id)
                    DO NOTHING
                    """,
                    (
                        name,
                        category,
                        lat,
                        lon,
                        "OpenStreetMap",
                        source_id,
                    ),
                )

                if cur.rowcount:
                    imported += 1
                    category_counts[category] = (
                        category_counts.get(category, 0) + 1
                    )

        conn.commit()

    print(f"New facilities inserted: {imported}")
    print(f"Features skipped: {skipped}")
    print("All imported records remain unverified.")
    print("Newly inserted facilities by category:")

    for category, count in sorted(category_counts.items()):
        print(f"  {category}: {count}")


if __name__ == "__main__":
    main()
