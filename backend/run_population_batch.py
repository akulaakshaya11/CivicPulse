from pathlib import Path
from population_exposure import calculate_reference_population_batch

PROJECT_DIR = Path(__file__).resolve().parent.parent

REFERENCE_POINTS_PATH = (
    PROJECT_DIR
    / "data"
    / "boundary"
    / "ghmc_reference_points.gpkg"
)

OUTPUT_CSV_PATH = (
    PROJECT_DIR
    / "data"
    / "population"
    / "ghmc_population_exposure_500m.csv"
)

results = calculate_reference_population_batch(
    REFERENCE_POINTS_PATH,
    OUTPUT_CSV_PATH
)

print("\nFirst 5 results:")

for result in results[:5]:
    print(result)