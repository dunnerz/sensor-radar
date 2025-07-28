
from flask import Flask, request, jsonify
from geopy.distance import geodesic
import numpy as np
import json
import scipy.io

app = Flask(__name__)

# Load cell data once on startup
mat = scipy.io.loadmat("england-cells.mat")
cells_raw = mat["cells"][0]
cells = [{"latitude": cell["latitude"][0][0], "longitude": cell["longitude"][0][0]} for cell in cells_raw]

@app.route("/compute-coverage", methods=["POST"])
def compute_coverage():
    try:
        data = request.get_json()
        sensor_id = data["sensor_id"]
        sensor_position = data["sensor_position"]  # [lat, lon, height]
        config = data["config"]

        sensor_lat, sensor_lon, sensor_alt = sensor_position
        max_range = config["maxRange"]
        rx_sensitivity = config["rxSensitivity"]
        tx_power = config["txPower"]
        tx_freq = config["txFrequency"]
        min_height = config["minHeight"]
        max_height = config["maxHeight"]
        height_res = config["heightRes"]

        local_cells = []
        for cell in cells:
            d = geodesic((sensor_lat, sensor_lon), (cell["latitude"], cell["longitude"])).meters
            if d < max_range:
                cell["distance"] = d
                local_cells.append(cell)

        min_height_coverage = [np.nan] * len(local_cells)

        for h in range(min_height, max_height + 1, height_res):
            for i, cell in enumerate(local_cells):
                if np.isnan(min_height_coverage[i]):
                    d = cell["distance"]
                    path_loss = 20 * np.log10(d + 1e-6) + 20 * np.log10(tx_freq) - 147.55
                    received_power = tx_power - path_loss
                    if received_power > rx_sensitivity:
                        min_height_coverage[i] = h

        output = []
        for i, cell in enumerate(local_cells):
            if not np.isnan(min_height_coverage[i]):
                output.append({"id": i, "height": min_height_coverage[i]})

        return jsonify({"sensor_id": sensor_id, "result": output})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
