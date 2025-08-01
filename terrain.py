import rasterio
from rasterio.transform import rowcol
from threading import Lock
from functools import lru_cache
import numpy as np
from pyproj import Transformer
import pickle
import os
import hashlib
import sys
import gc

_raster = None
_lock = Lock()
_elevation_cache = None
_cache_bounds = None
_cache_loaded = False  # Flag to track if cache has been loaded

# Cache configuration
MAX_CACHE_SIZE = 100000  # Maximum number of cached coordinates
CACHE_MEMORY_LIMIT_MB = 100  # Maximum memory usage for cache in MB

def get_memory_usage():
    """Get current memory usage in MB."""
    import psutil
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def estimate_cache_memory_usage(cache_size):
    """Estimate memory usage of cache in MB."""
    # Each cache entry: (lat, lon) tuple + float elevation + overhead
    # Rough estimate: 32 bytes per entry
    return (cache_size * 32) / 1024 / 1024

def cleanup_cache_if_needed():
    """Clean up cache if it's too large or using too much memory."""
    global _elevation_cache
    
    if _elevation_cache is None:
        return
    
    cache_size = len(_elevation_cache)
    estimated_memory = estimate_cache_memory_usage(cache_size)
    actual_memory = get_memory_usage()
    
    # OPTIMIZATION: More aggressive cleanup thresholds
    if cache_size > MAX_CACHE_SIZE * 0.8:  # Cleanup at 80% of max size
        print(f"⚠️ Cache approaching limit ({cache_size}/{MAX_CACHE_SIZE}), clearing...")
        _elevation_cache.clear()
        gc.collect()
        return
    
    # OPTIMIZATION: More aggressive memory threshold
    if actual_memory > CACHE_MEMORY_LIMIT_MB * 0.8:  # Cleanup at 80% of memory limit
        print(f"⚠️ Memory usage approaching limit ({actual_memory:.1f}MB), clearing cache...")
        _elevation_cache.clear()
        gc.collect()
        return
    
    # OPTIMIZATION: Periodic cleanup even if not at limits
    if cache_size > MAX_CACHE_SIZE * 0.5 and actual_memory > CACHE_MEMORY_LIMIT_MB * 0.5:
        print(f"🔍 Cache memory usage: {estimated_memory:.1f}MB estimated, {actual_memory:.1f}MB actual")
        # Keep only the most recent 50% of entries
        cache_items = list(_elevation_cache.items())
        _elevation_cache.clear()
        # Keep the most recent half
        for key, value in cache_items[-len(cache_items)//2:]:
            _elevation_cache[key] = value
        gc.collect()

def get_cache_stats():
    """Get cache statistics."""
    if _elevation_cache is None:
        return {
            'size': 0,
            'memory_usage_mb': 0,
            'bounds': None,
            'loaded': False
        }
    
    cache_size = len(_elevation_cache)
    memory_usage = estimate_cache_memory_usage(cache_size)
    
    return {
        'size': cache_size,
        'memory_usage_mb': memory_usage,
        'bounds': _cache_bounds,
        'loaded': _cache_loaded
    }

def get_cache_filename(center_lat, center_lon, max_range_km):
    """Generate a unique cache filename based on parameters."""
    # Create a hash of the parameters for a unique filename
    params = f"{center_lat:.6f}_{center_lon:.6f}_{max_range_km:.1f}"
    cache_hash = hashlib.md5(params.encode()).hexdigest()[:8]
    return f"terrain_cache_{cache_hash}.pkl"

def save_cache_to_disk(cache_data, cache_bounds, filename):
    """Save cache data to disk."""
    try:
        cache_file = {
            'elevation_cache': cache_data,
            'cache_bounds': cache_bounds,
            'cache_loaded': True
        }
        with open(filename, 'wb') as f:
            pickle.dump(cache_file, f)
        print(f"✅ Cache saved to disk: {filename}")
        return True
    except Exception as e:
        print(f"❌ Failed to save cache: {str(e)}")
        return False

def load_cache_from_disk(filename):
    """Load cache data from disk."""
    try:
        if not os.path.exists(filename):
            return None, None, False
        
        with open(filename, 'rb') as f:
            cache_file = pickle.load(f)
        
        print(f"✅ Cache loaded from disk: {filename}")
        return cache_file['elevation_cache'], cache_file['cache_bounds'], cache_file['cache_loaded']
    except Exception as e:
        print(f"❌ Failed to load cache: {str(e)}")
        return None, None, False

def load_terrain_model():
    global _raster
    if _raster is None:
        with _lock:
            if _raster is None:
                # Try multiple possible paths for the terrain file
                possible_paths = [
                    "london-terrain-test.tif",
                    "/app/london-terrain-test.tif",
                    "./london-terrain-test.tif",
                    os.path.join(os.getcwd(), "london-terrain-test.tif")
                ]
                
                for path in possible_paths:
                    try:
                        print(f"🔍 Trying to load terrain from: {path}")
                        if os.path.exists(path):
                            print(f"✅ File exists at: {path}")
                            _raster = rasterio.open(path)
                            print(f"✅ Successfully opened terrain file: {path}")
                            break
                        else:
                            print(f"❌ File not found at: {path}")
                    except Exception as e:
                        print(f"❌ Failed to load from {path}: {str(e)}")
                        continue
                else:
                    # If we get here, none of the paths worked
                    error_msg = f"Failed to load terrain data: 'london-terrain-test.tif' not found in any of the expected locations. Tried: {possible_paths}"
                    print(f"❌ {error_msg}")
                    print(f"🔍 Current working directory: {os.getcwd()}")
                    print(f"🔍 Files in current directory: {[f for f in os.listdir('.') if f.endswith('.tif')]}")
                    raise RuntimeError(error_msg)
    return _raster

async def preload_elevation_cache(center_lat, center_lon, max_range_km, progress_callback=None, max_cells=None):
    """
    Pre-load elevation data for the entire coverage area into memory.
    This dramatically speeds up terrain lookups.
    
    Args:
        center_lat: Center latitude of coverage area
        center_lon: Center longitude of coverage area  
        max_range_km: Maximum range in kilometers
        progress_callback: Optional callback function for progress updates
        max_cells: Maximum number of cells to load (for testing)
    """
    global _elevation_cache, _cache_bounds, _cache_loaded
    
    print(f"Loading terrain data for {max_range_km}km range...")
    
    # Generate cache filename
    cache_filename = get_cache_filename(center_lat, center_lon, max_range_km)
    
    # Try to load from disk first
    print(f"🔍 Checking for cached elevation data...")
    
    disk_cache, disk_bounds, disk_loaded = load_cache_from_disk(cache_filename)
    if disk_cache is not None and disk_bounds is not None:
        _elevation_cache = disk_cache
        _cache_bounds = disk_bounds
        _cache_loaded = disk_loaded
        print(f"✅ Using cached data from disk")
        return True
    
    # If we already have a cache loaded, use it immediately
    if _cache_loaded and _elevation_cache is not None:
        print(f"✅ Using existing cached data")
        return True
    
    # Calculate required bounds for this request
    lat_deg_per_km = 1 / 111.32
    lon_deg_per_km = 1 / (111.32 * np.cos(np.radians(center_lat)))
    
    lat_range = max_range_km * lat_deg_per_km
    lon_range = max_range_km * lon_deg_per_km
    
    # Create grid with 500m resolution
    grid_resolution = 0.5
    lat_step = grid_resolution * lat_deg_per_km
    lon_step = grid_resolution * lon_deg_per_km
    
    # Generate all coordinates in coverage area
    lats = np.arange(center_lat - lat_range, center_lat + lat_range + lat_step, lat_step)
    lons = np.arange(center_lon - lon_range, center_lon + lon_range + lon_step, lon_step)
    
    required_bounds = {
        'lat_min': lats.min(),
        'lat_max': lats.max(), 
        'lon_min': lons.min(),
        'lon_max': lons.max(),
        'lat_step': lat_step,
        'lon_step': lon_step
    }
    
    # Check if we already have the required data cached
    # Round coordinates to avoid floating point precision issues
    required_bounds_rounded = {
        'lat_min': round(required_bounds['lat_min'], 6),
        'lat_max': round(required_bounds['lat_max'], 6),
        'lon_min': round(required_bounds['lon_min'], 6),
        'lon_max': round(required_bounds['lon_max'], 6)
    }
    
    if _cache_bounds is not None:
        cached_bounds_rounded = {
            'lat_min': round(_cache_bounds['lat_min'], 6),
            'lat_max': round(_cache_bounds['lat_max'], 6),
            'lon_min': round(_cache_bounds['lon_min'], 6),
            'lon_max': round(_cache_bounds['lon_max'], 6)
        }
    else:
        cached_bounds_rounded = None
    
    # More lenient cache check: if cached area is larger than required area, use it
    if (_elevation_cache is not None and cached_bounds_rounded is not None and
        required_bounds_rounded['lat_min'] >= cached_bounds_rounded['lat_min'] and
        required_bounds_rounded['lat_max'] <= cached_bounds_rounded['lat_max'] and
        required_bounds_rounded['lon_min'] >= cached_bounds_rounded['lon_min'] and
        required_bounds_rounded['lon_max'] <= cached_bounds_rounded['lon_max']):
        
        print(f"✅ Using existing terrain cache (covers {max_range_km}km range)")
        print(f"   Cached bounds: {cached_bounds_rounded}")
        print(f"   Required bounds: {required_bounds_rounded}")
        if progress_callback:
            progress_callback(60, "Using existing terrain cache")
        return "already cached"
    
    # Even more lenient: if we have any cache and the range is the same, use it
    if (_elevation_cache is not None and _cache_bounds is not None and
        abs(_cache_bounds.get('lat_step', 0) - required_bounds['lat_step']) < 0.000001 and
        abs(_cache_bounds.get('lon_step', 0) - required_bounds['lon_step']) < 0.000001):
        
        print(f"✅ Using existing terrain cache (same resolution)")
        print(f"   Cached bounds: {_cache_bounds}")
        print(f"   Required bounds: {required_bounds}")
        if progress_callback:
            progress_callback(60, "Using existing terrain cache")
        return "already cached"
    
    # Debug: Show cache status
    if _elevation_cache is not None and cached_bounds_rounded is not None:
        print(f"🔍 Cache exists but doesn't cover required area")
    else:
        print(f"🔍 No existing cache found")
    
    # Calculate total cells needed
    total_cells = len(lats) * len(lons)
    print(f"🔄 Processing {total_cells} terrain cells...")
    
    raster = load_terrain_model()
    transformer = get_coordinate_transformer()
    
    if not transformer:
        print("❌ Could not create coordinate transformer")
        return False
    
    # Create coordinate mesh
    lat_mesh, lon_mesh = np.meshgrid(lats, lons, indexing='ij')
    
    # Transform all coordinates at once
    x_coords, y_coords = transformer.transform(lon_mesh.flatten(), lat_mesh.flatten())
    x_coords = x_coords.reshape(lat_mesh.shape)
    y_coords = y_coords.reshape(lat_mesh.shape)
    
    # Get raster bounds
    bounds = get_raster_bounds()
    if not bounds:
        print("❌ Could not get raster bounds")
        return False
    
    # Create elevation cache
    _elevation_cache = {}
    _cache_bounds = required_bounds
    _cache_loaded = True  # Mark cache as loaded
    
    # Load elevation data for all valid coordinates
    valid_count = 0
    total_count = 0
    
    # Calculate total iterations for progress tracking
    total_iterations = len(lats) * len(lons)
    current_iteration = 0
    
    for i, lat in enumerate(lats):
        for j, lon in enumerate(lons):
            total_count += 1
            current_iteration += 1
            x, y = x_coords[i, j], y_coords[i, j]
            
            # Check if coordinates are within raster bounds
            if (x < bounds['left'] or x > bounds['right'] or 
                y < bounds['bottom'] or y > bounds['top']):
                continue
            
            try:
                row, col = rowcol(raster.transform, x, y)
                
                if (row < 0 or row >= raster.height or col < 0 or col >= raster.width):
                    continue
                
                elevation = raster.read(1)[row, col]
                
                if np.isnan(elevation) or (hasattr(elevation, 'mask') and elevation.mask):
                    continue
                
                if elevation < -1000 or elevation > 9000:
                    continue
                
                # Store in cache with rounded coordinates for fast lookup
                lat_key = round(lat, 6)
                lon_key = round(lon, 6)
                _elevation_cache[(lat_key, lon_key)] = float(elevation)
                valid_count += 1
                
                # Stop if we've reached the maximum number of cells
                if max_cells is not None and valid_count >= max_cells:
                    print(f"🛑 Stopping terrain loading at {valid_count} cells (max_cells={max_cells})")
                    break
                
            except Exception:
                continue
            
            # Update progress every 50 iterations or at the end
            if current_iteration % 50 == 0 or current_iteration == total_iterations:
                print(f"   Processed {current_iteration}/{total_iterations} cells")
        
        # Break outer loop if we've reached max cells
        if max_cells is not None and valid_count >= max_cells:
            break
    
    print(f"✅ Cached {valid_count}/{total_count} elevation points")
    
    # Save cache to disk for future use
    save_cache_to_disk(_elevation_cache, _cache_bounds, cache_filename)
    
    return True

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
    # Check if we have a pre-loaded cache
    if _elevation_cache is not None and _cache_bounds is not None:
        # Round coordinates to match cache keys
        lat_key = round(lat, 6)
        lon_key = round(lon, 6)
        
        # Check if coordinates are within cache bounds
        if (_cache_bounds['lat_min'] <= lat_key <= _cache_bounds['lat_max'] and
            _cache_bounds['lon_min'] <= lon_key <= _cache_bounds['lon_max']):
            
            # Fast cache lookup
            elevation = _elevation_cache.get((lat_key, lon_key))
            if elevation is not None:
                return elevation
    
    # Fallback to original method if not in cache
    raster = load_terrain_model()
    transformer = get_coordinate_transformer()
    
    if not transformer:
        print("Error: Could not create coordinate transformer")
        return None
    
    try:
        # Transform lat/lon to raster coordinates
        x, y = transformer.transform(lon, lat)
        
        # Get raster bounds for validation (but don't use for filtering since coordinates are in different systems)
        bounds = get_raster_bounds()
        
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