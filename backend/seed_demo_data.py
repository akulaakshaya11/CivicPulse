"""Safely preview or insert marked synthetic CivicPulse demonstration data.

Default behavior is a read-only dry run. Pass --apply explicitly to insert.
"""

from __future__ import annotations

import argparse
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import geopandas as gpd
import psycopg
from dotenv import load_dotenv
from shapely.geometry import Point
from shapely.ops import unary_union

MARKER = "[SYNTHETIC DEMO DATA]"
EXPECTED_EXISTING_ISSUES = 6
EXPECTED_EXISTING_COMPLAINTS = 7
NEW_ISSUES = 44
NEW_COMPLAINTS = 144
TARGET_ISSUES = 50
TARGET_COMPLAINTS = 151
RANDOM_SEED = 20261115
# Reserved transaction-scoped advisory-lock pair for CivicPulse demo seeding.
ADVISORY_LOCK_CLASS_ID = 1129334348  # ASCII "CPVL"
ADVISORY_LOCK_OBJECT_ID = 1

LOCALITIES = [
    ("Kukatpally", 78.3996, 17.4948),
    ("Miyapur", 78.3560, 17.4968),
    ("Ameerpet", 78.4483, 17.4375),
    ("Banjara Hills", 78.4347, 17.4126),
    ("Begumpet", 78.4627, 17.4447),
    ("Secunderabad", 78.4983, 17.4399),
    ("Uppal", 78.5590, 17.4058),
    ("LB Nagar", 78.5522, 17.3457),
    ("Mehdipatnam", 78.4320, 17.3949),
    ("Charminar", 78.4747, 17.3616),
    ("Gachibowli", 78.3489, 17.4401),
    ("Madhapur", 78.3915, 17.4483),
]

CATEGORIES = [
    ("pothole", "pothole", 8),
    ("garbage", "garbage", 8),
    ("drainage", "drainage", 7),
    ("waterlogging", "waterlogging", 7),
    ("streetlight", "streetlight", 7),
    ("water_supply", "water supply", 7),
]

ISSUE_TEMPLATES = {
    "pothole": "Road surface damage with a pothole near {locality}.",
    "garbage": "Garbage accumulation needs collection in {locality}.",
    "drainage": "Blocked drainage is affecting the street in {locality}.",
    "waterlogging": "Standing water is affecting access in {locality}.",
    "streetlight": "A streetlight outage is affecting a public route in {locality}.",
    "water_supply": "Intermittent water supply is reported in {locality}.",
}

COMPLAINT_TEMPLATES = {
    "pothole": "Residents report a hazardous road depression near {locality}.",
    "garbage": "Residents report uncollected waste near {locality}.",
    "drainage": "Residents report slow drainage and an obstruction in {locality}.",
    "waterlogging": "Residents report water remaining on the road in {locality}.",
    "streetlight": "Residents report poor nighttime lighting in {locality}.",
    "water_supply": "Residents report a recent interruption in {locality}.",
}

# Four issues have no complaints; the remaining counts sum to 144.
COMPLAINT_COUNTS = [0] * 4 + [1] * 10 + [3] * 14 + [5] * 10 + [7] * 6
ISSUE_STATUSES = ["open"] * 15 + ["in_progress"] * 15 + ["resolved"] * 14
COMPLAINT_STATUSES = ["open"] * 72 + ["in_progress"] * 36 + ["resolved"] * 36


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview or insert synthetic CivicPulse demo records."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the planned data without inserting anything (default).",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Insert records; must be specified explicitly.",
    )
    return parser.parse_args()


def load_boundary() -> Any:
    boundary_path = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "boundary"
        / "ghmc_boundary.gpkg"
    )
    if not boundary_path.is_file():
        raise FileNotFoundError(f"GHMC boundary GeoPackage not found: {boundary_path}")

    boundary_frame = gpd.read_file(boundary_path, layer="ghmc_boundary")
    if boundary_frame.empty or boundary_frame.crs is None:
        raise ValueError("GHMC boundary data is empty or has no CRS.")
    if boundary_frame.crs.to_epsg() != 4326:
        boundary_frame = boundary_frame.to_crs(epsg=4326)

    boundary = unary_union(
        [geometry for geometry in boundary_frame.geometry if geometry is not None]
    )
    if boundary.is_empty or not boundary.is_valid:
        raise ValueError("GHMC boundary geometry is empty or invalid.")

    for locality, longitude, latitude in LOCALITIES:
        if not boundary.covers(Point(longitude, latitude)):
            raise ValueError(
                f"Locality anchor {locality} is outside the GHMC boundary."
            )
    return boundary


