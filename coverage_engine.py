from geopy.distance import geodesic
from terrain import get_elevation
import numpy as np
from utils import fresnel_triangle_check, fresnel_zone_clearance
import asyncio

def compute_min_agl(sensor_id, lat, lon, alt, config):
    results = []
    sensor_pos = (lat, lon, alt)
    
    # Generate terrain cells around the sensor
    cells = generate_terrain_cells(lat, lon, config['maxRange'])
    
    for cell in cells:
        cell_pos = (cell['latitude'], cell['longitude'])
        distance_km = geodesic(sensor_pos[:2], cell_pos).km
        if distance_km > config['maxRange']:
            continue
        terrain_asl = get_elevation(cell['latitude'], cell['longitude'])
        if terrain_asl is None:
            continue
        for h in range(config['minHeight'], config['maxHeight'] + 1, config['heightRes']):
            aircraft_alt_asl = terrain_asl + h
            target_pos = (cell['latitude'], cell['longitude'], aircraft_alt_asl)
            
            # Check signal strength
            signal_strength = simulate_signal_strength(sensor_pos, target_pos, config)
            if signal_strength > config['rxSensitivity']:
                # Check Fresnel zone clearance for line-of-sight
                frequency_hz = config['txFrequency'] * 1e6  # Convert MHz to Hz
                # Use enhanced Fresnel zone checking for better accuracy
                los_clear = fresnel_zone_clearance(sensor_pos, target_pos, get_elevation, frequency_hz, fresnel_zone=1)
                
                if los_clear:
                    results.append({
                        "lat": cell['latitude'],
                        "lon": cell['longitude'],
                        "agl": h
                    })
                    break
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
    results = []
    sensor_pos = (lat, lon, alt)
    
    # Generate terrain cells around the sensor
    cells = generate_terrain_cells(lat, lon, config['maxRange'])
    
    # Update progress with total cells
    from main import progress_store
    progress_store[job_id]["total_cells"] = len(cells)
    progress_store[job_id]["processed_cells"] = 0
    
    for i, cell in enumerate(cells):
        cell_pos = (cell['latitude'], cell['longitude'])
        distance_km = geodesic(sensor_pos[:2], cell_pos).km
        if distance_km > config['maxRange']:
            continue
        terrain_asl = get_elevation(cell['latitude'], cell['longitude'])
        if terrain_asl is None:
            continue
        for h in range(config['minHeight'], config['maxHeight'] + 1, config['heightRes']):
            aircraft_alt_asl = terrain_asl + h
            target_pos = (cell['latitude'], cell['longitude'], aircraft_alt_asl)
            
            # Check signal strength
            signal_strength = simulate_signal_strength(sensor_pos, target_pos, config)
            if signal_strength > config['rxSensitivity']:
                # Check Fresnel zone clearance for line-of-sight
                frequency_hz = config['txFrequency'] * 1e6  # Convert MHz to Hz
                # Use enhanced Fresnel zone checking for better accuracy
                los_clear = fresnel_zone_clearance(sensor_pos, target_pos, get_elevation, frequency_hz, fresnel_zone=1)
                
                if los_clear:
                    results.append({
                        "lat": cell['latitude'],
                        "lon": cell['longitude'],
                        "agl": h
                    })
                    break
        
        # Update progress every 10 cells or at the end
        if i % 10 == 0 or i == len(cells) - 1:
            progress = min(100, int((i + 1) / len(cells) * 100))
            progress_store[job_id]["progress"] = progress
            progress_store[job_id]["processed_cells"] = i + 1
            # Allow other tasks to run
            await asyncio.sleep(0.001)
    
    return results

def generate_terrain_cells(center_lat, center_lon, max_range_km):
    """
    Generate a grid of terrain cells around the sensor location.
    
    Args:
        center_lat: Sensor latitude
        center_lon: Sensor longitude  
        max_range_km: Maximum range in kilometers
        
    Returns:
        List of cell dictionaries with lat/lon coordinates
    """
    # Convert km to approximate degrees (rough approximation)
    lat_deg_per_km = 1 / 111.32  # 1 degree latitude ≈ 111.32 km
    lon_deg_per_km = 1 / (111.32 * np.cos(np.radians(center_lat)))
    
    # Calculate grid bounds
    lat_range = max_range_km * lat_deg_per_km
    lon_range = max_range_km * lon_deg_per_km
    
    # Create grid with 1km resolution
    grid_resolution = 1  # km
    lat_step = grid_resolution * lat_deg_per_km
    lon_step = grid_resolution * lon_deg_per_km
    
    cells = []
    for lat in np.arange(center_lat - lat_range, center_lat + lat_range + lat_step, lat_step):
        for lon in np.arange(center_lon - lon_range, center_lon + lon_range + lon_step, lon_step):
            cells.append({
                'latitude': lat,
                'longitude': lon
            })
    
    return cells

def simulate_signal_strength(sensor_pos, target_pos, config):
    """
    Calculate signal strength using free space path loss model.
    
    Args:
        sensor_pos: (lat, lon, alt) of transmitter
        target_pos: (lat, lon, alt) of receiver  
        config: Configuration dictionary with txPower, txFrequency
        
    Returns:
        Signal strength in dBm
    """
    from math import sqrt, log10, cos, radians
    
    # Calculate 3D distance in meters
    dx = (sensor_pos[0] - target_pos[0]) * 111320  # Convert lat to meters
    dy = (sensor_pos[1] - target_pos[1]) * 111320 * cos(radians(sensor_pos[0]))  # Convert lon to meters
    dz = sensor_pos[2] - target_pos[2]  # Height difference in meters
    
    distance = sqrt(dx**2 + dy**2 + dz**2)
    if distance == 0:
        return config['txPower']
    
    # Free space path loss: PL = 20*log10(d) + 20*log10(f) - 147.55
    # where d is in meters and f is in MHz
    frequency_mhz = config['txFrequency']  # Assuming frequency is in MHz
    path_loss = 20 * log10(distance) + 20 * log10(frequency_mhz) - 147.55
    
    return config['txPower'] - path_loss