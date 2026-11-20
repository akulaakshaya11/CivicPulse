# CivicPulse – AI-Based Civic Issue Prioritization Based on Societal Impact

## About the Project

CivicPulse is a web-based platform designed to help civic authorities identify, analyse and prioritize civic issues based on their societal impact.

Instead of considering only the number of complaints, the system considers multiple factors such as physical severity, safety risk, complaint volume, unresolved duration, population exposure and nearby facility availability.

The goal is to help authorities make informed decisions and address critical civic issues more effectively.

## Key Features

- Civic issue registration and management
- Priority scoring using a weighted rule-based approach
- Critical, High, Medium and Low priority classification
- Population exposure analysis using WorldPop data
- Nearby facility analysis using OpenStreetMap data
- Spatial clustering and underserved-area analysis
- Analytics dashboard with charts and statistics
- Issue filtering, status management and report export

## Technology Stack

**Frontend**
- React.js
- JavaScript
- CSS

**Backend**
- Python
- FastAPI

**Database**
- PostgreSQL
- PostGIS

**Geospatial Analysis**
- QGIS
- GeoPandas
- Shapely
- WorldPop population data
- OpenStreetMap facility data

## Priority Scoring Factors

| Factor | Weight |
|---|---:|
| Physical Severity | 20% |
| Safety Risk | 25% |
| Complaint Volume | 10% |
| Unresolved Duration | 10% |
| Population Exposure | 20% |
| Facility Accessibility Gap | 15% |

The system calculates a normalized weighted score and classifies issues into four priority levels: Critical, High, Medium and Low.

The current implementation uses a spatially enhanced rule-based scoring approach.

## Project Structure

```text
CivicPulse/
├── backend/
├── frontend/
├── data/
├── .gitignore
└── README.md
```

## Requirements

- Python
- Node.js and npm
- PostgreSQL
- PostGIS extension

QGIS is required for additional desktop GIS processing and visualization.

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/CivicPulse.git
cd CivicPulse
```

### 2. Set up the backend

```bash
cd backend
python -m venv venv
```

Activate the environment on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Configure the database connection using your environment variables.

### 3. Set up the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

### 4. Start the backend

From the backend directory:

```bash
python -m uvicorn main:app --reload
```

Backend API documentation:

http://127.0.0.1:8000/docs

Frontend:

http://localhost:5173

## Geospatial Data

The project uses:
- GHMC boundary data for the study area.
- WorldPop data for population exposure analysis.
- OpenStreetMap data for nearby civic facility analysis.

**Note:** The large WorldPop raster is not included in this GitHub repository because of GitHub's individual file size limit. It must be obtained separately and placed in the appropriate data directory before running population analysis.

## Future Enhancements

- Train and evaluate machine-learning models for issue prioritization.
- Integrate real-time civic complaint data.
- Improve facility accessibility analysis using road-network travel distances.
- Develop a mobile application for citizens.
- Improve spatial data coverage and accuracy.

## Project Goal

CivicPulse aims to support smarter civic governance by combining complaint management, impact-based prioritization, spatial analysis and analytics in one centralized platform.
