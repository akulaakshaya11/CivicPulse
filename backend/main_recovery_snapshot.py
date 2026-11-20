import os
from datetime import datetime, timezone
from enum import Enum

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(
    title="Civic Impact Prioritization System",
    description="AI-based civic issue prioritization",
    version="0.2.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- STATUS ENUM --------------------

class IssueStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


# -------------------- DATABASE CONNECTION --------------------

def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "civic_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
    )


# -------------------- REQUEST MODELS --------------------

class Complaint(BaseModel):
    issue_id: int = Field(gt=0)
    description: str = Field(min_length=5)
    issue_type: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    physical_severity: int = Field(ge=1, le=5)
    safety_risk: int = Field(ge=1, le=5)
    status: IssueStatus = IssueStatus.OPEN
    reported_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class CivicIssue(BaseModel):
    issue_type: str
    description: str = Field(min_length=5)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    physical_severity: int = Field(ge=1, le=5)
    safety_risk: int = Field(ge=1, le=5)


class IssueStatusUpdate(BaseModel):
    status: IssueStatus


# -------------------- HOME AND HEALTH --------------------

@app.get("/")
def home():
    return {
        "message": "Civic Impact Prioritization API is running!",
        "status": "success",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# -------------------- CREATE A CIVIC ISSUE --------------------

@app.post("/issues", status_code=201)
def create_issue(issue: CivicIssue):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO civic_issues (
                        issue_type,
                        description,
                        latitude,
                        longitude,
                        physical_severity,
                        safety_risk,
                        location
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s,
                        ST_SetSRID(
                            ST_MakePoint(%s, %s), 4326
                        )::geography
                    )
                    RETURNING issue_id, status, first_reported_at
                    """,
                    (
                        issue.issue_type,
                        issue.description,
                        issue.latitude,
                        issue.longitude,
                        issue.physical_severity,
                        issue.safety_risk,
                        issue.longitude,
                        issue.latitude,
                    ),
                )
                row = cur.fetchone()

        return {
            "message": "Civic issue created successfully",
            "issue_id": row[0],
            "status": row[1],
            "first_reported_at": row[2],
        }

    except psycopg.Error:
        raise HTTPException(
            status_code=500,
            detail="Could not create civic issue.",
        )


# -------------------- UPDATE A CIVIC ISSUE --------------------

@app.put("/issues/{issue_id}")
def update_issue(
    issue: CivicIssue,
    issue_id: int = Path(gt=0),
):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE civic_issues
                    SET
                        issue_type = %s,
                        description = %s,
                        latitude = %s,
                        longitude = %s,
                        physical_severity = %s,
                        safety_risk = %s,
                        location = ST_SetSRID(
                            ST_MakePoint(%s, %s), 4326
                        )::geography,
                        last_reported_at = CURRENT_TIMESTAMP
                    WHERE issue_id = %s
                    RETURNING
                        issue_id,
                        issue_type,
                        description,
                        latitude,
                        longitude,
                        physical_severity,
                        safety_risk,
                        status,
                        first_reported_at,
                        last_reported_at,
                        resolved_at
                    """,
                    (
                        issue.issue_type,
                        issue.description,
                        issue.latitude,
                        issue.longitude,
                        issue.physical_severity,
                        issue.safety_risk,
                        issue.longitude,
                        issue.latitude,
                        issue_id,
                    ),
                )
                row = cur.fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Civic issue not found.",
            )

        return {
            "issue_id": row[0],
            "issue_type": row[1],
            "description": row[2],
            "latitude": row[3],
            "longitude": row[4],
            "physical_severity": row[5],
            "safety_risk": row[6],
            "status": row[7],
            "first_reported_at": row[8],
            "last_reported_at": row[9],
            "resolved_at": row[10],
        }

    except psycopg.Error:
        raise HTTPException(
            status_code=500,
            detail="Could not update civic issue.",
        )


