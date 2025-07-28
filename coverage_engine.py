import numpy as np
from scipy.io import loadmat
from utils import haversine_distance, is_los_clear, fspl_db

def compute_min_agl(sensor_id, lat, lon, height, config):
    mat = loadmat("england-cells.mat")
    cells = mat["cells"].squeeze()

    sensor_pos = np.array([lat, lon])
    sensor_height_asl = height

    tx_power_dbm = config["txPower"]
    rx_sens_dbm = config["rxSensitivity"]
    freq_hz = config["txFrequency"]
    min_alt = config["minHeight"]
    max_alt = config["maxHeight"]
    alt_step = config["heightRes"]
    max_range_m = config["maxRange"]

    results = []
    for cell in cells:
        cell_lat = float(cell["latitude"])
        cell_lon = float(cell["longitude"])
        terrain_asl = float(cell["terrainHeight"])
        dist_m = haversine_distance(lat, lon, cell_lat, cell_lon)

        if dist_m > max_range_m:
            continue

        for alt_agl in np.arange(min_alt, max_alt + 1, alt_step):
            aircraft_alt_asl = terrain_asl + alt_agl
            if not is_los_clear(sensor_pos, sensor_height_asl, [cell_lat, cell_lon], aircraft_alt_asl, terrain_asl):
                continue

            path_loss = fspl_db(dist_m, freq_hz)
            rx_power = tx_power_dbm - path_loss
            if rx_power >= rx_sens_dbm:
                results.append({
                    "latitude": cell_lat,
                    "longitude": cell_lon,
                    "min_detectable_agl": alt_agl
                })
                break

    return results
