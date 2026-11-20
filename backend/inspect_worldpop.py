
import rasterio
from pathlib import Path
import numpy as np

# -----------------------------------------
# 1. Locate the WorldPop raster file
# -----------------------------------------

project_dir = Path(__file__).resolve().parent.parent

raster_path = (
    project_dir
    / "data"
    / "population"
    / "ind_pop_2025_CN_100m_R2025A_v1.tif"
)

# -----------------------------------------
# 2. Check whether the file exists
# -----------------------------------------

if not raster_path.exists():
    print("ERROR: Population raster file not found!")
    print("Expected location:", raster_path)
    raise SystemExit(1)

# -----------------------------------------
# 3. Open and inspect the raster
# -----------------------------------------

with rasterio.open(raster_path) as src:

    print("\n========== WORLDPOP RASTER DETAILS ==========")

    print("File:", raster_path.name)
    print("CRS:", src.crs)
    print("Width:", src.width)
    print("Height:", src.height)
    print("Bands:", src.count)
    print("Data type:", src.dtypes)
    print("NoData value:", src.nodata)
    print("Bounds:", src.bounds)
    print("Resolution:", src.res)
    print("Pixel size:", src.block_shapes)
    print("Descriptions:", src.descriptions)
    print("Metadata:", src.tags())

    # -----------------------------------------
    # 4. Read a small sample of population data
    # -----------------------------------------

    print("\n========== POPULATION VALUE SAMPLE ==========")

    # Read only 100 x 100 pixels
    # This avoids loading the entire 778 MB file

    sample = src.read(
        1,
        window=((10000, 10100), (10000, 10100)),
        masked=True
    )

    # -----------------------------------------
    # 5. Calculate sample statistics
    # -----------------------------------------

    if sample.count() > 0:

        print("Minimum population:", sample.min())
        print("Maximum population:", sample.max())
        print("Mean population:", sample.mean())
        print("Valid pixels:", sample.count())
        print("Masked pixels:", np.ma.count_masked(sample))

    else:
        print("No valid population values in this sample.")

    # -----------------------------------------
    # 6. Check Hyderabad coverage
    # -----------------------------------------

    print("\n========== HYDERABAD COVERAGE ==========")

    hyderabad_lat = 17.385
    hyderabad_lon = 78.4867

    print("Hyderabad coordinates:")
    print("Latitude:", hyderabad_lat)
    print("Longitude:", hyderabad_lon)

    print(
        "Covered by raster:",
        src.bounds.left <= hyderabad_lon <= src.bounds.right
        and src.bounds.bottom <= hyderabad_lat <= src.bounds.top
    )

    # -----------------------------------------
    # 7. Inspect population at Hyderabad
    # -----------------------------------------

    print("\n========== HYDERABAD SAMPLE PIXEL ==========")

    row, col = src.index(hyderabad_lon, hyderabad_lat)

    value = src.read(
        1,
        window=((row, row + 1), (col, col + 1)),
        masked=True
    )[0, 0]

    if np.ma.is_masked(value):
        print("Population value: NoData")
    else:
        print("Population value:", float(value))

    print("\n========== INSPECTION COMPLETED ==========")