@app.patch("/issues/{issue_id}/status")
def update_issue_status(
    status_update: IssueStatusUpdate,
    issue_id: int = Path(gt=0),
):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE civic_issues
                    SET
                        status = %s,
                        resolved_at = CASE
                            WHEN %s = 'resolved' THEN CURRENT_TIMESTAMP
                            ELSE NULL
                        END,
                        last_reported_at = CURRENT_TIMESTAMP
                    WHERE issue_id = %s
                    RETURNING
                        issue_id,
                        issue_type,
                        description,
                        latitude,
                        longitude,
                        physical_severity,
                        safety_risk,
                        status,
                        first_reported_at,
                        last_reported_at,
                        resolved_at
                    """,
                    (
                        status_update.status.value,
                        status_update.status.value,
                        issue_id,
                    ),
                )
                row = cur.fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Civic issue not found.",
            )

        return {
            "issue_id": row[0],
            "issue_type": row[1],
            "description": row[2],
            "latitude": row[3],
            "longitude": row[4],
            "physical_severity": row[5],
            "safety_risk": row[6],
            "status": row[7],
            "first_reported_at": row[8],
            "last_reported_at": row[9],
            "resolved_at": row[10],
        }

    except psycopg.Error:
        raise HTTPException(
            status_code=500,
            detail="Could not update civic issue status.",
        )


# -------------------- CREATE A COMPLAINT --------------------

@app.post("/complaints", status_code=201)
def create_complaint(complaint: Complaint):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Check that the civic issue exists.
                cur.execute(
                    """
                    SELECT issue_id
                    FROM civic_issues
                    WHERE issue_id = %s
                    """,
                    (complaint.issue_id,),
                )

                if cur.fetchone() is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Civic issue not found. Create the issue first.",
                    )

                # Save the complaint and link it to the issue.
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
                        location
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        ST_SetSRID(
                            ST_MakePoint(%s, %s), 4326
                        )::geography
                    )
                    RETURNING complaint_id, reported_at
                    """,
                    (
                        complaint.issue_id,
                        complaint.description,
                        complaint.issue_type,
                        complaint.latitude,
                        complaint.longitude,
                        complaint.physical_severity,
                        complaint.safety_risk,
                        complaint.status.value,
                        complaint.reported_at,
                        complaint.longitude,
                        complaint.latitude,
                    ),
                )
                row = cur.fetchone()

        return {
            "message": "Complaint saved successfully",
            "complaint_id": row[0],
            "issue_id": complaint.issue_id,
            "reported_at": row[1],
            "status": complaint.status.value,
        }

    except HTTPException:
        raise

    except psycopg.Error:
        raise HTTPException(
            status_code=500,
            detail="Could not save complaint to the database.",
        )


# -------------------- GET ALL COMPLAINTS --------------------

@app.get("/complaints")
def get_complaints():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        complaint_id,
                        issue_id,
                        description,
                        issue_type,
                        latitude,
                        longitude,
                        physical_severity,
                        safety_risk,
                        status,
                        reported_at
                    FROM complaints
                    ORDER BY reported_at DESC
                    """
                )
                rows = cur.fetchall()

        return [
            {
                "complaint_id": row[0],
                "issue_id": row[1],
                "description": row[2],
                "issue_type": row[3],
                "latitude": row[4],
                "longitude": row[5],
                "physical_severity": row[6],
                "safety_risk": row[7],
                "status": row[8],
                "reported_at": row[9],
            }
            for row in rows
        ]

    except psycopg.Error:
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve complaints from the database.",
        )


# -------------------- ISSUE ANALYTICS --------------------

@app.get("/issues/{issue_id}/analytics")
def get_issue_analytics(
    issue_id: int = Path(gt=0)
):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        i.issue_id,
                        i.issue_type,
                        i.description,
                        i.status,
                        i.physical_severity,
                        i.safety_risk,
                        i.first_reported_at,
                        COUNT(c.complaint_id) AS complaint_count,
                        FLOOR(
                            EXTRACT(
                                EPOCH FROM (
                                    NOW() - i.first_reported_at
                                )
                            ) / 86400
                        )::INTEGER AS age_days
                    FROM civic_issues i
                    LEFT JOIN complaints c
                        ON c.issue_id = i.issue_id
                    WHERE i.issue_id = %s
                    GROUP BY
                        i.issue_id,
                        i.issue_type,
                        i.description,
                        i.status,
                        i.physical_severity,
                        i.safety_risk,
                        i.first_reported_at
                    """,
                    (issue_id,),
                )
                row = cur.fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Civic issue not found.",
            )

        unresolved = row[3] != "resolved"

        return {
            "issue_id": row[0],
            "issue_type": row[1],
            "description": row[2],
            "status": row[3],
            "physical_severity": row[4],
            "safety_risk": row[5],
            "first_reported_at": row[6],
            "complaint_count": row[7],
            "age_days": row[8],
            "unresolved_review_flag": unresolved,
        }

    except HTTPException:
        raise

    except psycopg.Error:
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve issue analytics.",
        )

