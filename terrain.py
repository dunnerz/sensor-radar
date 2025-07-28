import rasterio
from rasterio.transform import rowcol
from threading import Lock

_raster = None
_lock = Lock()

def load_terrain_model():
    global _raster
    if _raster is None:
        with _lock:
            if _raster is None:
                _raster = rasterio.open("london-terrain-test.tif")
    return _raster

def get_elevation(lat, lon):
    raster = load_terrain_model()
    try:
        row, col = rowcol(raster.transform, lon, lat)
        elevation = raster.read(1)[row, col]
        return float(elevation)
    except IndexError:
        return None