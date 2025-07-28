from flask import Flask, request, jsonify
import numpy as np
import json
import scipy.io

app = Flask(__name__)

# Load and preprocess cells once
mat = scipy.io.loadmat("england-cells.mat")
cells_raw = mat["cells"][0]
cells = np.array([[cell["latitude"][0][0], cell["longitude"][0][0]] for cell in cells_raw])

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    d_phi = np.radians(lat2 - lat1)
    d_lambda = np.radians(lon2 - lon1)
    a = np.sin(d_phi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(d_lambda / 2.0) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))

@app.route("/compute-coverage", methods=["POST"])
def compute_coverage():
    try:
        data = request.get_json()
        sensor_id = data["sensor_id"]
        sensor_position = data["sensor_position"]
        config = data["config"]

        sensor_lat, sensor_lon, sensor_alt = sensor_position
        max_range = config["maxRange"]
        rx_sensitivity = config["rxSensitivity"]
        tx_power = config["txPower"]
        tx_freq = config["txFrequency"]
        min_height = config["minHeight"]
        max_height = config["maxHeight"]
        height_res = config["heightRes"]

        # Vectorised distance calculation using haversine
        distances = haversine(sensor_lat, sensor_lon, cells[:, 0], cells[:, 1])
        in_range_mask = distances < max_range
        local_cells = cells[in_range_mask]
        distances = distances[in_range_mask]

        if local_cells.shape[0] == 0:
            return jsonify({"sensor_id": sensor_id, "result": []})

        min_height_coverage = np.full(local_cells.shape[0], np.nan)

        heights = np.arange(min_height, max_height + 1, height_res)
        for h in heights:
            still_needed = np.isnan(min_height_coverage)
            if not np.any(still_needed):
                break
            d = distances[still_needed]
            # Vectorised free-space path loss model
            path_loss = 20 * np.log10(d + 1e-6) + 20 * np.log10(tx_freq) - 147.55
            received_power = tx_power - path_loss
            hits = received_power > rx_sensitivity
            indices = np.where(still_needed)[0][hits]
            min_height_coverage[indices] = h

        result = [{"id": int(i), "height": float(h)} for i, h in enumerate(min_height_coverage) if not np.isnan(h)]
        return jsonify({"sensor_id": sensor_id, "result": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
