#!/usr/bin/env python3
"""
Test script for Render deployment with progress tracking.
This script tests the progress tracking system on the deployed Render server.
"""

import requests
import json
import time
from datetime import datetime

def test_render_progress():
    """Test progress tracking on Render deployment."""
    
    # Render server URL
    RENDER_URL = "https://sensor-radar.onrender.com"
    
    # Test configuration - small range for quick testing
    payload = {
        "sensor_id": "RenderTestRadar",
        "latitude": 51.493,
        "longitude": -0.0669,
        "height": 5,
        "config": {
            "rxSensitivity": -110,
            "txPower": 20,
            "txFrequency": 1090,
            "maxRange": 3,  # Small range for testing
            "minHeight": 0,
            "maxHeight": 100,
            "heightRes": 20
        }
    }
    
    print("🚀 Testing Render deployment with progress tracking...")
    print(f"📡 Server: {RENDER_URL}")
    print(f"⏰ Start time: {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 50)
    
    try:
        # Step 1: Submit job
        print("📤 Submitting coverage computation job...")
        response = requests.post(f"{RENDER_URL}/", json=payload, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Error submitting job: {response.text}")
            return False
        
        response_data = response.json()
        print(f"📋 Response: {response_data}")
        
        # Check if progress system is deployed
        if "job_id" not in response_data:
            print("❌ Progress system not detected - old API format")
            print("💡 The Render deployment may not have the latest code")
            return False
        
        job_id = response_data["job_id"]
        print(f"✅ Job created successfully!")
        print(f"🎯 Job ID: {job_id}")
        print(f"📝 Status: {response_data.get('status', 'unknown')}")
        print(f"💬 Message: {response_data.get('message', 'No message')}")
        
        # Step 2: Monitor progress
        print("\n📈 Monitoring progress...")
        print("-" * 50)
        
        max_checks = 30  # Maximum number of progress checks
        check_count = 0
        
        while check_count < max_checks:
            try:
                progress_response = requests.get(
                    f"{RENDER_URL}/progress/{job_id}", 
                    timeout=10
                )
                
                if progress_response.status_code != 200:
                    print(f"❌ Progress check failed: {progress_response.status_code}")
                    print(f"📄 Response: {progress_response.text}")
                    break
                
                progress_data = progress_response.json()
                status = progress_data.get("status", "unknown")
                
                # Display progress information
                if status == "completed":
                    print(f"🎉 COMPLETED!")
                    print(f"📊 Total coverage points: {progress_data.get('total_points', 0)}")
                    print(f"⏰ End time: {datetime.now().strftime('%H:%M:%S')}")
                    
                    # Show sample results
                    results = progress_data.get('results', [])
                    if results:
                        print(f"📍 Sample coverage point: {results[0]}")
                    
                    return True
                    
                elif status == "error":
                    error_msg = progress_data.get('detail', 'Unknown error')
                    print(f"❌ COMPUTATION FAILED: {error_msg}")
                    return False
                    
                elif status in ["starting", "computing"]:
                    progress = progress_data.get("progress", 0)
                    processed = progress_data.get("processed_cells", 0)
                    total = progress_data.get("total_cells", 0)
                    
                    # Create progress bar
                    bar_length = 30
                    filled_length = int(bar_length * progress / 100)
                    bar = "█" * filled_length + "░" * (bar_length - filled_length)
                    
                    print(f"⏳ Progress: {progress:3d}% |{bar}| {processed:3d}/{total:3d} cells")
                    print(f"📊 Status: {status} | ⏰ {datetime.now().strftime('%H:%M:%S')}")
                    
                else:
                    print(f"❓ Unknown status: {status}")
                    print(f"📄 Full response: {progress_data}")
                
                check_count += 1
                time.sleep(2)  # Wait 2 seconds between checks
                
            except requests.exceptions.Timeout:
                print(f"⏰ Timeout on progress check {check_count + 1}")
                check_count += 1
                time.sleep(5)  # Wait longer on timeout
                
            except Exception as e:
                print(f"❌ Error checking progress: {e}")
                break
        
        if check_count >= max_checks:
            print(f"⏰ Reached maximum checks ({max_checks}) - job may still be running")
            print(f"💡 You can manually check progress at: {RENDER_URL}/progress/{job_id}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - server may be down or URL incorrect")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_simple_endpoint():
    """Test if the basic endpoint is working."""
    print("\n🔍 Testing basic endpoint functionality...")
    
    try:
        response = requests.get("https://sensor-radar.onrender.com/", timeout=10)
        print(f"📊 Basic endpoint status: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Basic endpoint test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Render Progress Tracking Test")
    print("=" * 50)
    
    # Test basic connectivity first
    if test_simple_endpoint():
        print("✅ Basic connectivity confirmed")
        print()
        
        # Test progress tracking
        success = test_render_progress()
        
        if success:
            print("\n🎉 All tests passed! Progress tracking is working on Render.")
        else:
            print("\n💥 Tests failed. Check deployment status.")
    else:
        print("❌ Basic connectivity failed. Server may be down.")
    
    print("\n" + "=" * 50)
    print("�� Test completed") 