def point_near_anchor(
    boundary: Any,
    rng: random.Random,
    longitude: float,
    latitude: float,
    radius_degrees: float,
) -> tuple[float, float]:
    for _ in range(5000):
        dx = rng.uniform(-radius_degrees, radius_degrees)
        dy = rng.uniform(-radius_degrees, radius_degrees)
        candidate = Point(longitude + dx, latitude + dy)
        if boundary.covers(candidate):
            return candidate.x, candidate.y

    if boundary.covers(Point(longitude, latitude)):
        return longitude, latitude
    raise ValueError("Could not sample a point inside the GHMC boundary.")


def nearby_complaint_point(
    boundary: Any,
    rng: random.Random,
    longitude: float,
    latitude: float,
) -> tuple[float, float]:
    # Offsets are roughly within 50 metres at GHMC latitudes.
    for _ in range(100):
        dx = rng.uniform(-0.00045, 0.00045)
        dy = rng.uniform(-0.00045, 0.00045)
        candidate = Point(longitude + dx, latitude + dy)
        if boundary.covers(candidate):
            return candidate.x, candidate.y
    return longitude, latitude


def random_timestamp(
    rng: random.Random,
    lower: datetime,
    upper: datetime,
) -> datetime:
    if lower >= upper:
        return lower
    span_seconds = int((upper - lower).total_seconds())
    return lower + timedelta(seconds=rng.randint(0, span_seconds))


