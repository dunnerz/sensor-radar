#!/usr/bin/env python3
"""
Test script for UK coverage calculation with specified parameters.
"""

import requests
import time
import json
import numpy as np
from datetime import datetime

def test_uk_coverage():
    """Test coverage calculation with UK parameters."""
    
    print("🚀 UK Coverage Test")
    print("=" * 50)
    
    # Test configuration with your specified parameters
    test_config = {
        "sensor_id": "uk-test-sensor",
        "latitude": 51.528210,
        "longitude": -0.244990,
        "height": 5.0,
        "config": {
            "maxRange": 20.0,  # 20km range
            "minHeight": 0,
            "maxHeight": 400,  # 400m height range
            "heightRes": 20,  # 20m height resolution
            "txFrequency": 1090,
            "txPower": 20,
            "txGain": 0,
            "rxGain": 0,
            "rxSensitivity": -79,  # -79dBm
            "gridResolution": 1.0,  # 1km grid resolution
            "fresnelSamplingDensity": 500
        }
    }
    
    print(f"�� Sensor location: {test_config['latitude']}, {test_config['longitude']}")
    print(f"📡 Range: {test_config['config']['maxRange']}km")
    print(f"🛩️ Height range: {test_config['config']['minHeight']}-{test_config['config']['maxHeight']}m")
    print(f"�� Height resolution: {test_config['config']['heightRes']}m")
    print(f"�� Grid resolution: {test_config['config']['gridResolution']}km")
    print(f"📡 Frequency: {test_config['config']['txFrequency']}MHz")
    print(f"📡 Rx sensitivity: {test_config['config']['rxSensitivity']}dBm")
    print()
    
    # Submit job
    print("🔄 Submitting coverage computation job...")
    response = requests.post("http://localhost:8000/", json=test_config)
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    job_data = response.json()
    job_id = job_data.get("job_id")
    print(f"✅ Job submitted successfully!")
    print(f"📋 Job ID: {job_id}")
    print()
    
    # Monitor progress
    print("📊 Monitoring progress...")
    print("=" * 50)
    
    start_time = time.time()
    last_progress = 0
    
    while True:
        try:
            progress_response = requests.get(f"http://localhost:8000/progress/{job_id}")
            if progress_response.status_code == 200:
                progress_data = progress_response.json()
                
                # Show progress
                progress = progress_data.get("progress", 0)
                stage = progress_data.get("stage", "")
                substage = progress_data.get("substage", "")
                
                # Only show progress if it changed
                if progress != last_progress:
                    elapsed = time.time() - start_time
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] Progress: {progress}% | {stage} | {substage} | {elapsed:.1f}s")
                    last_progress = progress
                
                # Check if job is complete
                if progress_data.get("status") == "completed":
                    elapsed = time.time() - start_time
                    results = progress_data.get("results", [])
                    
                    print("=" * 50)
                    print("🎉 COMPLETED!")
                    print(f"📊 Results:")
                    print(f"   • Total cells processed: {len(results)}")
                    print(f"   • Total time: {elapsed:.1f} seconds")
                    print(f"   • Average time per cell: {elapsed/len(results):.3f}s" if results else "   • No cells processed")
                    
                    # Calculate detailed statistics
                    if results:
                        agl_values = [result.get('agl', 0) for result in results]
                        cells_with_zero_agl = len([agl for agl in agl_values if agl == 0])
                        cells_with_coverage = len([agl for agl in agl_values if agl > 0])
                        min_agl = min(agl_values) if agl_values else 0
                        max_agl = max(agl_values) if agl_values else 0
                        mean_agl = np.mean(agl_values) if agl_values else 0
                        
                        print()
                        print("📈 DETAILED RESULTS:")
                        print(f"   • Number of cells computed: {len(results)}")
                        print(f"   • Number of cells with 0m AGL (ground coverage): {cells_with_zero_agl}")
                        print(f"   • Number of cells with >0m AGL (airborne coverage): {cells_with_coverage}")
                        print(f"   • Minimum AGL: {min_agl}m")
                        print(f"   • Maximum AGL: {max_agl}m")
                        print(f"   • Mean AGL: {mean_agl:.1f}m")
                    
                    print()
                    print("✅ Test completed!")
                    break
                    
            else:
                print(f"❌ Error getting progress: {progress_response.status_code}")
                print(f"Response: {progress_response.text}")
                break
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            break
            
        time.sleep(0.5)  # Poll every 500ms

if __name__ == "__main__":
    test_uk_coverage() 