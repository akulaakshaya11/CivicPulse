
import geopandas as gpd
import numpy as np

from pathlib import Path
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

PROJECT_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    PROJECT_DIR / "data" / "population"
    / "ghmc_underserved_lisa.gpkg"
)

gdf = gpd.read_file(INPUT_PATH)

hh = gdf[
    gdf["cluster_type"] == "High-High"
].to_crs("EPSG:32644").reset_index(drop=True)

coordinates = np.column_stack([
    hh.geometry.x,
    hh.geometry.y
])

tree = cKDTree(coordinates)

print("High-High locations:", len(hh))

for threshold in [600, 750, 1000]:

    pairs = list(
        tree.query_pairs(r=threshold)
    )

    if pairs:
        edges = np.array(pairs)

        rows = np.concatenate([
            edges[:, 0], edges[:, 1]
        ])

        cols = np.concatenate([
            edges[:, 1], edges[:, 0]
        ])

        graph = coo_matrix(
            (
                np.ones(len(rows)),
                (rows, cols)
            ),
            shape=(len(hh), len(hh))
        ).tocsr()

    else:
        graph = coo_matrix(
            (len(hh), len(hh))
        ).tocsr()

    n_clusters, labels = connected_components(
        graph,
        directed=False
    )

    sizes = np.bincount(labels)

    print(f"\n========== {threshold} METRES ==========")
    print("Number of clusters:", n_clusters)
    print("Largest cluster:", sizes.max())
    print("Smallest cluster:", sizes.min())
    print("Singleton clusters:", (sizes == 1).sum())

    print(
        "Top 5 cluster sizes:",
        sorted(sizes, reverse=True)[:5]
    )
