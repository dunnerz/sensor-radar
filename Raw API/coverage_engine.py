from geopy.distance import geodesic
from terrain import get_elevation
import numpy as np
from utils import true_fresnel_check
import asyncio
from functools import lru_cache
import math

# Cache for distance calculations
_distance_cache = {}
_distance_cache_hits = 0
_distance_cache_misses = 0

@lru_cache(maxsize=10000)
def fast_distance_calculation(lat1, lon1, lat2, lon2):
    """
    Fast distance calculation using Haversine formula with caching.
    This is much faster than geodesic for repeated calculations.
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
        
    Returns:
        Distance in kilometers
    """
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth radius in kilometers
    R = 6371
    distance_km = R * c
    
    return distance_km

def get_cached_distance(sensor_pos, cell_pos):
    """
    Get distance with caching for better performance.
    
    Args:
        sensor_pos: (lat, lon) of sensor
        cell_pos: (lat, lon) of cell
        
    Returns:
        Distance in kilometers
    """
    global _distance_cache_hits, _distance_cache_misses
    
    # Create cache key
    cache_key = (sensor_pos[0], sensor_pos[1], cell_pos[0], cell_pos[1])
    
    if cache_key in _distance_cache:
        _distance_cache_hits += 1
        return _distance_cache[cache_key]
    
    _distance_cache_misses += 1
    
    # Calculate distance using fast method
    distance_km = fast_distance_calculation(sensor_pos[0], sensor_pos[1], cell_pos[0], cell_pos[1])
    
    # Cache the result
    _distance_cache[cache_key] = distance_km
    
    return distance_km

def calculate_max_signal_range(config):
    """
    Calculate maximum signal range based on txPower and rxSensitivity.
    Uses free space path loss model.
    
    Args:
        config: Configuration dictionary with txPower, rxSensitivity, txFrequency
        
    Returns:
        Maximum range in meters where signal can be received
    """
    tx_power = config['txPower']  # dBm
    rx_sensitivity = config['rxSensitivity']  # dBm
    frequency_mhz = config['txFrequency']  # MHz
    
    # Convert to linear scale
    tx_power_linear = 10**(tx_power/10)  # mW
    rx_sensitivity_linear = 10**(rx_sensitivity/10)  # mW
    
    # Free space path loss: PL = 20*log10(d) + 20*log10(f) - 147.55
    # where d is in meters and f is in MHz
    # Rearranging: d = 10^((PL - 20*log10(f) + 147.55)/20)
    
    # Calculate path loss
    path_loss_db = tx_power - rx_sensitivity
    
    # Calculate maximum range
    max_range_m = 10**((path_loss_db - 20*np.log10(frequency_mhz) + 147.55)/20)
    
    return max_range_m

def get_distance_stats():
    """Get distance cache statistics."""
    total_requests = _distance_cache_hits + _distance_cache_misses
    hit_rate = (_distance_cache_hits / total_requests * 100) if total_requests > 0 else 0
    return {
        'hits': _distance_cache_hits,
        'misses': _distance_cache_misses,
        'total': total_requests,
        'hit_rate': hit_rate,
        'cache_size': len(_distance_cache)
    }

