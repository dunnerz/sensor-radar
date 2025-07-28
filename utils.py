import numpy as np
import math

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2*R*math.atan2(math.sqrt(a), math.sqrt(1 - a))

def fspl_db(distance_m, freq_hz):
    c = 299792458  # Speed of light
    wavelength = c / freq_hz
    return 20 * np.log10(4 * np.pi * distance_m / wavelength)

def is_los_clear(start_pos, start_alt, end_pos, end_alt, terrain_alt):
    # Placeholder for LOS logic. For now assume LOS is clear if no hill between
    return end_alt >= terrain_alt
