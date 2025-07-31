import numpy as np
from functools import lru_cache

# OPTIMIZATION: Simple terrain cache for frequently accessed coordinates
_terrain_cache = {}

def cached_terrain_sampler(lat, lon, terrain_sampler):
    """Cached terrain sampler to avoid redundant lookups."""
    # Round coordinates to reduce cache size
    lat_rounded = round(lat, 6)
    lon_rounded = round(lon, 6)
    cache_key = (lat_rounded, lon_rounded)
    
    if cache_key not in _terrain_cache:
        _terrain_cache[cache_key] = terrain_sampler(lat, lon)
    
    return _terrain_cache[cache_key]

def clear_terrain_cache():
    """Clear the terrain cache."""
    global _terrain_cache
    _terrain_cache.clear()

@lru_cache(maxsize=10000)
def haversine_m(lat1, lon1, lat2, lon2):
    """Calculate haversine distance between two points in meters."""
    R = 6371000
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = phi2 - phi1
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

def fresnel_radius(frequency_hz, d1_m, d2_m):
    """Calculate Fresnel zone radius."""
    # OPTIMIZATION: Cache constants
    c = 3e8  # speed of light in m/s
    wavelength = c / frequency_hz
    
    # Handle division by zero or very small numbers
    if d1_m + d2_m < 1e-6:
        return 0.0
    
    # OPTIMIZATION: Use more efficient calculation
    return ((wavelength * d1_m * d2_m) / (d1_m + d2_m)) ** 0.5

def true_fresnel_check(p1, p2, terrain_sampler, frequency_hz, fresnel_samples=7, debug=False):
    """
    Optimized true Fresnel zone calculation with early termination.
    
    Parameters:
    - p1, p2: tuples (lat, lon, alt) for transmitter and receiver
    - terrain_sampler: function accepting (lat, lon) and returning terrain height in meters
    - frequency_hz: frequency in Hz
    - fresnel_samples: number of sampling points along the Fresnel zone (default: 7)
    - debug: if True, print detailed calculation steps
    
    Returns:
    - bool: True if LOS is clear, False if obstructed
    """
    lat1, lon1, alt1 = p1
    lat2, lon2, alt2 = p2

    # OPTIMIZATION: Calculate distance once and cache it
    d = haversine_m(lat1, lon1, lat2, lon2)
    
    if d == 0:
        return True

    # OPTIMIZATION: Pre-calculate constants
    c = 3e8
    wavelength = c / frequency_hz
    clearance_factor = 0.6
    
    if debug:
        print(f"\n🔍 FRESNEL CALCULATION DEBUG:")
        print(f"   Sensor: ({lat1:.6f}, {lon1:.6f}, {alt1}m)")
        print(f"   Aircraft: ({lat2:.6f}, {lon2:.6f}, {alt2}m)")
        print(f"   Distance: {d:.1f}m")
        print(f"   Wavelength: {wavelength:.6f}m")
        print(f"   Clearance factor: {clearance_factor}")
    
    # OPTIMIZATION: Pre-calculate interpolation factors
    num_samples = fresnel_samples
    if num_samples == 1:
        t_values = [0.5]
    elif num_samples == 2:
        # For 2 samples, use the middle point only
        t_values = [0.5]
    else:
        # Sample from index 2 to n-1 (exclude start and end points where Fresnel radius = 0)
        # This means t values from 1/(n-1) to (n-2)/(n-1)
        t_values = [i / (num_samples - 1) for i in range(1, num_samples - 1)]
    
    # OPTIMIZATION: Pre-calculate lat/lon differences
    lat_diff = lat2 - lat1
    lon_diff = lon2 - lon1
    alt_diff = alt2 - alt1
    
    if debug:
        print(f"   Sampling points: {len(t_values)}")
        print(f"   T values: {[f'{t:.3f}' for t in t_values]}")
    
    # Check each sample point directly (no line segments for speed)
    for i, t in enumerate(t_values):
        # OPTIMIZATION: Use pre-calculated differences for interpolation
        lat = lat1 + t * lat_diff
        lon = lon1 + t * lon_diff
        alt = alt1 + t * alt_diff
        
        # OPTIMIZATION: Calculate distances more efficiently
        d1 = t * d
        d2 = d - d1  # OPTIMIZATION: Avoid multiplication
        
        # OPTIMIZATION: Avoid division by zero check since d1 + d2 = d > 0
        r_fresnel = ((wavelength * d1 * d2) / d) ** 0.5
        
        # OPTIMIZATION: Combine clearance calculation
        clearance_height = alt - (clearance_factor * r_fresnel)
        
        # Check terrain at this point (early termination)
        terrain_height = cached_terrain_sampler(lat, lon, terrain_sampler)
        if terrain_height is None:
            # DEBUG: Log when terrain sampling fails
            print(f"⚠️ Terrain sampling failed for lat={lat:.6f}, lon={lon:.6f}")
            continue  # Skip this point if terrain data is unavailable
        
        if debug:
            print(f"\n   Sample {i+1}/{len(t_values)} (t={t:.3f}):")
            print(f"     Position: ({lat:.6f}, {lon:.6f}, {alt:.1f}m)")
            print(f"     Distances: d1={d1:.1f}m, d2={d2:.1f}m")
            print(f"     Fresnel radius: {r_fresnel:.3f}m")
            print(f"     Clearance height: {clearance_height:.1f}m")
            print(f"     Terrain height: {terrain_height:.1f}m")
            print(f"     Clearance margin: {clearance_height - terrain_height:.1f}m")
        
        if terrain_height > clearance_height:
            if debug:
                print(f"     ❌ OBSTRUCTED: Terrain ({terrain_height:.1f}m) > Clearance ({clearance_height:.1f}m)")
            return False
        elif debug:
            print(f"     ✅ CLEAR: Terrain ({terrain_height:.1f}m) < Clearance ({clearance_height:.1f}m)")
    
    if debug:
        print(f"   ✅ ALL SAMPLES CLEAR - LOS is unobstructed")
    return True