def process_single_cell(cell, sensor_pos, config, previous_agl=0, max_free_space_range_m=None):
    """
    Process a single cell for coverage analysis using TRUE FRESNEL method.
    This function is designed to be run sequentially.
    
    Args:
        cell: Cell dictionary with lat/lon
        sensor_pos: Sensor position (lat, lon, alt)
        config: Configuration dictionary
        previous_agl: Previous successful AGL height (default 0)
        max_free_space_range_m: Maximum free space range in meters (pre-calculated)
        
    Returns:
        Coverage result or None if no coverage
    """
    cell_pos = (cell['latitude'], cell['longitude'])
    
    # Get terrain elevation at this cell
    from terrain import get_elevation
    terrain_asl = get_elevation(cell['latitude'], cell['longitude'])
    if terrain_asl is None:
        return None
    
    # Calculate 2D distance to cell
    cell_2d_distance_m = get_cached_distance(sensor_pos[:2], cell_pos) * 1000  # Convert km to m
    
    # If cell is beyond max free space range, skip it entirely
    if max_free_space_range_m is not None and cell_2d_distance_m > max_free_space_range_m:
        return None
    
    # Smart height loop - start from previous successful AGL
    min_height = config['minHeight']
    max_height = config['maxHeight']
    height_res = config.get('heightRes', 10)
    frequency_hz = config['txFrequency'] * 1e6
    fresnel_samples = config.get('fresnelSamples', 7)
    
    # Determine starting height from previous AGL
    start_height = max(min_height, min(max_height, previous_agl))
    
    # OPTIMIZATION: Pre-calculate constants outside the loop
    sensor_alt = sensor_pos[2]
    cell_lat = cell['latitude']
    cell_lon = cell['longitude']
    
    # OPTIMIZATION: Clear terrain cache for fresh calculations
    from utils import clear_terrain_cache
    clear_terrain_cache()
    
    # Smart height loop: start from previous AGL, then search up or down based on first result
    def test_height(h):
        """Test a specific height and return success/failure."""
        aircraft_alt_asl = terrain_asl + h
        target_pos = (cell_lat, cell_lon, aircraft_alt_asl)
        
        # OPTIMIZATION: Calculate 3D distance more efficiently
        height_diff = aircraft_alt_asl - sensor_alt
        distance_3d_m = np.sqrt(cell_2d_distance_m**2 + height_diff**2)
        
        # Check if 3D distance is within free space range
        if max_free_space_range_m is not None and distance_3d_m > max_free_space_range_m:
            return False  # Too far
        
        # Check line-of-sight at this height using TRUE FRESNEL method (correct mathematics)
        from utils import true_fresnel_check
        # Enable debug for first cell only
        debug_mode = False  # Disable debug for now
        los_clear = true_fresnel_check(sensor_pos, target_pos, get_elevation, frequency_hz, fresnel_samples, debug=debug_mode)
        
        # COMMENTED OUT: Triangle method (incorrect mathematics)
        # from utils import fresnel_triangle_check
        # los_clear = fresnel_triangle_check(sensor_pos, target_pos, get_elevation, frequency_hz, 500)
        
        return los_clear
    
    # Test the starting height (previous AGL)
    start_success = test_height(start_height)
    
    if start_success:
        # Previous AGL works - search downward to find the minimum
        last_successful_height = start_height
        current_height = start_height - height_res
        
        while current_height >= min_height:
            if test_height(current_height):
                last_successful_height = current_height
                current_height -= height_res
            else:
                # Found failure after success - return last successful
                return {
                    'latitude': cell['latitude'],
                    'longitude': cell['longitude'],
                    'agl': last_successful_height,
                    'signal_strength': None,
                    'terrain_asl': terrain_asl
                }
        
        # If we get here, we need to test 0m specifically
        if test_height(0):
            return {
                'latitude': cell['latitude'],
                'longitude': cell['longitude'],
                'agl': 0,
                'signal_strength': None,
                'terrain_asl': terrain_asl
            }
        else:
            # 0m failed, return the last successful height
            return {
                'latitude': cell['latitude'],
                'longitude': cell['longitude'],
                'agl': last_successful_height,
                'signal_strength': None,
                'terrain_asl': terrain_asl
            }
    else:
        # Previous AGL fails - search upward to find success
        current_height = start_height + height_res
        
        while current_height <= max_height:
            if test_height(current_height):
                # Found success - return it
                return {
                    'latitude': cell['latitude'],
                    'longitude': cell['longitude'],
                    'agl': current_height,
                    'signal_strength': None,
                    'terrain_asl': terrain_asl
                }
            current_height += height_res
        
        # No success found up to max height
        return None

