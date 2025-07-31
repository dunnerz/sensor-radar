#!/usr/bin/env python3
"""
API Test Script for Deployed Sensor Coverage API
Calls the Render-hosted API and provides detailed logging and progress reporting.
"""

import requests
import time
import json
import numpy as np
from datetime import datetime

# API Configuration
API_BASE_URL = "https://sensor-radar.onrender.com"

def test_api_coverage():
    """Test coverage calculation using the deployed API."""
    
    print("🚀 API Coverage Test - Deployed Service")
    print("=" * 60)
    print(f"🌐 API URL: {API_BASE_URL}")
    print()
    
    # Test configuration - 5km range with 10m height resolution
    test_config = {
        "sensor_id": "api-test-sensor",
        "latitude": 51.5074,  # London coordinates
        "longitude": -0.1278,
        "height": 5.0,  # 5m sensor height
        "config": {
            "maxRange": 5.0,  # 5km range
            "minHeight": 0,
            "maxHeight": 200,  # 200m max height
            "heightRes": 10,  # 10m height resolution
            "txFrequency": 2400,
            "txPower": 30,
            "txGain": 0,
            "rxGain": 0,
            "rxSensitivity": -90,
            "gridResolution": 0.5,
            "fresnelSamplingDensity": 500,
            "maxCells": 100  # Limit to 100 cells for faster testing
        }
    }
    
    print("📋 Test Configuration:")
    print(f"   📍 Sensor location: {test_config['latitude']}, {test_config['longitude']}")
    print(f"   📡 Range: {test_config['config']['maxRange']}km")
    print(f"   🛩️ Height range: {test_config['config']['minHeight']}-{test_config['config']['maxHeight']}m")
    print(f"   🔧 Height resolution: {test_config['config']['heightRes']}m")
    print(f"   🔧 Grid resolution: {test_config['config']['gridResolution']}km")
    print(f"   📊 Max cells: {test_config['config']['maxCells']}")
    print()
    
    # Test API connectivity first
    print("🔍 Testing API connectivity...")
    try:
        health_response = requests.get(f"{API_BASE_URL}/")
        if health_response.status_code == 200:
            print("✅ API is accessible")
        else:
            print(f"⚠️ API health check returned: {health_response.status_code}")
    except Exception as e:
        print(f"❌ API connectivity error: {e}")
        return
    
    # Test terrain debug endpoint
    print("🔍 Checking terrain data status...")
    try:
        terrain_response = requests.get(f"{API_BASE_URL}/debug/terrain")
        if terrain_response.status_code == 200:
            terrain_data = terrain_response.json()
            file_size_mb = terrain_data.get("terrain_file", {}).get("size_mb", 0)
            terrain_valid = terrain_data.get("terrain_validation", False)
            print(f"✅ Terrain file size: {file_size_mb}MB")
            print(f"✅ Terrain validation: {terrain_valid}")
        else:
            print(f"⚠️ Terrain debug returned: {terrain_response.status_code}")
    except Exception as e:
        print(f"❌ Terrain debug error: {e}")
    
    print()
    
    # Submit job
    print("🔄 Submitting coverage computation job...")
    start_time = time.time()
    
    try:
        response = requests.post(f"{API_BASE_URL}/", json=test_config, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Job submission failed: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        job_data = response.json()
        job_id = job_data.get("job_id")
        status = job_data.get("status")
        message = job_data.get("message")
        
        print(f"✅ Job submitted successfully!")
        print(f"📋 Job ID: {job_id}")
        print(f"📊 Status: {status}")
        print(f"💬 Message: {message}")
        print()
        
    except requests.exceptions.Timeout:
        print("❌ Job submission timed out")
        return
    except Exception as e:
        print(f"❌ Job submission error: {e}")
        return
    
    # Monitor progress
    print("📊 Monitoring progress...")
    print("=" * 60)
    
    last_progress = -1
    last_stage = ""
    last_substage = ""
    consecutive_errors = 0
    max_errors = 5
    
    while True:
        try:
            progress_response = requests.get(f"{API_BASE_URL}/progress/{job_id}", timeout=10)
            
            if progress_response.status_code == 200:
                progress_data = progress_response.json()
                consecutive_errors = 0  # Reset error counter on success
                
                # Show progress
                progress = progress_data.get("progress", 0)
                stage = progress_data.get("stage", "")
                substage = progress_data.get("substage", "")
                status = progress_data.get("status", "")
                
                # Only show progress if it changed
                if (progress != last_progress or 
                    stage != last_stage or 
                    substage != last_substage):
                    
                    elapsed = time.time() - start_time
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    print(f"[{timestamp}] Progress: {progress}% | {stage} | {substage} | {elapsed:.1f}s")
                    
                    last_progress = progress
                    last_stage = stage
                    last_substage = substage
                
                # Check if job is complete
                if status == "completed":
                    elapsed = time.time() - start_time
                    results = progress_data.get("results", [])
                    total_points = progress_data.get("total_points", 0)
                    
                    print("=" * 60)
                    print("🎉 COMPLETED!")
                    print(f"📊 Results:")
                    print(f"   • Total cells processed: {len(results)}")
                    print(f"   • Total points: {total_points}")
                    print(f"   • Total time: {elapsed:.1f} seconds")
                    print(f"   • Average time per cell: {elapsed/len(results):.3f}s" if results else "   • No cells processed")
                    
                    # Calculate detailed statistics
                    if results:
                        agl_values = [result.get('agl', 0) for result in results]
                        terrain_values = [result.get('terrain_asl', 0) for result in results]
                        
                        cells_with_zero_agl = len([agl for agl in agl_values if agl == 0])
                        cells_with_coverage = len([agl for agl in agl_values if agl > 0])
                        min_agl = min(agl_values) if agl_values else 0
                        max_agl = max(agl_values) if agl_values else 0
                        mean_agl = np.mean(agl_values) if agl_values else 0
                        
                        min_terrain = min(terrain_values) if terrain_values else 0
                        max_terrain = max(terrain_values) if terrain_values else 0
                        mean_terrain = np.mean(terrain_values) if terrain_values else 0
                        
                        print()
                        print("📈 DETAILED RESULTS:")
                        print(f"   • Number of cells computed: {len(results)}")
                        print(f"   • Number of cells with 0m AGL (ground coverage): {cells_with_zero_agl}")
                        print(f"   • Number of cells with >0m AGL (airborne coverage): {cells_with_coverage}")
                        print(f"   • AGL Range: {min_agl}m - {max_agl}m (mean: {mean_agl:.1f}m)")
                        print(f"   • Terrain Range: {min_terrain:.1f}m - {max_terrain:.1f}m ASL (mean: {mean_terrain:.1f}m)")
                        
                        # Show sample results
                        print()
                        print("📋 SAMPLE RESULTS (first 5 cells):")
                        for i, result in enumerate(results[:5]):
                            print(f"   {i+1}. Lat: {result['latitude']:.6f}, Lon: {result['longitude']:.6f}, AGL: {result['agl']}m, Terrain: {result['terrain_asl']:.1f}m ASL")
                    
                    print()
                    print("✅ API test completed successfully!")
                    break
                    
                elif status == "failed":
                    error = progress_data.get("error", "Unknown error")
                    print(f"❌ Job failed: {error}")
                    break
                    
            else:
                consecutive_errors += 1
                print(f"⚠️ Progress check failed: {progress_response.status_code} (error {consecutive_errors}/{max_errors})")
                
                if consecutive_errors >= max_errors:
                    print("❌ Too many consecutive errors, stopping")
                    break
                    
        except requests.exceptions.Timeout:
            consecutive_errors += 1
            print(f"⚠️ Progress check timed out (error {consecutive_errors}/{max_errors})")
            
            if consecutive_errors >= max_errors:
                print("❌ Too many consecutive timeouts, stopping")
                break
                
        except Exception as e:
            consecutive_errors += 1
            print(f"⚠️ Progress check error: {e} (error {consecutive_errors}/{max_errors})")
            
            if consecutive_errors >= max_errors:
                print("❌ Too many consecutive errors, stopping")
                break
            
        time.sleep(1.0)  # Poll every 1 second

if __name__ == "__main__":
    test_api_coverage() 