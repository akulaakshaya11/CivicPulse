
import requests
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
import os
import time

load_dotenv()

# Approximate Hyderabad bounding box:
# south, west, north, east
SOUTH, WEST, NORTH, EAST = 17.20, 78.20, 17.60, 78.65

# Primary Overpass endpoint
OVERPASS_URL = "https://overpass.kumi.systems/api/interpreter"

QUERY = f"""
[out:json][timeout:60];
(
  nwr["amenity"~"^(hospital|clinic|doctors|school|college|university|pharmacy|fire_station)$"](
    {SOUTH},{WEST},{NORTH},{EAST}
  );
);
out center tags;
"""


def get_db_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        row_factory=dict_row,
    )


def main():
    print("Fetching mapped Hyderabad facilities from OpenStreetMap...")

    response = None

    # Retry temporary Overpass server errors
    for attempt in range(4):
        try:
            response = requests.post(
                OVERPASS_URL,
                data={"data": QUERY},
                headers={
                    "User-Agent": "CivicImpactStudentProject/1.0",
                    "Accept": "application/json",
                },
                timeout=180,
            )

            if response.ok:
                break

            print(
                f"Attempt {attempt + 1}: "
                f"HTTP {response.status_code}"
            )
            print("Server response:", response.text[:500])

            if response.status_code not in (
                429, 500, 502, 503, 504
            ):
                response.raise_for_status()

        except requests.RequestException as exc:
            print(f"Attempt {attempt + 1} failed: {exc}")

        if attempt < 3:
            wait_seconds = 10 * (2 ** attempt)
            print(f"Retrying in {wait_seconds} seconds...")
            time.sleep(wait_seconds)

    if response is None or not response.ok:
        raise RuntimeError(
            "Overpass is unavailable. Try again later. "
            "No database inserts were performed."
        )

    elements = response.json().get("elements", [])
    print(f"Received {len(elements)} mapped features.")

    imported = 0
    skipped = 0

    # Insert facilities into PostgreSQL
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for element in elements:
                tags = element.get("tags", {})

                point = (
                    element
                    if "lat" in element
                    else element.get("center", {})
                )

                lat = point.get("lat")
                lon = point.get("lon")

                if lat is None or lon is None:
                    skipped += 1
                    continue

                amenity = tags.get("amenity")

                if not amenity:
                    skipped += 1
                    continue

                source_id = f"{element['type']}/{element['id']}"
                name = tags.get("name")

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
                        amenity,
                        lat,
                        lon,
                        "OpenStreetMap",
                        source_id,
                    ),
                )

                if cur.rowcount > 0:
                    imported += 1

        conn.commit()

    print(f"New facilities inserted: {imported}")
    print(f"Features skipped: {skipped}")
    print("Facilities remain unverified pending validation.")
    print("Data source: OpenStreetMap contributors (ODbL).")


if __name__ == "__main__":
    main()
