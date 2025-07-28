import math
from scipy.io import loadmat
from geopy.distance import geodesic
from typing import List, Dict, Any


def mat_struct_to_dict(obj):
    """Recursively convert MATLAB mat_struct to nested Python dicts."""
    from scipy.io.matlab.mio5_params import mat_struct
    if isinstance(obj, mat_struct):
        result = {}
        for field_name in obj._fieldnames:
            result[field_name] = mat_struct_to_dict(getattr(obj, field_name))
        return result
    elif isinstance(obj, list):
        return [mat_struct_to_dict(item) for item in obj]
    else:
        return obj


def compute_min_agl(
    sensor_id: str,
    sensor_lat: float,
    sensor_lon: float,
    sensor_alt: float,
    config: Dict[str, Any]
) -> List[Dict[str, float]]:
    # Load and process MATLAB cells
    mat = loadmat("england-cells.mat", struct_as_record=False, squeeze_me=True)
    raw_cells = mat["cells"]
    cells = [mat_struct_to_dict(cell) for cell in raw_cells]

    # Filter cells within range
    def haversine(lat1, lon1, lat2, lon2):
        return geodesic((lat1, lon1), (lat2, lon2)).meters

    local_cells = [
        cell for cell in cells
        if haversine(sensor_lat, sensor_lon, cell["latitude"], cell["longitude"]) < config["maxRange"]
    ]

    results = []
    for cell in local_cells:
        terrain_asl = float(cell["height"])  # Altitude of the terrain
        min_detectable_agl = None

        for h in range(config["minHeight"], config["maxHeight"] + 1, config["heightRes"]):
            aircraft_alt_asl = terrain_asl + h
            slant_distance = haversine(sensor_lat, sensor_lon, cell["latitude"], cell["longitude"])
            fspl = 20 * math.log10(slant_distance) + 20 * math.log10(config["txFrequency"]) - 147.55
            rcv_power = config["txPower"] - fspl

            if rcv_power >= config["rxSensitivity"]:
                min_detectable_agl = h
                break

        results.append({
            "latitude": cell["latitude"],
            "longitude": cell["longitude"],
            "minDetectableAGL": min_detectable_agl if min_detectable_agl is not None else -1
        })

    return results