def build_plan(boundary: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(RANDOM_SEED)
    now = datetime.now(timezone.utc)
    complaint_counts = COMPLAINT_COUNTS.copy()
    statuses = ISSUE_STATUSES.copy()
    complaint_statuses = COMPLAINT_STATUSES.copy()
    rng.shuffle(complaint_counts)
    rng.shuffle(statuses)
    rng.shuffle(complaint_statuses)

    category_values = [
        category
        for category, _label, count in CATEGORIES
        for _ in range(count)
    ]
    rng.shuffle(category_values)

    issues: list[dict[str, Any]] = []
    complaints: list[dict[str, Any]] = []
    for index in range(NEW_ISSUES):
        category = category_values[index]
        locality, anchor_lon, anchor_lat = LOCALITIES[index % len(LOCALITIES)]
        longitude, latitude = point_near_anchor(
            boundary, rng, anchor_lon, anchor_lat, radius_degrees=0.004
        )
        first_reported_at = now - timedelta(
            days=rng.randint(90, 240),
            hours=rng.randint(0, 23),
            minutes=rng.randint(0, 59),
        )
        status = statuses[index]
        if status == "resolved":
            resolved_at = random_timestamp(rng, first_reported_at, now)
            last_reported_at = resolved_at
        else:
            resolved_at = None
            last_reported_at = random_timestamp(
                rng,
                first_reported_at,
                now - timedelta(days=1),
            )

        issue = {
            "category": category,
            "locality": locality,
            "issue_type": category,
            "description": f"{MARKER} {ISSUE_TEMPLATES[category].format(locality=locality)}",
            "latitude": latitude,
            "longitude": longitude,
            "physical_severity": rng.randint(1, 5),
            "safety_risk": rng.randint(1, 5),
            "status": status,
            "first_reported_at": first_reported_at,
            "last_reported_at": last_reported_at,
            "resolved_at": resolved_at,
            "complaint_count": complaint_counts[index],
        }
        issues.append(issue)

        # Place reports across recent, previous-week, and older periods. All
        # report timestamps remain after the parent issue's first report.
        age_choices = [1, 4, 9, 12, 20, 45, 75]
        for complaint_index in range(issue["complaint_count"]):
            age_days = age_choices[complaint_index % len(age_choices)]
            reported_at = now - timedelta(
                days=age_days,
                hours=rng.randint(0, 23),
                minutes=rng.randint(0, 59),
            )
            if reported_at <= first_reported_at:
                reported_at = first_reported_at + timedelta(minutes=1)

            complaint_status = complaint_statuses[len(complaints)]
            complaint_resolved_at = (
                random_timestamp(rng, reported_at, now)
                if complaint_status == "resolved"
                else None
            )
            complaint_lon, complaint_lat = nearby_complaint_point(
                boundary, rng, longitude, latitude
            )
            complaints.append({
                "parent_index": index,
                "category": category,
                "locality": locality,
                "issue_type": category,
                "description": (
                    f"{MARKER} {COMPLAINT_TEMPLATES[category].format(locality=locality)}"
                ),
                "latitude": complaint_lat,
                "longitude": complaint_lon,
                "physical_severity": issue["physical_severity"],
                "safety_risk": issue["safety_risk"],
                "status": complaint_status,
                "reported_at": reported_at,
                "resolved_at": complaint_resolved_at,
            })

    if len(issues) != NEW_ISSUES or len(complaints) != NEW_COMPLAINTS:
        raise AssertionError(
            f"Plan mismatch: {len(issues)} issues, {len(complaints)} complaints."
        )
    return issues, complaints


def print_plan(issues: list[dict[str, Any]], complaints: list[dict[str, Any]], apply: bool) -> None:
    mode = "APPLY" if apply else "DRY RUN (no inserts)"
    print(f"Mode: {mode}")
    print(f"Planned new issues: {len(issues)}; planned new complaints: {len(complaints)}")
    print(f"Expected totals after insertion: {TARGET_ISSUES} issues, {TARGET_COMPLAINTS} complaints")
    print("\nPlanned issue inserts (IDs are database-generated):")
    for issue in issues:
        print(
            f"  {issue['issue_type']:<12} {issue['locality']:<16} "
            f"({issue['latitude']:.6f}, {issue['longitude']:.6f}) "
            f"status={issue['status']:<11} complaints={issue['complaint_count']}"
        )

    print("\nPlanned complaint inserts (parent plan numbers map to the issue list above):")
    for complaint in complaints:
        print(
            f"  parent=#{complaint['parent_index'] + 1:02d} "
            f"{complaint['issue_type']:<12} {complaint['locality']:<16} "
            f"status={complaint['status']:<11} "
            f"reported_at={complaint['reported_at'].isoformat()} "
            f"({complaint['latitude']:.6f}, {complaint['longitude']:.6f})"
        )

    print("\nIssue distribution by category:")
    for category, _label, _count in CATEGORIES:
        category_issues = [issue for issue in issues if issue["category"] == category]
        category_complaints = sum(issue["complaint_count"] for issue in category_issues)
        print(
            f"  {category}: {len(category_issues)} issues, "
            f"{category_complaints} complaints"
        )

    print("\nIssue distribution by locality:")
    for locality, _longitude, _latitude in LOCALITIES:
        count = sum(issue["locality"] == locality for issue in issues)
        print(f"  {locality}: {count} issues")

    print("\nStatus distributions:")
    for status in ("open", "in_progress", "resolved"):
        issue_count = sum(issue["status"] == status for issue in issues)
        complaint_count = sum(complaint["status"] == status for complaint in complaints)
        print(
            f"  {status}: {issue_count} issues, {complaint_count} complaints"
        )

    zero_count = sum(issue["complaint_count"] == 0 for issue in issues)
    multiple_count = sum(issue["complaint_count"] > 1 for issue in issues)
    print(f"\nIssues with zero complaints: {zero_count}")
    print(f"Issues with multiple complaints: {multiple_count}")
    print("\nNo issue or complaint descriptions are printed; every planned description includes the synthetic marker.")


def check_database_preconditions(conn: psycopg.Connection[Any]) -> tuple[int, int]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM civic_issues),
                (SELECT COUNT(*) FROM complaints),
                (SELECT COUNT(*) FROM civic_issues WHERE description LIKE %s),
                (SELECT COUNT(*) FROM complaints WHERE description LIKE %s)
            """,
            (f"%{MARKER}%", f"%{MARKER}%"),
        )
        issue_count, complaint_count, marked_issues, marked_complaints = cur.fetchone()

    if marked_issues or marked_complaints:
        raise RuntimeError(
            "Synthetic demo marker already exists; refusing to create duplicates. "
            f"Found {marked_issues} marked issues and {marked_complaints} marked complaints."
        )
    if issue_count != EXPECTED_EXISTING_ISSUES or complaint_count != EXPECTED_EXISTING_COMPLAINTS:
        raise RuntimeError(
            "Unexpected starting totals; refusing to insert to protect existing data. "
            f"Expected {EXPECTED_EXISTING_ISSUES} issues and "
            f"{EXPECTED_EXISTING_COMPLAINTS} complaints, found "
            f"{issue_count} issues and {complaint_count} complaints."
        )
    return issue_count, complaint_count


def insert_plan(
    conn: psycopg.Connection[Any],
    issues: list[dict[str, Any]],
    complaints: list[dict[str, Any]],
) -> None:
    inserted_issue_ids: dict[int, int] = {}

    with conn.transaction():
        # Serialize apply runs and hold the lock through commit or rollback.
        with conn.cursor() as cur:
            cur.execute(
                "SELECT pg_advisory_xact_lock(%s, %s)",
                (ADVISORY_LOCK_CLASS_ID, ADVISORY_LOCK_OBJECT_ID),
            )

        # Recheck after taking the lock, within the transaction that inserts.
        starting_issues, starting_complaints = check_database_preconditions(conn)
        print(
            f"\nCurrent database totals: {starting_issues} issues, "
            f"{starting_complaints} complaints."
        )

        with conn.cursor() as cur:
            for index, issue in enumerate(issues):
                cur.execute(
                    """
                    INSERT INTO civic_issues (
                        issue_type,
                        description,
                        latitude,
                        longitude,
                        first_reported_at,
                        last_reported_at,
                        status,
                        resolved_at,
                        physical_severity,
                        safety_risk,
                        location
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                    )
                    RETURNING issue_id
                    """,
                    (
                        issue["issue_type"],
                        issue["description"],
                        issue["latitude"],
                        issue["longitude"],
                        issue["first_reported_at"],
                        issue["last_reported_at"],
                        issue["status"],
                        issue["resolved_at"],
                        issue["physical_severity"],
                        issue["safety_risk"],
                        issue["longitude"],
                        issue["latitude"],
                    ),
                )
                inserted_issue_ids[index] = cur.fetchone()[0]

            for complaint in complaints:
                issue_id = inserted_issue_ids[complaint["parent_index"]]
                cur.execute(
                    """
                    INSERT INTO complaints (
                        issue_id,
                        description,
                        issue_type,
                        latitude,
                        longitude,
                        physical_severity,
                        safety_risk,
                        status,
                        reported_at,
                        resolved_at,
                        location
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                    )
                    """,
                    (
                        issue_id,
                        complaint["description"],
                        complaint["issue_type"],
                        complaint["latitude"],
                        complaint["longitude"],
                        complaint["physical_severity"],
                        complaint["safety_risk"],
                        complaint["status"],
                        complaint["reported_at"],
                        complaint["resolved_at"],
                        complaint["longitude"],
                        complaint["latitude"],
                    ),
                )

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM civic_issues),
                    (SELECT COUNT(*) FROM complaints),
                    (SELECT COUNT(*) FROM civic_issues WHERE description LIKE %s),
                    (SELECT COUNT(*) FROM complaints WHERE description LIKE %s)
                """,
                (f"%{MARKER}%", f"%{MARKER}%"),
            )
            totals = cur.fetchone()
        expected = (TARGET_ISSUES, TARGET_COMPLAINTS, NEW_ISSUES, NEW_COMPLAINTS)
        if totals != expected:
            raise RuntimeError(
                f"Verification before commit failed: expected {expected}, found {totals}."
            )


