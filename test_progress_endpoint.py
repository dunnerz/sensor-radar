#!/usr/bin/env python3
"""
Simple test to check if the progress endpoint is working.
"""

import requests
import json

def test_progress_endpoint():
    """Test the progress endpoint directly."""
    
    # Test 1: Check if the main endpoint still works with old format
    print("🔍 Testing main endpoint...")
    payload = {
        "sensor_id": "TestRadar1",
        "latitude": 51.493,
        "longitude": -0.0669,
        "height": 5,
        "config": {
            "rxSensitivity": -110,
            "txPower": 20,
            "txFrequency": 1090,
            "maxRange": 1,  # Very small range for quick test
            "minHeight": 0,
            "maxHeight": 50,
            "heightRes": 10
        }
    }
    
    try:
        response = requests.post("https://sensor-radar.onrender.com/", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Check if it's the new progress format or old format
        response_data = response.json()
        if "job_id" in response_data:
            print("✅ New progress system detected!")
            job_id = response_data["job_id"]
            
            # Test progress endpoint
            print(f"\n🔍 Testing progress endpoint for job: {job_id}")
            progress_response = requests.get(f"https://sensor-radar.onrender.com/progress/{job_id}", timeout=10)
            print(f"Progress Status: {progress_response.status_code}")
            print(f"Progress Response: {progress_response.json()}")
            
        else:
            print("❌ Old system detected - progress tracking not deployed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Check if progress endpoint exists
    print(f"\n🔍 Testing progress endpoint directly...")
    try:
        test_response = requests.get("https://sensor-radar.onrender.com/progress/test-job", timeout=10)
        print(f"Direct Progress Status: {test_response.status_code}")
        print(f"Direct Progress Response: {test_response.text}")
    except Exception as e:
        print(f"❌ Progress endpoint error: {e}")

if __name__ == "__main__":
    test_progress_endpoint() 