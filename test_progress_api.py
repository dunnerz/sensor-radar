#!/usr/bin/env python3
"""
Test script to demonstrate progress tracking in the API.
"""

import requests
import json
import time

def test_progress_tracking():
    """Test the progress tracking functionality."""
    
    # Test configuration (smaller range for faster testing)
    payload = {
        "sensor_id": "TestRadar1",
        "latitude": 51.493,
        "longitude": -0.0669,
        "height": 5,
        "config": {
            "rxSensitivity": -110,
            "txPower": 20,
            "txFrequency": 1090,
            "maxRange": 5,  # Smaller range for testing
            "minHeight": 0,
            "maxHeight": 100,
            "heightRes": 20
        }
    }
    
    print("🚀 Starting coverage computation with progress tracking...")
    
    # Step 1: Start the computation
    response = requests.post("http://localhost:8000/", json=payload)
    
    if response.status_code != 200:
        print(f"❌ Error starting computation: {response.text}")
        return
    
    job_data = response.json()
    job_id = job_data["job_id"]
    print(f"✅ Job started with ID: {job_id}")
    print(f"📊 Status: {job_data['status']}")
    print(f"💡 Message: {job_data['message']}")
    
    # Step 2: Monitor progress
    print("\n📈 Monitoring progress...")
    while True:
        progress_response = requests.get(f"http://localhost:8000/progress/{job_id}")
        
        if progress_response.status_code != 200:
            print(f"❌ Error getting progress: {progress_response.text}")
            break
        
        progress_data = progress_response.json()
        status = progress_data["status"]
        
        if status == "completed":
            print(f"🎉 Computation completed!")
            print(f"📊 Total coverage points: {progress_data['total_points']}")
            if progress_data['results']:
                print(f"📍 Sample result: {progress_data['results'][0]}")
            break
        
        elif status == "error":
            print(f"❌ Computation failed: {progress_data.get('detail', 'Unknown error')}")
            break
        
        else:
            progress = progress_data.get("progress", 0)
            processed = progress_data.get("processed_cells", 0)
            total = progress_data.get("total_cells", 0)
            
            print(f"⏳ Progress: {progress}% ({processed}/{total} cells processed)")
            
            # Wait before checking again
            time.sleep(1)
    
    print("\n✅ Progress tracking test completed!")

if __name__ == "__main__":
    test_progress_tracking() 