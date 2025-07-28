import requests
import json

with open("sample_request_range_1000.json") as f:
    payload = json.load(f)

# Replace with your actual Render URL
res = requests.post("https://sensor-radar.onrender.com", json=payload)

print("Status Code:", res.status_code)
print("Response JSON:", res.json())
print("Raw Response Text:", res.text)

