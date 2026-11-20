from pathlib import Path
import rasterio

raster_path = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "population"
    / "india_population_2025_100m.tif"
)

if not raster_path.exists():
    raise FileNotFoundError(
        f"Population raster not found: {raster_path}"
    )

with rasterio.open(raster_path) as src:
    print("File:", raster_path.name)
    print("CRS:", src.crs)
    print("Bounds:", src.bounds)
    print("Resolution:", src.res)
    print("Width:", src.width)
    print("Height:", src.height)
    print("Bands:", src.count)
    print("Data type:", src.dtypes)
    print("NoData value:", src.nodata)
    print("Pixel size:", src.res)