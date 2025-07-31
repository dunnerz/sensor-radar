#!/usr/bin/env python3
"""
Test progress tracking locally.
"""

import requests
import json
import time

def test_local_progress():
    """Test progress tracking on local server."""
    
    payload = {
        "sensor_id": "TestRadar1",
        "latitude": 51.493,
        "longitude": -0.0669,
        "height": 5,
        "config": {
            "rxSensitivity": -110,
            "txPower": 20,
            "txFrequency": 1090,
            "maxRange": 2,  # Small range for quick test
            "minHeight": 0,
            "maxHeight": 50,
            "heightRes": 10
        }
    }
    
    print("🚀 Testing local progress tracking...")
    print("📝 Make sure to start the server with: python start_server.py")
    print("⏳ Waiting 3 seconds for server to be ready...")
    time.sleep(3)
    
    try:
        # Test main endpoint
        response = requests.post("http://localhost:8000/", json=payload, timeout=10)
        print(f"✅ Main endpoint status: {response.status_code}")
        print(f"📊 Response: {response.json()}")
        
        if response.status_code == 200:
            job_data = response.json()
            if "job_id" in job_data:
                job_id = job_data["job_id"]
                print(f"🎯 Job ID: {job_id}")
                
                # Monitor progress
                print("\n📈 Monitoring progress...")
                for i in range(10):  # Check 10 times
                    progress_res = requests.get(f"http://localhost:8000/progress/{job_id}", timeout=5)
                    if progress_res.status_code == 200:
                        progress_data = progress_res.json()
                        status = progress_data["status"]
                        
                        if status == "completed":
                            print(f"🎉 Completed! Found {progress_data['total_points']} coverage points")
                            break
                        elif status == "error":
                            print(f"❌ Error: {progress_data.get('detail', 'Unknown error')}")
                            break
                        else:
                            progress = progress_data.get("progress", 0)
                            processed = progress_data.get("processed_cells", 0)
                            total = progress_data.get("total_cells", 0)
                            print(f"⏳ Progress: {progress}% ({processed}/{total} cells)")
                            time.sleep(1)
                    else:
                        print(f"❌ Progress check failed: {progress_res.status_code}")
                        break
            else:
                print("❌ No job_id in response - old system detected")
        else:
            print(f"❌ Main endpoint failed: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure the server is running with: python start_server.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_local_progress() 