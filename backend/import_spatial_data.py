
import os
import pandas as pd
import psycopg
from dotenv import load_dotenv

load_dotenv()

CSV_PATH = "../data/population/ghmc_combined_spatial_indicators.csv"

def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "civic_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
    )


def import_spatial_data():
    print("Reading spatial indicators CSV...")

    df = pd.read_csv(CSV_PATH)

    print(f"Total reference points: {len(df)}")

    with get_connection() as conn:
        with conn.cursor() as cur:

            # Ensure PostGIS is available
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

            # Create a separate table for spatial indicators
            cur.execute("""
                CREATE TABLE IF NOT EXISTS spatial_reference_points (
                    sample_id INTEGER PRIMARY KEY,
                    latitude DOUBLE PRECISION NOT NULL,
                    longitude DOUBLE PRECISION NOT NULL,
                    population_500m DOUBLE PRECISION,
                    valid_pixels INTEGER,
                    coverage_percent DOUBLE PRECISION,
                    status TEXT,

                    healthcare_500m INTEGER,
                    healthcare_1000m INTEGER,
                    healthcare_nearest_m DOUBLE PRECISION,

                    education_500m INTEGER,
                    education_1000m INTEGER,
                    education_nearest_m DOUBLE PRECISION,

                    emergency_500m INTEGER,
                    emergency_1000m INTEGER,
                    emergency_nearest_m DOUBLE PRECISION,

                    community_500m INTEGER,
                    community_1000m INTEGER,
                    community_nearest_m DOUBLE PRECISION,

                    public_transport_500m INTEGER,
                    public_transport_1000m INTEGER,
                    public_transport_nearest_m DOUBLE PRECISION,

                    location GEOGRAPHY(POINT, 4326)
                );
            """)

            # Insert or update reference points
            insert_sql = """
                INSERT INTO spatial_reference_points (
                    sample_id, latitude, longitude,
                    population_500m, valid_pixels,
                    coverage_percent, status,

                    healthcare_500m, healthcare_1000m,
                    healthcare_nearest_m,

                    education_500m, education_1000m,
                    education_nearest_m,

                    emergency_500m, emergency_1000m,
                    emergency_nearest_m,

                    community_500m, community_1000m,
                    community_nearest_m,

                    public_transport_500m, public_transport_1000m,
                    public_transport_nearest_m,

                    location
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                )
                ON CONFLICT (sample_id) DO UPDATE SET
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    population_500m = EXCLUDED.population_500m,
                    valid_pixels = EXCLUDED.valid_pixels,
                    coverage_percent = EXCLUDED.coverage_percent,
                    status = EXCLUDED.status,
                    healthcare_500m = EXCLUDED.healthcare_500m,
                    healthcare_1000m = EXCLUDED.healthcare_1000m,
                    healthcare_nearest_m = EXCLUDED.healthcare_nearest_m,
                    education_500m = EXCLUDED.education_500m,
                    education_1000m = EXCLUDED.education_1000m,
                    education_nearest_m = EXCLUDED.education_nearest_m,
                    emergency_500m = EXCLUDED.emergency_500m,
                    emergency_1000m = EXCLUDED.emergency_1000m,
                    emergency_nearest_m = EXCLUDED.emergency_nearest_m,
                    community_500m = EXCLUDED.community_500m,
                    community_1000m = EXCLUDED.community_1000m,
                    community_nearest_m = EXCLUDED.community_nearest_m,
                    public_transport_500m = EXCLUDED.public_transport_500m,
                    public_transport_1000m = EXCLUDED.public_transport_1000m,
                    public_transport_nearest_m = EXCLUDED.public_transport_nearest_m,
                    location = EXCLUDED.location;
            """

            columns = [
                "sample_id", "latitude", "longitude",
                "population_500m", "valid_pixels",
                "coverage_percent", "status",
                "healthcare_500m", "healthcare_1000m",
                "healthcare_nearest_m",
                "education_500m", "education_1000m",
                "education_nearest_m",
                "emergency_500m", "emergency_1000m",
                "emergency_nearest_m",
                "community_500m", "community_1000m",
                "community_nearest_m",
                "public_transport_500m", "public_transport_1000m",
                "public_transport_nearest_m"
            ]

            df = df.astype(object).where(pd.notna(df), None)

            records = []

            for row in df[columns].itertuples(index=False, name=None):
                records.append(tuple(row) + (row[2], row[1]))

            cur.executemany(insert_sql, records)

            # Create spatial index
            cur.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_spatial_reference_points_location
                ON spatial_reference_points
                USING GIST (location);
            """)

        conn.commit()

    print("Spatial data import completed successfully!")
    print(f"Imported/updated {len(df)} reference points.")


if __name__ == "__main__":
    import_spatial_data()