# -------------------- COMPLAINT TREND ANALYTICS --------------------

@app.get("/issues/{issue_id}/trend")
def get_issue_trend(
    issue_id: int = Path(gt=0)
):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        i.issue_id,
                        i.status,
                        COUNT(c.complaint_id) FILTER (
                            WHERE c.reported_at >= NOW() - INTERVAL '7 days'
                        ) AS recent_count,
                        COUNT(c.complaint_id) FILTER (
                            WHERE c.reported_at >= NOW() - INTERVAL '14 days'
                              AND c.reported_at < NOW() - INTERVAL '7 days'
                        ) AS previous_count
                    FROM civic_issues i
                    LEFT JOIN complaints c
                        ON c.issue_id = i.issue_id
                    WHERE i.issue_id = %s
                    GROUP BY i.issue_id, i.status
                    """,
                    (issue_id,),
                )
                row = cur.fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Civic issue not found.",
            )

        recent_count = row[2]
        previous_count = row[3]
        unresolved = row[1] != "resolved"

        # Avoid drawing a strong conclusion from tiny sample sizes.
        enough_data = previous_count >= 3

        decline_detected = (
            enough_data
            and recent_count < previous_count
        )

        review_flag = unresolved and decline_detected

        if not unresolved:
            message = "Issue is marked resolved."
        elif not enough_data:
            message = (
                "Not enough complaints in the previous period "
                "to reliably assess a declining trend."
            )
        elif decline_detected:
            message = (
                "Complaints have decreased while the issue remains "
                "unresolved. Review the issue; fewer reports do not "
                "confirm resolution."
            )
        else:
            message = (
                "No qualifying decline detected in the available "
                "14-day comparison."
            )

        return {
            "issue_id": row[0],
            "status": row[1],
            "complaints_last_7_days": recent_count,
            "complaints_previous_7_days": previous_count,
            "minimum_previous_complaints_required": 3,
            "enough_data": enough_data,
            "decline_detected": decline_detected,
            "unresolved_review_flag": review_flag,
            "message": message,
        }

    except HTTPException:
        raise

    except psycopg.Error:
        raise HTTPException(
            status_code=500,
            detail="Could not calculate complaint trends.",
        )


# -------------------- CIVIC IMPACT PRIORITY SCORE --------------------

@app.get("/issues/{issue_id}/priority")
def get_issue_priority(
    issue_id: int = Path(gt=0)
):
    try:
        rows = fetch_spatial_priority_rows(issue_id)

        if not rows:
            raise HTTPException(
                status_code=404,
                detail="Civic issue not found.",
            )

        return calculate_spatial_priority(rows[0])

    except HTTPException:
        raise

    except psycopg.Error:
        raise HTTPException(
            status_code=500,
            detail="Could not calculate civic issue priority.",
        )

# -------------------- RANK ALL CIVIC ISSUES --------------------

@app.get("/issues/priority-list")
def get_priority_list():
    try:
        rows = fetch_spatial_priority_rows()

        results = [
            calculate_spatial_priority(row)
            for row in rows
        ]

        # Highest-priority issues first.
        results.sort(
            key=lambda issue: (
                issue["priority_score"],
                issue["unresolved_review_flag"]
            ),
            reverse=True
        )

        for rank, issue in enumerate(results, start=1):
            issue["rank"] = rank

        return {
            "total_issues": len(results),
            "ranking_method": "spatially_enhanced_rule_based",
            "issues": results
        }

    except psycopg.Error:
        raise HTTPException(
            status_code=500,
            detail="Could not rank civic issues."
        )


# -------------------- DASHBOARD ANALYTICS --------------------

@app.get("/analytics/report-trend")
def get_dashboard_report_trend():
    """Return complaint counts for the last 7 calendar days."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        days.report_day::date,
                        COUNT(c.complaint_id)
                    FROM generate_series(
                        CURRENT_DATE - INTERVAL '6 days',
                        CURRENT_DATE,
                        INTERVAL '1 day'
                    ) AS days(report_day)
                    LEFT JOIN complaints c
                        ON c.reported_at >= days.report_day
                        AND c.reported_at < days.report_day + INTERVAL '1 day'
                    GROUP BY days.report_day
                    ORDER BY days.report_day
                """)
                rows = cur.fetchall()

        return {
            "source": "postgresql",
            "period_days": 7,
            "data": [
                {
                    "day": row[0].strftime("%a"),
                    "date": row[0].isoformat(),
                    "reports": row[1]
                }
                for row in rows
            ]
        }
    except psycopg.Error:
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve dashboard reporting trend."
        )


@app.get("/analytics/category-distribution")
def get_dashboard_category_distribution():
    """Return complaint counts and percentages by category."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        COALESCE(
                            NULLIF(TRIM(issue_type), ''),
                            'Uncategorized'
                        ) AS category,
                        COUNT(*) AS report_count
                    FROM complaints
                    GROUP BY 1
                    ORDER BY report_count DESC, category ASC
                """)
                rows = cur.fetchall()

        total = sum(row[1] for row in rows)

        return {
            "source": "postgresql",
            "total_reports": total,
            "data": [
                {
                    "name": row[0],
                    "value": round(row[1] * 100 / total, 1)
                             if total else 0,
                    "count": row[1]
                }
                for row in rows
            ]
        }
    except psycopg.Error:
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve category distribution."
        )

# -------------------- LOCATION IMPACT ANALYSIS --------------------

@app.get("/issues/{issue_id}/location-impact")
def get_issue_location_impact(
    issue_id: int = Path(gt=0)
):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:

                # First, confirm that the civic issue exists.
                cur.execute(
                    """
                    SELECT
                        issue_id,
                        issue_type,
                        description,
                        latitude,
                        longitude
                    FROM civic_issues
                    WHERE issue_id = %s
                    """,
                    (issue_id,)
                )

                issue = cur.fetchone()

                if issue is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Civic issue not found."
                    )

                # Find mapped essential facilities within 1 km.
                # The coordinates are restricted to our approximate
                # Hyderabad study area.
                cur.execute(
                    """
                    SELECT
                        category,
                        name,
                        ROUND(
                            ST_Distance(
                                location,
                                ST_SetSRID(
                                    ST_MakePoint(%s, %s),
                                    4326
                                )::geography
                            )::numeric,
                            1
                        ) AS distance_metres
                    FROM civic_facilities
                    WHERE data_source = 'OpenStreetMap'
                      AND category IN (
                          'healthcare',
                          'education',
                          'emergency'
                      )
                      AND latitude BETWEEN 17.20 AND 17.60
                      AND longitude BETWEEN 78.20 AND 78.65
                      AND location IS NOT NULL
                      AND ST_DWithin(
                          location,
                          ST_SetSRID(
                              ST_MakePoint(%s, %s),
                              4326
                          )::geography,
                          1000
                      )
                    ORDER BY distance_metres ASC
                    """,
                    (
                        issue[4], issue[3],
                        issue[4], issue[3]
                    )
                )

                facilities = cur.fetchall()

        # Count facilities by category and proximity band.
        category_counts = {
            "healthcare": 0,
            "education": 0,
            "emergency": 0
        }

        within_250m = 0
        within_500m = 0

        nearby_facilities = []

        for category, name, distance in facilities:
            distance = float(distance)

            category_counts[category] += 1

            if distance <= 250:
                within_250m += 1

            if distance <= 500:
                within_500m += 1

            nearby_facilities.append({
                "category": category,
                "name": name,
                "distance_metres": distance
            })

        # A transparent, provisional indicator based on nearby
        # essential facilities. This is not a trained ML score.
        proximity_indicator = min(
            100,
            10 * category_counts["healthcare"]
            + 5 * category_counts["education"]
            + 8 * category_counts["emergency"]
        )

        return {
            "issue_id": issue[0],
            "issue_type": issue[1],
            "description": issue[2],
            "study_area": {
                "latitude_range": [17.20, 17.60],
                "longitude_range": [78.20, 78.65],
                "boundary_note": (
                    "Approximate bounding box, not an official "
                    "administrative boundary."
                )
            },
            "search_radius_metres": 1000,
            "nearby_facility_count": len(nearby_facilities),
            "facilities_within_250m": within_250m,
            "facilities_within_500m": within_500m,
            "category_counts": category_counts,
            "proximity_indicator": proximity_indicator,
            "indicator_note": (
                "Provisional proximity proxy, not confirmed societal "
                "impact. Weights are initial assumptions and require "
                "validation. OpenStreetMap facilities are not "
                "independently verified."
            ),
            "nearby_facilities": nearby_facilities
        }

    except HTTPException:
        raise

    except psycopg.Error:
        raise HTTPException(
            status_code=500,
            detail="Could not calculate location impact."
        )


# -----------------------------------------
# POPULATION EXPOSURE API
# -----------------------------------------

@app.get("/issues/{issue_id}/population-exposure")
def get_population_exposure_api(
    issue_id: int = Path(gt=0)
):
    # Import locally to avoid circular imports.
    from population_exposure import (
        get_issue_coordinates,
        calculate_population_exposure
    )

    try:
        # Fetch issue coordinates from PostgreSQL
        latitude, longitude = get_issue_coordinates(issue_id)

        # Calculate population exposure
        exposure = calculate_population_exposure(
            issue_id,
            latitude,
            longitude
        )

        return {
            "issue_id": issue_id,
            "location": {
                "latitude": latitude,
                "longitude": longitude
            },
            "data_source": "WorldPop",
            "reference_year": 2025,
            "unit": "estimated persons",
            "population_exposure": {
                f"{radius}m": values
                for radius, values in exposure.items()
            }
        }

    except ValueError as error:
        if "not found" in str(error).lower():
            raise HTTPException(
                status_code=404,
                detail=str(error)
            )

        raise HTTPException(
            status_code=422,
            detail=str(error)
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Could not calculate population exposure."
        )


# -------------------- SPATIALLY ENHANCED PRIORITY SHARED LOGIC --------------------

PRIORITY_LIST_SQL = """
    SELECT
        i.issue_id, i.issue_type, i.description, i.status,
        i.physical_severity, i.safety_risk, i.first_reported_at,
        COUNT(c.complaint_id) AS total_complaints,
        COUNT(c.complaint_id) FILTER (
            WHERE c.reported_at >= NOW() - INTERVAL '7 days'
        ) AS recent_count,
        COUNT(c.complaint_id) FILTER (
            WHERE c.reported_at >= NOW() - INTERVAL '14 days'
              AND c.reported_at < NOW() - INTERVAL '7 days'
        ) AS previous_count,
        r.sample_id, r.population_500m, r.coverage_percent,
        r.status AS population_status,
        r.healthcare_500m, r.education_500m, r.emergency_500m,
        r.community_500m, r.public_transport_500m,
        ST_Distance(i.location, r.location) AS distance_m
    FROM civic_issues i
    LEFT JOIN complaints c ON c.issue_id = i.issue_id
    LEFT JOIN LATERAL (
        SELECT * FROM spatial_reference_points r
        WHERE i.location IS NOT NULL
        ORDER BY i.location <-> r.location
        LIMIT 1
    ) r ON TRUE
    {where_clause}
    GROUP BY
        i.issue_id, i.issue_type, i.description, i.status,
        i.physical_severity, i.safety_risk, i.first_reported_at,
        r.sample_id, r.population_500m, r.coverage_percent, r.status,
        r.healthcare_500m, r.education_500m, r.emergency_500m,
        r.community_500m, r.public_transport_500m, r.location
