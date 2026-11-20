import pandas as pd
import geopandas as gpd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

CSV_PATH = (
    PROJECT_DIR / "data" / "population"
    / "ghmc_population_exposure_500m.csv"
)

OUTPUT_PATH = (
    PROJECT_DIR / "data" / "population"
    / "ghmc_population_coverage_map.gpkg"
)

df = pd.read_csv(CSV_PATH)

gdf = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(
        df["longitude"],
        df["latitude"]
    ),
    crs="EPSG:4326"
)

gdf.to_file(
    OUTPUT_PATH,
    layer="population_coverage",
    driver="GPKG"
)

excluded = gdf[gdf["coverage_percent"] < 95]

print("Total reference points:", len(gdf))
print("Points with >=95% coverage:", len(gdf) - len(excluded))
print("Points below 95% coverage:", len(excluded))

print("\nExcluded locations by status:")
print(excluded["status"].value_counts())

print("\nCoverage map saved to:", OUTPUT_PATH)