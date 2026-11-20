
import rasterio
from rasterio.mask import mask
from pathlib import Path
from shapely.geometry import Point, Polygon, mapping
from shapely import transform as transform_geometry
from pyproj import Transformer
import numpy as np

from main import get_connection


# -----------------------------------------
# 1. Configuration
# -----------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent

RASTER_PATH = (
    PROJECT_DIR
    / "data"
    / "population"
    / "ind_pop_2025_CN_100m_R2025A_v1.tif"
)

RADII = [250, 500, 1000]

BUFFER_CRS = "EPSG:32644"


# -----------------------------------------
# 2. Fetch issue coordinates
# -----------------------------------------

def get_issue_coordinates(issue_id):

    conn = get_connection()

    try:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    ST_Y(location::geometry),
                    ST_X(location::geometry)
                FROM civic_issues
                WHERE issue_id = %s
                """,
                (issue_id,)
            )

            result = cur.fetchone()

            if result is None:
                raise ValueError(
                    f"Issue ID {issue_id} not found."
                )

            latitude, longitude = result

            if latitude is None or longitude is None:
                raise ValueError(
                    "Issue coordinates are missing."
                )

            return float(latitude), float(longitude)

    finally:
        conn.close()


# -----------------------------------------
# 3. Calculate fractional pixel exposure
# -----------------------------------------

def calculate_population_exposure(
    issue_id,
    latitude,
    longitude
):

    if not RASTER_PATH.exists():
        raise FileNotFoundError(
            f"Raster not found: {RASTER_PATH}"
        )

    results = {}

    # Convert issue coordinates to UTM
    to_utm = Transformer.from_crs(
        "EPSG:4326",
        BUFFER_CRS,
        always_xy=True
    )

    # Open population raster
    with rasterio.open(RASTER_PATH) as src:

        # Convert UTM buffers to raster CRS
        to_raster = Transformer.from_crs(
            BUFFER_CRS,
            src.crs,
            always_xy=True
        )

        # Convert raster pixels back to UTM
        to_utm_from_raster = Transformer.from_crs(
            src.crs,
            BUFFER_CRS,
            always_xy=True
        )

        x, y = to_utm.transform(
            longitude,
            latitude
        )

        issue_point = Point(x, y)

        print("\n========== POPULATION EXPOSURE ==========")
        print("Issue ID:", issue_id)
        print("Latitude:", latitude)
        print("Longitude:", longitude)

        for radius in RADII:

            # Create buffer in metres
            buffer_utm = issue_point.buffer(
                radius,
                quad_segs=32
            )

            # Transform buffer to raster CRS
            buffer_raster = transform_geometry(
                buffer_utm,
                to_raster.transform,
                interleaved=False
            )

            try:

                # Include all pixels touching the buffer
                data, out_transform = mask(
                    src,
                    [mapping(buffer_raster)],
                    crop=True,
                    filled=False,
                    all_touched=True
                )

            except ValueError:

                results[radius] = {
                    "population": None,
                    "valid_pixels": 0,
                    "coverage_percent": 0,
                    "status": "Outside raster coverage"
                }

                continue

            population = data[0]

            total_population = 0.0
            valid_pixels = 0
            valid_area = 0.0

            # Buffer area in square metres
            buffer_area = buffer_utm.area

            # Examine each intersecting raster pixel
            for row in range(population.shape[0]):

                for col in range(population.shape[1]):

                    value = population[row, col]

                    if np.ma.is_masked(value):
                        continue

                    if not np.isfinite(value):
                        continue

                    # Construct pixel polygon
                    x1, y1 = out_transform * (col, row)
                    x2, y2 = out_transform * (col + 1, row)
                    x3, y3 = out_transform * (col + 1, row + 1)
                    x4, y4 = out_transform * (col, row + 1)

                    pixel_polygon = Polygon([
                        (x1, y1),
                        (x2, y2),
                        (x3, y3),
                        (x4, y4)
                    ])

                    # Calculate intersection in raster CRS
                    intersection = pixel_polygon.intersection(
                        buffer_raster
                    )

                    if intersection.is_empty:
                        continue

                    # Transform pixel polygon into UTM
                    pixel_utm = transform_geometry(
                        pixel_polygon,
                        to_utm_from_raster.transform,
                        interleaved=False
                    )

                    # Transform intersection into UTM
                    intersection_utm = transform_geometry(
                        intersection,
                        to_utm_from_raster.transform,
                        interleaved=False
                    )

                    if pixel_utm.area == 0:
                        continue

                    # Fraction of pixel inside buffer
                    fraction = (
                        intersection_utm.area
                        / pixel_utm.area
                    )

                    fraction = min(
                        1.0,
                        max(0.0, fraction)
                    )

                    # Estimate population contribution
                    total_population += (
                        float(value) * fraction
                    )

                    # Track valid area in square metres
                    valid_area += intersection_utm.area
                    valid_pixels += 1

            # Calculate valid raster coverage
            coverage_percent = (
                valid_area / buffer_area * 100
                if buffer_area > 0
                else 0
            )

            coverage_percent = min(
                100.0,
                coverage_percent
            )

            # -----------------------------------------
            # 4. Classify data coverage quality
            # -----------------------------------------

            if valid_pixels == 0:
                status = "No valid population data"

            elif coverage_percent >= 95:
                status = "Success"

            elif coverage_percent >= 90:
                status = "Partial Coverage"

            else:
                status = "Low Coverage"

            # Store results
            results[radius] = {
                "population": round(total_population, 2),
                "valid_pixels": valid_pixels,
                "coverage_percent": round(
                    coverage_percent, 2
                ),
                "status": status
            }

            # Display results
            print(f"\nRadius: {radius} metres")

            print(
                "Estimated population:",
                results[radius]["population"]
            )

            print(
                "Valid pixels:",
                results[radius]["valid_pixels"]
            )

            print(
                "Valid area coverage:",
                results[radius]["coverage_percent"], "%"
            )

            print(
                "Status:",
                results[radius]["status"]
            )

    return results


def calculate_reference_population_batch(
    reference_points_path,
    output_csv_path
):
    import geopandas as gpd
    import csv

    if not RASTER_PATH.exists():
        raise FileNotFoundError(
            f"Raster not found: {RASTER_PATH}"
        )

    reference_points = gpd.read_file(
        reference_points_path
    )

    # Convert all reference points to WGS84
    reference_points = reference_points.to_crs(
        "EPSG:4326"
    )

    to_utm = Transformer.from_crs(
        "EPSG:4326",
        BUFFER_CRS,
        always_xy=True
    )

    results = []

    # Open raster only once
    with rasterio.open(RASTER_PATH) as src:

        to_raster = Transformer.from_crs(
            BUFFER_CRS,
            src.crs,
            always_xy=True
        )

        to_utm_from_raster = Transformer.from_crs(
            src.crs,
            BUFFER_CRS,
            always_xy=True
        )

        total_points = len(reference_points)

        print(f"\nProcessing {total_points} reference points...")

        for index, row in reference_points.iterrows():

            sample_id = int(row["sample_id"])

            longitude = row.geometry.x
            latitude = row.geometry.y

            x, y = to_utm.transform(
                longitude,
                latitude
            )

            point = Point(x, y)

            buffer_utm = point.buffer(
                500,
                quad_segs=32
            )

            buffer_raster = transform_geometry(
                buffer_utm,
                to_raster.transform,
                interleaved=False
            )

            try:

                data, out_transform = mask(
                    src,
                    [mapping(buffer_raster)],
                    crop=True,
                    filled=False,
                    all_touched=True
                )

            except ValueError:

                results.append({
                    "sample_id": sample_id,
                    "latitude": latitude,
                    "longitude": longitude,
                    "population_500m": None,
                    "valid_pixels": 0,
                    "coverage_percent": 0,
                    "status": "Outside raster coverage"
                })

                continue

            population = data[0]

            total_population = 0.0
            valid_pixels = 0
            valid_area = 0.0

            for r in range(population.shape[0]):

                for c in range(population.shape[1]):

                    value = population[r, c]

                    if np.ma.is_masked(value):
                        continue

                    if not np.isfinite(value):
                        continue

                    # Construct raster pixel polygon
                    x1, y1 = out_transform * (c, r)
                    x2, y2 = out_transform * (c + 1, r)
                    x3, y3 = out_transform * (c + 1, r + 1)
                    x4, y4 = out_transform * (c, r + 1)

                    pixel_polygon = Polygon([
                        (x1, y1),
                        (x2, y2),
                        (x3, y3),
                        (x4, y4)
                    ])

                    intersection = pixel_polygon.intersection(
                        buffer_raster
                    )

                    if intersection.is_empty:
                        continue

                    pixel_utm = transform_geometry(
                        pixel_polygon,
                        to_utm_from_raster.transform,
                        interleaved=False
                    )

                    intersection_utm = transform_geometry(
                        intersection,
                        to_utm_from_raster.transform,
                        interleaved=False
                    )

                    if pixel_utm.area <= 0:
                        continue

                    fraction = (
                        intersection_utm.area /
                        pixel_utm.area
                    )

                    fraction = min(
                        1.0,
                        max(0.0, fraction)
                    )

                    total_population += (
                        float(value) * fraction
                    )

                    valid_area += intersection_utm.area
                    valid_pixels += 1

            coverage_percent = (
                valid_area / buffer_utm.area * 100
            )

            coverage_percent = min(
                100.0,
                coverage_percent
            )

            if valid_pixels == 0:
                status = "No valid population data"

            elif coverage_percent >= 95:
                status = "Success"

            elif coverage_percent >= 90:
                status = "Partial Coverage"

            else:
                status = "Low Coverage"

            results.append({
                "sample_id": sample_id,
                "latitude": latitude,
                "longitude": longitude,
                "population_500m": round(
                    total_population, 2
                ),
                "valid_pixels": valid_pixels,
                "coverage_percent": round(
                    coverage_percent, 2
                ),
                "status": status
            })

            # Progress update every 100 points
            if (len(results) % 100 == 0):
                print(
                    f"Processed {len(results)} "
                    f"/ {total_points} points"
                )

    # Save results to CSV
    with open(
        output_csv_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        fieldnames = [
            "sample_id",
            "latitude",
            "longitude",
            "population_500m",
            "valid_pixels",
            "coverage_percent",
            "status"
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(results)

    print("\n========== BATCH PROCESSING COMPLETE ==========")
    print("Total points:", len(results))
    print("CSV saved to:", output_csv_path)

    return results


# -----------------------------------------
# 5. Test the calculation
# -----------------------------------------

if __name__ == "__main__":

    TEST_ISSUE_IDS = [1, 2, 3]

    for issue_id in TEST_ISSUE_IDS:

        print("\n\n" + "=" * 50)
        print("TESTING ISSUE:", issue_id)
        print("=" * 50)

        try:

            latitude, longitude = get_issue_coordinates(
                issue_id
            )

            exposure = calculate_population_exposure(
                issue_id,
                latitude,
                longitude
            )

            print("\nSUMMARY:")

            for radius, values in exposure.items():

                print(
                    f"{radius}m: "
                    f"{values['population']} people | "
                    f"Coverage: "
                    f"{values['coverage_percent']}% | "
                    f"Status: {values['status']}"
                )

        except Exception as error:

            print(
                f"Could not process issue {issue_id}:",
                error
            )
