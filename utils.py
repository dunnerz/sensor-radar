import numpy as np

def fresnel_triangle_check(p1, p2, terrain_sampler, frequency_hz):
    """
    Check if terrain obstructs the first Fresnel zone using a triangular approximation.

    Parameters:
    - p1, p2: tuples (lat, lon, alt) for transmitter and receiver
    - terrain_sampler: function accepting (lat, lon) and returning terrain height in meters
    - frequency_hz: frequency in Hz (e.g., 9.1e9 for 9.1 GHz)

    Returns:
    - bool: True if LOS is clear, False if obstructed
    """
    lat1, lon1, alt1 = p1
    lat2, lon2, alt2 = p2

    def haversine_m(lat1, lon1, lat2, lon2):
        R = 6371000
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        dphi = phi2 - phi1
        dlambda = np.radians(lon2 - lon1)
        a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
        return 2 * R * np.arcsin(np.sqrt(a))

    d = haversine_m(lat1, lon1, lat2, lon2)

    c = 3e8
    r_fresnel = np.sqrt(c * d / (2 * frequency_hz))

    lat_mid = (lat1 + lat2) / 2
    lon_mid = (lon1 + lon2) / 2
    alt_mid = (alt1 + alt2) / 2 - r_fresnel

    C = (lat_mid, lon_mid, alt_mid)

    # Dynamic sampling based on distance - more samples for longer distances
    base_samples = 6
    distance_factor = min(d / 1000, 5)  # Scale up to 5x for distances > 1km
    N = max(base_samples, int(base_samples * distance_factor))
    
    def check_segment(p_start, p_end):
        lats = np.linspace(p_start[0], p_end[0], N)
        lons = np.linspace(p_start[1], p_end[1], N)
        alts = np.linspace(p_start[2], p_end[2], N)
        for lat, lon, alt in zip(lats, lons, alts):
            terrain_alt = terrain_sampler(lat, lon)
            if terrain_alt is not None and terrain_alt > alt:
                return False
        return True

    return check_segment(p1, C) and check_segment(C, p2)

def fresnel_zone_clearance(p1, p2, terrain_sampler, frequency_hz, fresnel_zone=1):
    """
    Enhanced Fresnel zone clearance check with configurable zone number.
    
    Parameters:
    - p1, p2: tuples (lat, lon, alt) for transmitter and receiver
    - terrain_sampler: function accepting (lat, lon) and returning terrain height in meters
    - frequency_hz: frequency in Hz
    - fresnel_zone: which Fresnel zone to check (1 for first zone, 2 for second, etc.)
    
    Returns:
    - bool: True if the specified Fresnel zone is clear, False if obstructed
    """
    lat1, lon1, alt1 = p1
    lat2, lon2, alt2 = p2

    def haversine_m(lat1, lon1, lat2, lon2):
        R = 6371000
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        dphi = phi2 - phi1
        dlambda = np.radians(lon2 - lon1)
        a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
        return 2 * R * np.arcsin(np.sqrt(a))

    d = haversine_m(lat1, lon1, lat2, lon2)
    
    if d == 0:
        return True

    c = 3e8
    # Fresnel zone radius: r = sqrt(n * λ * d1 * d2 / (d1 + d2))
    # For first zone (n=1): r = sqrt(λ * d / 2)
    r_fresnel = np.sqrt(fresnel_zone * c * d / (2 * frequency_hz))

    # Dynamic sampling based on distance and Fresnel zone
    base_samples = 8
    distance_factor = min(d / 500, 8)  # More aggressive scaling
    zone_factor = np.sqrt(fresnel_zone)  # More samples for higher zones
    N = max(base_samples, int(base_samples * distance_factor * zone_factor))
    
    # Check multiple points along the path with Fresnel zone clearance
    lats = np.linspace(lat1, lat2, N)
    lons = np.linspace(lon1, lon2, N)
    alts = np.linspace(alt1, alt2, N)
    
    for i, (lat, lon, alt) in enumerate(zip(lats, lons, alts)):
        # Calculate Fresnel zone clearance at this point
        # The clearance needed decreases as we approach the endpoints
        progress = i / (N - 1) if N > 1 else 0.5
        clearance_factor = 4 * progress * (1 - progress)  # Parabolic shape
        required_clearance = r_fresnel * clearance_factor
        
        terrain_alt = terrain_sampler(lat, lon)
        if terrain_alt is not None and terrain_alt > (alt - required_clearance):
            return False
    
    return True