"""


def fetch_spatial_priority_rows(issue_id=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if issue_id is None:
                cur.execute(PRIORITY_LIST_SQL.format(where_clause=""))
                return cur.fetchall()
            cur.execute(
                PRIORITY_LIST_SQL.format(where_clause="WHERE i.issue_id = %s"),
                (issue_id,),
            )
            return cur.fetchall()


def calculate_spatial_priority(row, now=None):
    if now is None:
        now = datetime.now(timezone.utc)

    (
        issue_id, issue_type, description, status, severity, safety_risk,
        first_reported_at, total_complaints, recent_count, previous_count,
        sample_id, population, coverage, population_status,
        healthcare, education, emergency, community, public_transport,
        distance_m,
    ) = row

    unresolved = status != "resolved"
    if first_reported_at.tzinfo is None:
        first_reported_at = first_reported_at.replace(tzinfo=timezone.utc)
    age_days = max(0, (now - first_reported_at).days)

    severity_score = (severity / 5) * 100
    safety_score = (safety_risk / 5) * 100
    duration_score = min(age_days / 30, 1) * 100 if unresolved else 0
    volume_score = min(total_complaints / 10, 1) * 100

    population_available = (
        population is not None
        and coverage is not None
        and coverage >= 95
    )
    population_score = None
    if population_available:
        population_score = min((population / 13924.35) * 100, 100)

    facility_values = [healthcare, education, emergency, community, public_transport]
    facility_available = sample_id is not None and all(value is not None for value in facility_values)
    facility_gap_score = None
    if facility_available:
        zero_facility_categories = sum(1 for value in facility_values if value == 0)
        facility_gap_score = (zero_facility_categories / 5) * 100

    enough_data = previous_count >= 3
    decline_detected = enough_data and recent_count < previous_count
    review_flag = unresolved and decline_detected

    weighted_score = (
        20 * severity_score
        + 25 * safety_score
        + 10 * volume_score
        + 10 * duration_score
    )
    available_weight = 65
    if population_available:
        weighted_score += 20 * population_score
        available_weight += 20
    if facility_available:
        weighted_score += 15 * facility_gap_score
        available_weight += 15

    score = round(weighted_score / available_weight, 2)
    if score >= 75:
        priority = "critical"
    elif score >= 50:
        priority = "high"
    elif score >= 25:
        priority = "medium"
    else:
        priority = "low"

    return {
        "issue_id": issue_id,
        "issue_type": issue_type,
        "description": description,
        "status": status,
        "physical_severity": severity,
        "safety_risk": safety_risk,
        "age_days": age_days,
        "total_complaints": total_complaints,
        "complaints_last_7_days": recent_count,
        "complaints_previous_7_days": previous_count,
        "spatial_data": {
            "reference_point_id": sample_id,
            "distance_m": round(distance_m, 2) if distance_m is not None else None,
            "population_500m": population,
            "population_coverage": coverage,
            "population_status": population_status,
            "population_available": population_available,
            "facility_counts_500m": {
                "healthcare": healthcare,
                "education": education,
                "emergency": emergency,
                "community": community,
                "public_transport": public_transport,
            },
        },
        "component_scores": {
            "physical_severity": round(severity_score, 2),
            "safety_risk": round(safety_score, 2),
            "population_exposure": round(population_score, 2) if population_score is not None else None,
            "facility_accessibility_gap": round(facility_gap_score, 2) if facility_gap_score is not None else None,
            "complaint_volume": round(volume_score, 2),
            "unresolved_duration": round(duration_score, 2),
        },
        "available_weight": available_weight,
        "priority_score": score,
        "priority_level": priority,
        "decline_detected": decline_detected,
        "unresolved_review_flag": review_flag,
    }


# -------------------- CIVIC IMPACT PRIORITY SCORE --------------------

@app.get("/issues/{issue_id}/priority")
def get_issue_priority(issue_id: int = Path(gt=0)):
    try:
        rows = fetch_spatial_priority_rows(issue_id)
        if not rows:
            raise HTTPException(status_code=404, detail="Civic issue not found.")
        return calculate_spatial_priority(rows[0])
    except HTTPException:
        raise
    except psycopg.Error:
        raise HTTPException(status_code=500, detail="Could not calculate civic issue priority.")
    
# -------------------- RANK ALL CIVIC ISSUES --------------------

@app.get("/issues/priority-list")
def get_priority_list():
    try:
        rows = fetch_spatial_priority_rows()
        results = [calculate_spatial_priority(row) for row in rows]
        results.sort(
            key=lambda issue: (issue["priority_score"], issue["unresolved_review_flag"]),
            reverse=True,
        )
        for rank, issue in enumerate(results, start=1):
            issue["rank"] = rank
        return {
            "total_issues": len(results),
            "ranking_method": "spatially_enhanced_rule_based",
            "issues": results,
        }
    except psycopg.Error:
        raise HTTPException(status_code=500, detail="Could not rank civic issues.")

# -------------------- DASHBOARD ANALYTICS --------------------

@app.get("/analytics/report-trend")
def get_dashboard_report_trend():
    """Return complaint counts for the last 7 calendar days."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        days.report_day::date,
                        COUNT(c.complaint_id)
                    FROM generate_series(
                        CURRENT_DATE - INTERVAL '6 days',
                        CURRENT_DATE,
                        INTERVAL '1 day'
                    ) AS days(report_day)
                    LEFT JOIN complaints c
                        ON c.reported_at >= days.report_day
                        AND c.reported_at < days.report_day + INTERVAL '1 day'
                    GROUP BY days.report_day
                    ORDER BY days.report_day
                """)
                rows = cur.fetchall()

        return {
            "source": "postgresql",
            "period_days": 7,
            "data": [
                {
                    "day": row[0].strftime("%a"),
                    "date": row[0].isoformat(),
                    "reports": row[1]
                }
                for row in rows
            ]
        }
    except psycopg.Error:
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve dashboard reporting trend."
        )


@app.get("/analytics/category-distribution")
def get_dashboard_category_distribution():
    """Return complaint counts and percentages by category."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        COALESCE(
                            NULLIF(TRIM(issue_type), ''),
                            'Uncategorized'
                        ) AS category,
                        COUNT(*) AS report_count
                    FROM complaints
                    GROUP BY 1
                    ORDER BY report_count DESC, category ASC
                """)
                rows = cur.fetchall()

        total = sum(row[1] for row in rows)

        return {
            "source": "postgresql",
            "total_reports": total,
            "data": [
                {
                    "name": row[0],
                    "value": round(row[1] * 100 / total, 1)
                             if total else 0,
                    "count": row[1]
                }
                for row in rows
            ]
        }
    except psycopg.Error:
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve category distribution."
        )

# -------------------- LOCATION IMPACT ANALYSIS --------------------

@app.get("/issues/{issue_id}/location-impact")
def get_issue_location_impact(
    issue_id: int = Path(gt=0)
):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:

                # First, confirm that the civic issue exists.
                cur.execute(
                    """
                    SELECT
                        issue_id,
                        issue_type,
                        description,
                        latitude,
                        longitude
                    FROM civic_issues
                    WHERE issue_id = %s
                    """,
                    (issue_id,)
                )

                issue = cur.fetchone()

                if issue is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Civic issue not found."
                    )

                # Find mapped essential facilities within 1 km.
                # The coordinates are restricted to our approximate
                # Hyderabad study area.
                cur.execute(
                    """
                    SELECT
                        category,
                        name,
                        ROUND(
                            ST_Distance(
                                location,
                                ST_SetSRID(
                                    ST_MakePoint(%s, %s),
                                    4326
                                )::geography
                            )::numeric,
                            1
                        ) AS distance_metres
                    FROM civic_facilities
                    WHERE data_source = 'OpenStreetMap'
                      AND category IN (
                          'healthcare',
                          'education',
                          'emergency'
                      )
                      AND latitude BETWEEN 17.20 AND 17.60
                      AND longitude BETWEEN 78.20 AND 78.65
                      AND location IS NOT NULL
                      AND ST_DWithin(
                          location,
                          ST_SetSRID(
                              ST_MakePoint(%s, %s),
                              4326
                          )::geography,
                          1000
                      )
                    ORDER BY distance_metres ASC
                    """,
                    (
                        issue[4], issue[3],
                        issue[4], issue[3]
                    )
                )

                facilities = cur.fetchall()

        # Count facilities by category and proximity band.
        category_counts = {
            "healthcare": 0,
            "education": 0,
            "emergency": 0
        }

        within_250m = 0
        within_500m = 0

        nearby_facilities = []

        for category, name, distance in facilities:
            distance = float(distance)

            category_counts[category] += 1

            if distance <= 250:
                within_250m += 1

            if distance <= 500:
                within_500m += 1

            nearby_facilities.append({
                "category": category,
                "name": name,
                "distance_metres": distance
            })

        # A transparent, provisional indicator based on nearby
        # essential facilities. This is not a trained ML score.
        proximity_indicator = min(
            100,
            10 * category_counts["healthcare"]
            + 5 * category_counts["education"]
            + 8 * category_counts["emergency"]
        )

        return {
            "issue_id": issue[0],
            "issue_type": issue[1],
            "description": issue[2],
            "study_area": {
                "latitude_range": [17.20, 17.60],
                "longitude_range": [78.20, 78.65],
                "boundary_note": (
                    "Approximate bounding box, not an official "
                    "administrative boundary."
                )
            },
            "search_radius_metres": 1000,
            "nearby_facility_count": len(nearby_facilities),
            "facilities_within_250m": within_250m,
            "facilities_within_500m": within_500m,
            "category_counts": category_counts,
            "proximity_indicator": proximity_indicator,
            "indicator_note": (
                "Provisional proximity proxy, not confirmed societal "
                "impact. Weights are initial assumptions and require "
                "validation. OpenStreetMap facilities are not "
                "independently verified."
            ),
            "nearby_facilities": nearby_facilities
        }

    except HTTPException:
        raise

    except psycopg.Error:
        raise HTTPException(
            status_code=500,
            detail="Could not calculate location impact."
        )


# -----------------------------------------
# POPULATION EXPOSURE API
# -----------------------------------------

@app.get("/issues/{issue_id}/population-exposure")
def get_population_exposure_api(
    issue_id: int = Path(gt=0)
):
    # Import locally to avoid circular imports.
    from population_exposure import (
        get_issue_coordinates,
        calculate_population_exposure
    )

    try:
        # Fetch issue coordinates from PostgreSQL
        latitude, longitude = get_issue_coordinates(issue_id)

        # Calculate population exposure
        exposure = calculate_population_exposure(
            issue_id,
            latitude,
            longitude
        )

        return {
            "issue_id": issue_id,
            "location": {
                "latitude": latitude,
                "longitude": longitude
            },
            "data_source": "WorldPop",
            "reference_year": 2025,
            "unit": "estimated persons",
            "population_exposure": {
                f"{radius}m": values
                for radius, values in exposure.items()
            }
        }

    except ValueError as error:
        if "not found" in str(error).lower():
            raise HTTPException(
                status_code=404,
                detail=str(error)
            )

        raise HTTPException(
            status_code=422,
            detail=str(error)
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Could not calculate population exposure."
        )