# COMMENTED OUT: This function is no longer needed since process_single_cell now uses true Fresnel method
# def process_single_cell_true_fresnel(cell, sensor_pos, config, previous_agl=0, max_free_space_range_m=None):
#     """
#     Process a single cell for coverage analysis using true Fresnel method.
#     This function is designed to be run sequentially.
#     
#     Args:
#         cell: Cell dictionary with lat/lon
#         sensor_pos: Sensor position (lat, lon, alt)
#         config: Configuration dictionary
#         previous_agl: Previous successful AGL height (default 0)
#         max_free_space_range_m: Maximum free space range in meters (pre-calculated)
#         
#     Returns:
#         Coverage result or None if no coverage
#     """
#     cell_pos = (cell['latitude'], cell['longitude'])
#     
#     # Get terrain elevation at this cell
#     from terrain import get_elevation
#     terrain_asl = get_elevation(cell['latitude'], cell['longitude'])
#     if terrain_asl is None:
#         return None
#     
#     # Calculate 2D distance to cell
#     cell_2d_distance_m = get_cached_distance(sensor_pos[:2], cell_pos) * 1000  # Convert km to m
#     
#     # If cell is beyond max free space range, skip it entirely
#     if max_free_space_range_m is not None and cell_2d_distance_m > max_free_space_range_m:
#         return None
#     
#     # Smart height loop - start from previous successful AGL
#     min_height = config['minHeight']
#     max_height = config['maxHeight']
#     height_res = config.get('heightRes', 10)
#     frequency_hz = config['txFrequency'] * 1e6
#     fresnel_samples = config.get('fresnelSamples', 7)
#     
#     # Determine starting height from previous AGL
#     start_height = max(min_height, min(max_height, previous_agl))
#     
#     # Smart height loop: start from previous AGL, then search up or down based on first result
#     def test_height(h):
#         """Test a specific height and return success/failure using true Fresnel method."""
#         aircraft_alt_asl = terrain_asl + h
#         target_pos = (cell['latitude'], cell['longitude'], aircraft_alt_asl)
#         
#         # Calculate 3D distance
#         sensor_alt = sensor_pos[2]
#         height_diff = aircraft_alt_asl - sensor_alt
#         distance_3d_m = np.sqrt(cell_2d_distance_m**2 + height_diff**2)
#         
#         # Check if 3D distance is within free space range
#         if max_free_space_range_m is not None and distance_3d_m > max_free_space_range_m:
#             return False  # Too far
#         
#         # Check line-of-sight at this height using true Fresnel method
#         from utils import true_fresnel_check
#         los_clear = true_fresnel_check(sensor_pos, target_pos, get_elevation, frequency_hz, fresnel_samples)
#         return los_clear
#     
#     # Test the starting height (previous AGL)
#     start_success = test_height(start_height)
#     
#     if start_success:
#         # Previous AGL works - search downward to find the minimum
#         last_successful_height = start_height
#         current_height = start_height - height_res
#         
#         while current_height >= min_height:
#             if test_height(current_height):
#                 last_successful_height = current_height
#                 current_height -= height_res
#             else:
#                 # Found failure after success - return last successful
#                 return {
#                     'latitude': cell['latitude'],
#                     'longitude': cell['longitude'],
#                     'agl': last_successful_height,
#                     'signal_strength': None,
#                     'terrain_asl': terrain_asl
#                 }
#         
#         # If we get here, 0m was successful
#         return {
#             'latitude': cell['latitude'],
#             'longitude': cell['longitude'],
#             'agl': last_successful_height,
#             'signal_strength': None,
#             'terrain_asl': terrain_asl
#         }
#     else:
#         # Previous AGL fails - search upward to find success
#         current_height = start_height + height_res
#         
#         while current_height <= max_height:
#             if test_height(current_height):
#                 # Found success - return it
#                 return {
#                     'latitude': cell['latitude'],
#                     'longitude': cell['longitude'],
#                     'agl': current_height,
#                     'signal_strength': None,
#                     'terrain_asl': terrain_asl
#                 }
#             current_height += height_res
#         
#         # No success found up to max height
#         return None

