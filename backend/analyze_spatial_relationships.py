
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr

PROJECT_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    PROJECT_DIR / "data" / "population"
    / "ghmc_combined_spatial_indicators.csv"
)

df = pd.read_csv(INPUT_PATH)

# Define datasets for comparison
datasets = {
    "High coverage (>=95%)": df[df["coverage_percent"] >= 95].copy(),
    "All reference points": df.copy()
}

categories = [
    "healthcare",
    "education",
    "emergency",
    "community",
    "public_transport"
]

for dataset_name, data in datasets.items():

    print("\n" + "=" * 65)
    print(dataset_name)
    print("Observations:", len(data))
    print("=" * 65)

    for category in categories:

        for radius in [500, 1000]:

            facility_column = f"{category}_{radius}m"

            # Spearman rank correlation
            result = spearmanr(
                data["population_500m"],
                data[facility_column]
            )

            print(
                f"{category:18} | {radius:4}m | "
                f"Correlation: {result.statistic:.4f} | "
                f"p-value: {result.pvalue:.6g}"
            )
