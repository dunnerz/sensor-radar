import rasterio
from rasterio.transform import rowcol
from threading import Lock
from functools import lru_cache
import numpy as np
from pyproj import Transformer

_raster = None
_lock = Lock()

def load_terrain_model():
    global _raster
    if _raster is None:
        with _lock:
            if _raster is None:
                try:
                    _raster = rasterio.open("london-terrain-test.tif")
                except Exception as e:
                    raise RuntimeError(f"Failed to load terrain data: {str(e)}")
    return _raster

def get_coordinate_transformer():
    """
    Get a coordinate transformer for converting lat/lon to the raster's CRS.
    
    Returns:
        Transformer object or None if failed
    """
    try:
        raster = load_terrain_model()
        # Transform from WGS84 (lat/lon) to the raster's CRS
        transformer = Transformer.from_crs("EPSG:4326", raster.crs, always_xy=True)
        return transformer
    except Exception as e:
        print(f"Error creating coordinate transformer: {str(e)}")
        return None

def get_raster_bounds():
    """
    Get the bounds of the loaded raster for validation.
    
    Returns:
        Dictionary with bounds information or None if raster not loaded
    """
    try:
        raster = load_terrain_model()
        bounds = raster.bounds
        return {
            'left': bounds.left,
            'right': bounds.right,
            'bottom': bounds.bottom,
            'top': bounds.top,
            'width': raster.width,
            'height': raster.height
        }
    except Exception as e:
        print(f"Error getting raster bounds: {str(e)}")
        return None

@lru_cache(maxsize=10000)
def get_elevation(lat, lon):
    """
    Get elevation at given coordinates with caching for performance.
    
    Args:
        lat: Latitude (WGS84)
        lon: Longitude (WGS84)
        
    Returns:
        Elevation in meters or None if not available
    """
    raster = load_terrain_model()
    transformer = get_coordinate_transformer()
    
    if not transformer:
        print("Error: Could not create coordinate transformer")
        return None
    
    try:
        # Transform lat/lon to raster coordinates
        x, y = transformer.transform(lon, lat)
        
        # Get raster bounds for validation
        bounds = get_raster_bounds()
        if bounds:
            # Check if transformed coordinates are within raster bounds
            if (x < bounds['left'] or x > bounds['right'] or 
                y < bounds['bottom'] or y > bounds['top']):
                return None
        
        row, col = rowcol(raster.transform, x, y)
        
        # Check if row/col are within valid bounds
        if (row < 0 or row >= raster.height or col < 0 or col >= raster.width):
            return None
            
        elevation = raster.read(1)[row, col]
        
        # Check for NaN, masked values, or invalid data
        if np.isnan(elevation) or (hasattr(elevation, 'mask') and elevation.mask):
            return None
            
        # Check if the value is within reasonable bounds (optional)
        if elevation < -1000 or elevation > 9000:  # Typical elevation bounds
            return None
            
        return float(elevation)
    except IndexError:
        return None
    except Exception as e:
        # Log the error but don't crash the application
        print(f"Error getting elevation for ({lat}, {lon}): {str(e)}")
        return None

def validate_terrain_data():
    """
    Validate the loaded terrain data and print diagnostic information.
    
    Returns:
        bool: True if terrain data is valid, False otherwise
    """
    try:
        raster = load_terrain_model()
        bounds = get_raster_bounds()
        
        if not bounds:
            print("❌ Failed to get raster bounds")
            return False
            
        print("✅ Terrain data validation:")
        print(f"   Bounds: {bounds}")
        print(f"   NoData value: {raster.nodata}")
        print(f"   Data type: {raster.dtypes[0]}")
        
        # Check a sample of data for NaN/masked values
        sample_data = raster.read(1)[:10, :10]  # First 10x10 pixels
        nan_count = np.isnan(sample_data).sum()
        print(f"   Sample data shape: {sample_data.shape}")
        print(f"   NaN values in sample: {nan_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Terrain validation failed: {str(e)}")
        return False