async def compute_min_agl_parallel(job_id, sensor_id, lat, lon, alt, config, max_workers=4):
    """
    Compute minimum AGL with sequential processing for single CPU optimization.
    
    Args:
        job_id: Job ID for progress tracking
        sensor_id: Sensor identifier
        lat: Sensor latitude
        lon: Sensor longitude
        alt: Sensor altitude
        config: Configuration dictionary
        max_workers: Ignored (kept for compatibility)
        
    Returns:
        List of coverage results
    """
    import time
    results = []
    sensor_pos = (lat, lon, alt)
    
    from progress_store import update_progress as update_progress_store
    
    # Initialize timing tracking
    start_time = time.time()
    stage_times = {}
    
    def update_progress(progress, stage, substage=""):
        elapsed = time.time() - start_time
        stage_times[stage] = elapsed
        update_progress_store(job_id, {
            "progress": progress,
            "stage": stage,
            "substage": substage,
            "elapsed_time": f"{elapsed:.1f}s"
        })
    
    # Stage 1: Initialize terrain system
    update_progress(0, "Loading terrain...", "")
    
    # Display configuration parameters
    print(f"📋 Configuration:")
    print(f"   • Sensor location: {lat:.6f}, {lon:.6f}")
    print(f"   • Sensor altitude: {alt}m")
    print(f"   • Max range: {config['maxRange']}km")
    print(f"   • Height range: {config['minHeight']}-{config['maxHeight']}m")
    print(f"   • Height resolution: {config.get('heightRes', 10)}m")
    print(f"   • Grid resolution: {config.get('gridResolution', 0.5)}km")
    print(f"   • Frequency: {config['txFrequency']}MHz")
    print(f"   • Rx sensitivity: {config['rxSensitivity']}dBm")
    print(f"   • Processing: Sequential (single CPU optimized)")
    
    # Calculate and display signal range
    max_signal_range_m = calculate_max_signal_range(config)
    print(f"   • Max signal range: {max_signal_range_m/1000:.1f}km")
    
    from terrain import load_terrain_model, get_coordinate_transformer
    raster = load_terrain_model()
    transformer = get_coordinate_transformer()
    print("DEBUG: Terrain loaded, starting elevation caching...")
    
    # Add a small delay to make the "Loading terrain..." message visible
    import asyncio
    await asyncio.sleep(0.1)
    
    # Calculate coverage bounds
    lat_deg_per_km = 1 / 111.32
    lon_deg_per_km = 1 / (111.32 * np.cos(np.radians(lat)))
    lat_range = config['maxRange'] * lat_deg_per_km
    lon_range = config['maxRange'] * lon_deg_per_km
    
    # Phase 1: Pre-load elevation cache
    # Calculate approximate number of elevation points to cache
    grid_spacing = 0.001  # ~100m spacing for elevation cache
    lat_points = int(lat_range / grid_spacing) + 1
    lon_points = int(lon_range / grid_spacing) + 1
    total_elevations = lat_points * lon_points
    
    update_progress(0, "Caching terrain", f"Starting elevation caching of {total_elevations} cells")
    print(f"Checking for cached elevation data for {total_elevations} cells...")
    
    def elevation_progress_callback(progress, stage):
        print(f"DEBUG: Elevation progress: {progress}% - {stage}")
        update_progress(0, "Caching terrain", stage)
    
    from terrain import preload_elevation_cache
    max_cells = config.get('maxCells')
    cache_result = await preload_elevation_cache(lat, lon, config['maxRange'], elevation_progress_callback, max_cells)
    
    
    # Check if cache was already loaded
    if cache_result and "already cached" in str(cache_result):
        update_progress(0, "Terrain already cached, skipping to next phase...", "")
        print(f"{total_elevations} cached cells loaded from disk: terrain_cache_aa3c4734.pkl")
        print("Using cached data from disk")
        # Add a small delay to make the message visible
        await asyncio.sleep(0.1)
    else:
        pass
      
    # Generate terrain cells (no progress update needed, happens quickly)
    grid_resolution = config.get('gridResolution', 0.5)  # Default to 500m if not specified
    max_cells = config.get('maxCells')
    cells = generate_terrain_cells(lat, lon, config['maxRange'], None, grid_resolution, max_cells)
    
    # Phase 2: Compute coverage analysis with sequential processing
    total_cells = len(cells)
    update_progress(0, "AGL Calculations", f"Starting AGL calculations of {total_cells} cells")
    update_progress_store(job_id, {"total_cells": total_cells, "processed_cells": 0})
    
    # Add a small delay to make the AGL calculations start message visible
    await asyncio.sleep(0.1)
    
    # Print AGL calculation start message
    print(f"🔄 Starting AGL calculations for {total_cells} cells...")
    
    # Calculate max free space range once at the beginning
    max_free_space_range_m = calculate_max_signal_range(config)
    print(f"📡 Max free space range: {max_free_space_range_m/1000:.1f}km")
    
    # Process cells sequentially
    processed_cells = 0
    previous_agl = 0  # Track previous successful AGL for smart height loop
    
    for cell in cells:
        processed_cells += 1
        
        try:
            # Process single cell with previous AGL as starting point and max free space range
            result = process_single_cell(cell, sensor_pos, config, previous_agl, max_free_space_range_m)
            if result is not None:
                results.append(result)
                # Update previous_agl for next cell
                previous_agl = result['agl']
        except Exception as e:
            print(f"❌ Error processing cell {cell}: {str(e)}")
        
        # Update progress every 10 cells or at the end
        if processed_cells % 10 == 0 or processed_cells == total_cells:
            update_progress(0, "AGL Calculations", 
                          f"{processed_cells} of {total_cells} AGLs calculated")
            update_progress_store(job_id, {"processed_cells": processed_cells})
            print(f"📊 AGL Progress: {processed_cells}/{total_cells} cells processed")
            await asyncio.sleep(0.001)
    
    # Stage 6: Finalize results (95-100%)
    update_progress(95, "Finalizing results", "Preparing output")
    
    # Print detailed results summary
    agl_values = [result.get('agl', 0) for result in results] if results else []
    cells_with_zero_agl = len([agl for agl in agl_values if agl == 0])
    cells_with_coverage = len([agl for agl in agl_values if agl > 0])
    min_agl = min(agl_values) if agl_values else 0
    max_agl = max(agl_values) if agl_values else 0
    mean_agl = sum(agl_values) / len(agl_values) if agl_values else 0
    
    # Find cells with 0m AGL (sensor location or ground level)
    zero_agl_cells = []
    for result in results:
        if result.get('agl', 0) == 0:
            zero_agl_cells.append(result)
    
    # Calculate cells truly out of range (not in results)
    total_cells_generated = len(cells)
    cells_truly_out_of_range = total_cells_generated - len(results)
    
    print(f"📈 RESULTS SUMMARY:")
    print(f"   • Number of cells computed: {len(results)}")
    print(f"   • Number of cells out of range: {cells_truly_out_of_range}")
    print(f"   • Number of cells with 0m AGL: {cells_with_zero_agl}")
    print(f"   • Minimum AGL: {min_agl}m")
    print(f"   • Maximum AGL: {max_agl}m")
    print(f"   • Mean AGL: {mean_agl:.1f}m")
    
    print("END OF PROCESSING")
    
    return results

