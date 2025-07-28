import requests
import json

# Load test input
with open("sample_request_range_1000.json") as f:
    payload = json.load(f)

# Send request to local Flask app
response = requests.post("http://localhost:5000/compute-coverage", json=payload)

# Print results
print("Status Code:", response.status_code)
print("Response JSON:", response.json())
