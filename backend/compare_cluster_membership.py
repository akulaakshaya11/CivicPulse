
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

largest_clusters = {}

for threshold in [600, 750, 1000]:

    pairs = list(tree.query_pairs(r=threshold))

    if pairs:
        edges = np.array(pairs)
        rows = np.concatenate([edges[:, 0], edges[:, 1]])
        cols = np.concatenate([edges[:, 1], edges[:, 0]])

        graph = coo_matrix(
            (np.ones(len(rows)), (rows, cols)),
            shape=(len(hh), len(hh))
        ).tocsr()
    else:
        graph = coo_matrix((len(hh), len(hh))).tocsr()

    n_clusters, labels = connected_components(
        graph,
        directed=False
    )

    sizes = np.bincount(labels)
    largest_label = np.argmax(sizes)

    members = set(
        hh.loc[labels == largest_label, "sample_id"]
    )

    largest_clusters[threshold] = members

    print(
        f"{threshold}m: {len(members)} locations"
    )

print("\n========== MEMBERSHIP COMPARISON ==========")

for a, b in [(600, 750), (750, 1000), (600, 1000)]:

    A = largest_clusters[a]
    B = largest_clusters[b]

    intersection = len(A & B)
    union = len(A | B)

    jaccard = intersection / union

    print(f"\n{a}m vs {b}m")
    print("Common locations:", intersection)
    print("Union of locations:", union)
    print("Jaccard similarity:", round(jaccard, 4))