async def compute_min_agl_with_progress(job_id, sensor_id, lat, lon, alt, config):
    """
    Compute minimum AGL with progress tracking.
    
    Args:
        job_id: Job ID for progress tracking
        sensor_id: Sensor identifier
        lat: Sensor latitude
        lon: Sensor longitude
        alt: Sensor altitude
        config: Configuration dictionary
        
    Returns:
        List of coverage results
    """
    print("🔍 DEBUG: compute_min_agl_with_progress function called!")
    import time
    results = []
    sensor_pos = (lat, lon, alt)
    
    from progress_store import update_progress as update_progress_store
    
    # Initialize timing tracking
    start_time = time.time()
    stage_times = {}
    
    def update_progress(progress, stage, substage=""):
        elapsed = time.time() - start_time
        stage_times[stage] = elapsed
        update_progress_store(job_id, {
            "progress": progress,
            "stage": stage,
            "substage": substage,
            "elapsed_time": f"{elapsed:.1f}s"
        })
    
    # Stage 1: Initialize terrain system (0-5%)
    update_progress(0, "Initializing terrain system", "Loading raster file")
    from terrain import load_terrain_model, get_coordinate_transformer
    raster = load_terrain_model()
    transformer = get_coordinate_transformer()
    update_progress(5, "Initializing terrain system", "Coordinate system ready")
    
    # Stage 2: Calculate coverage bounds (5-10%)
    update_progress(5, "Calculating coverage bounds", "Computing grid dimensions")
    lat_deg_per_km = 1 / 111.32
    lon_deg_per_km = 1 / (111.32 * np.cos(np.radians(lat)))
    lat_range = config['maxRange'] * lat_deg_per_km
    lon_range = config['maxRange'] * lon_deg_per_km
    update_progress(10, "Calculating coverage bounds", "Bounds calculated")
    
    # Stage 3: Pre-load elevation cache (10-60%)
    update_progress(10, "Loading terrain data", "Preparing coordinate grid")
    
    def terrain_progress_callback(progress, stage):
        # Scale terrain loading to 10-60% of total progress
        scaled_progress = 10 + int(progress * 0.5)
        update_progress(scaled_progress, "Loading terrain data", stage)
    
    from terrain import preload_elevation_cache
    await preload_elevation_cache(lat, lon, config['maxRange'], terrain_progress_callback)
    
    # Stage 4: Generate terrain cells (60-70%)
    update_progress(60, "Generating terrain cells", "Creating cell grid")
    
    def cell_progress_callback(progress, stage):
        # Scale cell generation to 60-70% of total progress
        scaled_progress = 60 + int(progress * 0.1)
        update_progress(scaled_progress, "Generating terrain cells", stage)
    
    grid_resolution = config.get('gridResolution', 0.5)  # Default to 500m if not specified
    max_cells = config.get('maxCells')
    cells = generate_terrain_cells(lat, lon, config['maxRange'], cell_progress_callback, grid_resolution, max_cells)
    
    # Stage 5: Compute coverage analysis (70-95%)
    total_cells = len(cells)
    update_progress(70, "Computing coverage analysis", f"Starting processing on 1 of {total_cells} grid cells")
    update_progress_store(job_id, {"total_cells": total_cells, "processed_cells": 0})
    
    # Debug counters
    cells_filtered_by_distance = 0
    cells_filtered_by_terrain = 0
    cells_filtered_by_signal = 0
    cells_filtered_by_fresnel = 0
    cells_with_coverage = 0
    
    for i, cell in enumerate(cells):
        cell_pos = (cell['latitude'], cell['longitude'])
        
        distance_km = get_cached_distance(sensor_pos[:2], cell_pos)
        
        if distance_km > config['maxRange']:
            cells_filtered_by_distance += 1
            continue
        
        terrain_asl = get_elevation(cell['latitude'], cell['longitude'])
        
        if terrain_asl is None:
            cells_filtered_by_terrain += 1
            continue
        
        # OPTIMIZATION: Inline signal strength calculation
        min_height = config['minHeight']
        aircraft_alt_asl = terrain_asl + min_height
        target_pos = (cell_pos[0], cell_pos[1], aircraft_alt_asl)
        signal_strength = simulate_signal_strength(sensor_pos, target_pos, config)
        
        if signal_strength <= config['rxSensitivity']:
            cells_filtered_by_signal += 1
            continue
        
        # Debug: Print signal strength for first few cells
        if i < 5:
            print(f"🔍 Cell {i}: Signal strength at min height: {signal_strength:.1f} dBm (sensitivity: {config['rxSensitivity']} dBm)")
        
        # Time Fresnel zone calculation
        frequency_hz = config['txFrequency'] * 1e6  # Convert MHz to Hz
        los_clear_at_min = true_fresnel_check(sensor_pos, target_pos, get_elevation, frequency_hz)
        
        # Debug: Print Fresnel result for first few cells
        if i < 5:
            print(f"🔍 Cell {i}: Fresnel zone clear: {los_clear_at_min}")
        
        if not los_clear_at_min:
            cells_filtered_by_fresnel += 1
            continue
        
        # Now search for minimum AGL starting from minimum height
        for h in range(config['minHeight'], config['maxHeight'] + 1, config['heightRes']):
            aircraft_alt_asl = terrain_asl + h
            target_pos = (cell['latitude'], cell['longitude'], aircraft_alt_asl)
            
            # For heights above minimum, we can use a simpler check since we know LOS is clear at minimum
            if h > min_height:
                # Simple height check - if terrain doesn't block at minimum height, it won't block at higher heights
                # This is much faster than full Fresnel calculation
                los_clear = True
            else:
                # We already calculated this above, but for consistency
                los_clear = los_clear_at_min
            
            if los_clear:
                results.append({
                    "lat": cell['latitude'],
                    "lon": cell['longitude'],
                    "agl": h
                })
                cells_with_coverage += 1
                break
        
        # Update progress for every cell completion
        progress = min(95, 70 + int((i + 1) / total_cells * 25))  # 70-95% for computation
        
        progress_msg = f"{i + 1} of {total_cells} grid cells complete"
        
        update_progress(progress, "Computing coverage analysis", progress_msg)
        update_progress_store(job_id, {"processed_cells": i + 1})
        # Allow other tasks to run
        await asyncio.sleep(0.001)
    
    # Print detailed timing summary
    print(f"🔍 Cell Filtering Summary:")
    print(f"   Total cells: {len(cells)}")
    print(f"   Filtered by distance: {cells_filtered_by_distance}")
    print(f"   Filtered by terrain: {cells_filtered_by_terrain}")
    print(f"   Filtered by signal strength: {cells_filtered_by_signal}")
    print(f"   Filtered by Fresnel zone: {cells_filtered_by_fresnel}")
    print(f"   Cells with coverage: {cells_with_coverage}")
    print(f"   Sum of all: {cells_filtered_by_distance + cells_filtered_by_terrain + cells_filtered_by_signal + cells_filtered_by_fresnel + cells_with_coverage}")
    
    # Stage 6: Finalize results (95-100%)
    update_progress(95, "Finalizing results", "Preparing output")
    
    print("🔍 DEBUG: About to print detailed results...")
    
    # Print detailed results summary
    agl_values = [result.get('agl', 0) for result in results] if results else []
    cells_out_of_range = len([agl for agl in agl_values if agl == 0])
    cells_with_coverage = len([agl for agl in agl_values if agl > 0])
    min_agl = min(agl_values) if agl_values else 0
    max_agl = max(agl_values) if agl_values else 0
    mean_agl = sum(agl_values) / len(agl_values) if agl_values else 0
    
    print(f"📈 DETAILED RESULTS:")
    print(f"   • Number of cells computed: {len(results)}")
    print(f"   • Number of cells out of range: {cells_out_of_range}")
    print(f"   • Number of cells with 0m value: {cells_out_of_range}")
    print(f"   • Minimum AGL: {min_agl}m")
    print(f"   • Maximum AGL: {max_agl}m")
    print(f"   • Mean AGL: {mean_agl:.1f}m")
    
    print("🔍 DEBUG: Detailed results printed!")
    
    return results

