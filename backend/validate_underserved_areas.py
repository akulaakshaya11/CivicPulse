
import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

PATH = (
    PROJECT_DIR / "data" / "population"
    / "ghmc_underserved_analysis.csv"
)

df = pd.read_csv(PATH)

categories = [
    "healthcare",
    "education",
    "emergency",
    "community",
    "public_transport"
]

# Focus on high-population locations
high_population = df[df["high_population"]].copy()

print("High-population locations:", len(high_population))

for category in categories:

    zero_500 = high_population[
        high_population[f"{category}_500m"] == 0
    ]

    zero_1000 = high_population[
        high_population[f"{category}_1000m"] == 0
    ]

    print(f"\n========== {category.upper()} ==========")

    print("Zero facilities within 500m:", len(zero_500))
    print("Zero facilities within 1km:", len(zero_1000))

    print(
        "Median nearest-facility distance:",
        round(
            high_population[f"{category}_nearest_m"].median(),
            2
        ),
        "metres"
    )

    print(
        "90th percentile nearest distance:",
        round(
            high_population[f"{category}_nearest_m"].quantile(0.90),
            2
        ),
        "metres"
    )

# Examine locations underserved in multiple categories
print("\n========== MULTI-CATEGORY ANALYSIS ==========")

print(
    high_population["underserved_category_count"]
    .value_counts()
    .sort_index()
)

print(
    "\nLocations underserved in 3 or more categories:",
    (high_population["underserved_category_count"] >= 3).sum()
)

print(
    "Locations underserved in all 5 categories:",
    (high_population["underserved_category_count"] == 5).sum()
)
