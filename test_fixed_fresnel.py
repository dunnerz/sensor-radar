#!/usr/bin/env python3
"""
Test the fixed Fresnel zone calculation with original parameters but 2km range.
"""

import requests
import json
import time

def test_fixed_fresnel():
    """Test the fixed Fresnel zone calculation with original parameters but 2km range."""
    
    print("🧪 Testing Fixed Fresnel Zone Calculation")
    print("=" * 50)
    
    # Test configuration using original parameters but 2km range
    test_config = {
        "sensor_id": "fresnel-fix-test-2km",
        "latitude": 51.528210,
        "longitude": -0.244990,
        "height": 5.0,
        "config": {
            "maxRange": 2.0,  # 2km range (reduced from 20km)
            "minHeight": 0,
            "maxHeight": 400,  # 400m height range (same as original)
            "heightRes": 20,  # 20m height resolution (same as original)
            "txFrequency": 1090,
            "txPower": 20,
            "txGain": 0,
            "rxGain": 0,
            "rxSensitivity": -79,
            "gridResolution": 1.0,  # 1km grid resolution (same as original)
            "fresnelSamplingDensity": 500,
            "fresnelSamples": 7  # Same as original
        }
    }
    
    print(f"📋 Test Configuration:")
    print(f"  • Sensor: ({test_config['latitude']}, {test_config['longitude']}, {test_config['height']}m)")
    print(f"  • Range: {test_config['config']['maxRange']}km")
    print(f"  • Height range: {test_config['config']['minHeight']}-{test_config['config']['maxHeight']}m")
    print(f"  • Height resolution: {test_config['config']['heightRes']}m")
    print(f"  • Grid resolution: {test_config['config']['gridResolution']}km")
    print(f"  • Fresnel samples: {test_config['config']['fresnelSamples']}")
    
    # Submit job
    print(f"\n🚀 Submitting test job...")
    response = requests.post("http://localhost:8000/", json=test_config)
    
    if response.status_code != 200:
        print(f"❌ Failed to submit job: {response.status_code}")
        return
    
    result = response.json()
    job_id = result.get('job_id')
    print(f"✅ Job submitted with ID: {job_id}")
    
    # Monitor progress
    print(f"\n📊 Monitoring progress...")
    while True:
        progress_response = requests.get(f"http://localhost:8000/progress/{job_id}")
        
        if progress_response.status_code != 200:
            print(f"❌ Failed to get progress: {progress_response.status_code}")
            break
        
        progress_data = progress_response.json()
        status = progress_data.get('status', 'unknown')
        
        if status == 'completed':
            results = progress_data.get('results', [])
            print(f"\n✅ Job completed!")
            print(f"📊 Results summary:")
            print(f"  • Total cells: {len(results)}")
            
            if results:
                agl_values = [r.get('agl', 0) for r in results if r.get('agl', 0) > 0]
                if agl_values:
                    print(f"  • Min AGL: {min(agl_values)}m")
                    print(f"  • Max AGL: {max(agl_values)}m")
                    print(f"  • Mean AGL: {sum(agl_values)/len(agl_values):.1f}m")
                    print(f"  • Cells with AGL > 0: {len(agl_values)}")
                    
                    # Show some sample results
                    print(f"\n📋 Sample Results (first 10):")
                    for i, result in enumerate(results[:10]):
                        print(f"  {i+1}. ({result.get('latitude', 0):.6f}, {result.get('longitude', 0):.6f}): {result.get('agl', 0)}m AGL")
                    
                    # Compare with original results
                    print(f"\n🔍 Comparison with Original (20km range):")
                    print(f"  • Original min AGL: 20m")
                    print(f"  • Original max AGL: 400m")
                    print(f"  • Original mean AGL: 208.1m")
                    print(f"  • Fixed min AGL: {min(agl_values)}m")
                    print(f"  • Fixed max AGL: {max(agl_values)}m")
                    print(f"  • Fixed mean AGL: {sum(agl_values)/len(agl_values):.1f}m")
                    
                    # Calculate improvement
                    original_mean = 208.1
                    fixed_mean = sum(agl_values)/len(agl_values)
                    improvement = ((original_mean - fixed_mean) / original_mean) * 100
                    print(f"  • Improvement: {improvement:.1f}% reduction in mean AGL")
                    
                else:
                    print(f"  • No cells with AGL > 0")
            break
        elif status == 'failed':
            print(f"❌ Job failed: {progress_data.get('error', 'Unknown error')}")
            break
        else:
            progress = progress_data.get('progress', 0)
            print(f"  Progress: {progress}%")
            time.sleep(1)

if __name__ == "__main__":
    test_fixed_fresnel() 