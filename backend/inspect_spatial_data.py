
import geopandas as gpd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

files = {
    "Population exposure": (
        PROJECT_DIR / "data" / "population"
        / "ghmc_population_exposure_500m.csv"
    ),
    "Civic facilities": (
        PROJECT_DIR / "data" / "facilities"
        / "Hyderabad_Civic_Facilities.gpkg"
    )
}

import pandas as pd

# Inspect population exposure
population = pd.read_csv(files["Population exposure"])

print("\n========== POPULATION EXPOSURE ==========")
print("Rows:", len(population))
print("Columns:", population.columns.tolist())
print(population.head(3).to_string(index=False))

# Inspect civic facilities
facilities = gpd.read_file(files["Civic facilities"])

print("\n========== CIVIC FACILITIES ==========")
print("Rows:", len(facilities))
print("CRS:", facilities.crs)
print("Columns:", facilities.columns.tolist())
print(facilities.head(3).to_string(index=False))