def generate_terrain_cells(center_lat, center_lon, max_range_km, progress_callback=None, grid_resolution_km=0.5, max_cells=None):
    """
    Generate a grid of terrain cells around the sensor location.
    
    Args:
        center_lat: Sensor latitude
        center_lon: Sensor longitude  
        max_range_km: Maximum range in kilometers
        progress_callback: Optional callback function for progress updates
        grid_resolution_km: Grid resolution in kilometers (default: 0.5km = 500m)
        max_cells: Maximum number of cells to generate (for testing)
        
    Returns:
        List of cell dictionaries with lat/lon coordinates
    """
    # Convert km to approximate degrees (rough approximation)
    lat_deg_per_km = 1 / 111.32  # 1 degree latitude ≈ 111.32 km
    lon_deg_per_km = 1 / (111.32 * np.cos(np.radians(center_lat)))
    
    # Calculate grid bounds
    lat_range = max_range_km * lat_deg_per_km
    lon_range = max_range_km * lon_deg_per_km
    
    # Create grid with configurable resolution
    grid_resolution = grid_resolution_km  # Configurable grid resolution
    
    lat_step = grid_resolution * lat_deg_per_km
    lon_step = grid_resolution * lon_deg_per_km
    
    # Calculate total iterations for progress tracking
    lat_count = len(np.arange(center_lat - lat_range, center_lat + lat_range + lat_step, lat_step))
    lon_count = len(np.arange(center_lon - lon_range, center_lon + lon_range + lon_step, lon_step))
    total_iterations = lat_count * lon_count
    current_iteration = 0
    
    cells = []
    for lat in np.arange(center_lat - lat_range, center_lat + lat_range + lat_step, lat_step):
        for lon in np.arange(center_lon - lon_range, center_lon + lon_range + lon_step, lon_step):
            current_iteration += 1
            
            # Check if this cell is within the circular range
            cell_distance_km = geodesic((center_lat, center_lon), (lat, lon)).km
            if cell_distance_km <= max_range_km:
                cells.append({
                    'latitude': lat,
                    'longitude': lon
                })
                
                # Stop if we've reached the maximum number of cells
                if max_cells is not None and len(cells) >= max_cells:
                    print(f"🛑 Stopping at {len(cells)} cells (max_cells={max_cells})")
                    break
            
            # Update progress every 50 iterations or at the end
            if current_iteration % 50 == 0 or current_iteration == total_iterations:
                if progress_callback:
                    # Scale cell generation to 40-50% of total progress
                    cell_progress = int((current_iteration / total_iterations) * 10)
                    progress_percent = 40 + cell_progress
                    progress_callback(progress_percent, f"Generating terrain cells ({current_iteration}/{total_iterations})")
        
        # Break outer loop if we've reached max cells
        if max_cells is not None and len(cells) >= max_cells:
            break
    
    return cells