def print_verification_queries() -> None:
    print(
        """
Verification queries (run manually after insertion):

SELECT COUNT(*) AS total_issues FROM civic_issues;
SELECT COUNT(*) AS total_complaints FROM complaints;
SELECT COUNT(*) AS synthetic_issues FROM civic_issues
  WHERE description LIKE '%[SYNTHETIC DEMO DATA]%';
SELECT COUNT(*) AS synthetic_complaints FROM complaints
  WHERE description LIKE '%[SYNTHETIC DEMO DATA]%';
SELECT i.issue_id, i.issue_type, COUNT(c.complaint_id) AS complaint_count
  FROM civic_issues AS i
  LEFT JOIN complaints AS c ON c.issue_id = i.issue_id
  GROUP BY i.issue_id, i.issue_type ORDER BY i.issue_id;
SELECT status, COUNT(*) AS issue_count
  FROM civic_issues GROUP BY status ORDER BY status;
SELECT issue_type, COUNT(*) AS issue_count
  FROM civic_issues GROUP BY issue_type ORDER BY issue_type;
"""
    )


def main() -> int:
    args = parse_args()
    apply = bool(args.apply)
    rng_boundary = load_boundary()
    issues, complaints = build_plan(rng_boundary)
    print_plan(issues, complaints, apply)

    load_dotenv(Path(__file__).resolve().parent / ".env")
    try:
        with psycopg.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "civic_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD"),
            autocommit=True,
        ) as conn:
            # Preliminary read-only preflight; apply repeats this check under
            # the advisory lock before inserting.
            starting_issues, starting_complaints = check_database_preconditions(conn)
            print(
                f"\nCurrent database totals: {starting_issues} issues, "
                f"{starting_complaints} complaints."
            )

            if not apply:
                # Preview performs only SELECTs and does not acquire a lock.
                print("Dry run complete; no records were inserted.")
                print_verification_queries()
                return 0

            insert_plan(conn, issues, complaints)
            print(
                f"Inserted {NEW_ISSUES} synthetic issues and "
                f"{NEW_COMPLAINTS} synthetic complaints."
            )
            print_verification_queries()
            return 0
    except Exception as error:
        print(f"Seed operation failed; any active transaction was rolled back: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
