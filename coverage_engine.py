from geopy.distance import geodesic
from .terrain import get_elevation

def compute_min_agl(sensor_id, lat, lon, alt, config, cells):
    results = []
    sensor_pos = (lat, lon, alt)
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
            signal_strength = simulate_signal_strength(sensor_pos, (cell['latitude'], cell['longitude'], aircraft_alt_asl), config)
            if signal_strength > config['rxSensitivity']:
                results.append({
                    "lat": cell['latitude'],
                    "lon": cell['longitude'],
                    "agl": h
                })
                break
    return results

def simulate_signal_strength(sensor_pos, target_pos, config):
    # Very simplified path loss approximation (Free space model)
    from math import sqrt
    dx = sensor_pos[0] - target_pos[0]
    dy = sensor_pos[1] - target_pos[1]
    dz = sensor_pos[2] - target_pos[2]
    distance = sqrt(dx**2 + dy**2 + dz**2)
    if distance == 0:
        return config['txPower']
    path_loss = 20 * log10(distance) + 20 * log10(config['txFrequency']) - 147.55
    return config['txPower'] - path_loss