def simulate_signal_strength(sensor_pos, target_pos, config):
    """
    Calculate signal strength using free space path loss model.
    Optimized for single CPU performance.
    
    Args:
        sensor_pos: (lat, lon, alt) of transmitter
        target_pos: (lat, lon, alt) of receiver
        config: Configuration dictionary
        
    Returns:
        Signal strength in dBm
    """
    # OPTIMIZATION: Pre-calculate constants
    tx_power = config['txPower']  # dBm
    frequency_mhz = config['txFrequency']  # MHz
    
    # OPTIMIZATION: Calculate distance once using cached function
    lat1, lon1, alt1 = sensor_pos
    lat2, lon2, alt2 = target_pos
    
    # Use 2D distance for efficiency (altitude difference is small compared to horizontal distance)
    distance_km = get_cached_distance((lat1, lon1), (lat2, lon2))
    distance_m = distance_km * 1000
    
    # OPTIMIZATION: Early exit for very long distances
    if distance_m > 100000:  # 100km
        return -200  # Very weak signal
    
    # Free space path loss: PL = 20*log10(d) + 20*log10(f) - 147.55
    # where d is in meters and f is in MHz
    path_loss = 20 * np.log10(distance_m) + 20 * np.log10(frequency_mhz) - 147.55
    
    # OPTIMIZATION: Combine calculations
    signal_strength_dbm = tx_power - path_loss
    
    return signal_strength_dbm