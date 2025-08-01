#!/usr/bin/env python3
"""
Test with more realistic parameters to verify AGL calculations.
"""

import requests
import time
import json
import numpy as np
from datetime import datetime
from geopy.distance import geodesic

def test_realistic_config():
    """Test with more realistic parameters."""
    
    print("🧪 Testing Realistic Configuration")
    print("=" * 50)
    
    # More realistic configuration
    test_config = {
        "sensor_id": "realistic-test",
        "latitude": 51.528210,
        "longitude": -0.244990,
        "height": 5.0,
        "config": {
            "maxRange": 5.0,  # Reduced to 5km
            "minHeight": 0,
            "maxHeight": 100,  # Reduced to 100m
            "heightRes": 5,  # Reduced to 5m resolution
            "txFrequency": 1090,
            "txPower": 20,
            "txGain": 0,
            "rxGain": 0,
            "rxSensitivity": -79,
            "gridResolution": 0.5,  # Reduced to 500m
            "fresnelSamplingDensity": 500,
            "fresnelSamples": 3  # Reduced sampling
        }
    }
    
    print(f"📍 Sensor location: {test_config['latitude']}, {test_config['longitude']}")
    print(f"📡 Range: {test_config['config']['maxRange']}km")
    print(f"🛩️ Height range: {test_config['config']['minHeight']}-{test_config['config']['maxHeight']}m")
    print(f"🔧 Height resolution: {test_config['config']['heightRes']}m")
    print(f"🔧 Grid resolution: {test_config['config']['gridResolution']}km")
    print(f"🔧 Fresnel samples: {test_config['config']['fresnelSamples']}")
    print()
    
    # Submit job
    print("🔄 Submitting coverage computation job...")
    response = requests.post("http://localhost:8000/", json=test_config)
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        return None
    
    job_data = response.json()
    job_id = job_data.get("job_id")
    print(f"✅ Job submitted successfully!")
    print(f"📋 Job ID: {job_id}")
    print()
    
    # Monitor progress
    print("📊 Monitoring progress...")
    start_time = time.time()
    
    while True:
        try:
            progress_response = requests.get(f"http://localhost:8000/progress/{job_id}")
            if progress_response.status_code == 200:
                progress_data = progress_response.json()
                
                if progress_data.get("status") == "completed":
                    results = progress_data.get("results", [])
                    print(f"✅ Job completed! Analyzing {len(results)} cells...")
                    break
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return None
            
        time.sleep(1)
    
    # Analyze results
    print("\n📊 RESULTS ANALYSIS:")
    print("=" * 50)
    
    # Calculate distances and sort cells
    cells_with_distance = []
    sensor_lat = test_config['latitude']
    sensor_lon = test_config['longitude']
    
    for result in results:
        lat = result.get('latitude', 0)
        lon = result.get('longitude', 0)
        agl = result.get('agl', 0)
        
        if lat != 0 and lon != 0:
            distance = geodesic((sensor_lat, sensor_lon), (lat, lon)).km
            cells_with_distance.append({
                'lat': lat,
                'lon': lon,
                'agl': agl,
                'distance': distance
            })
    
    # Sort by distance
    cells_with_distance.sort(key=lambda x: x['distance'])
    
    print(f"📊 Total valid cells: {len(cells_with_distance)}")
    print()
    
    # Show closest cells
    print("📍 CLOSEST CELLS:")
    print("-" * 30)
    for i, cell in enumerate(cells_with_distance[:10]):
        print(f"Cell {i+1}: Distance={cell['distance']:.2f}km, AGL={cell['agl']}m")
    
    print()
    
    # Show farthest cells
    print("📍 FARTHEST CELLS:")
    print("-" * 30)
    for i, cell in enumerate(cells_with_distance[-10:]):
        print(f"Cell {i+1}: Distance={cell['distance']:.2f}km, AGL={cell['agl']}m")
    
    print()
    
    # Statistical analysis
    distances = [cell['distance'] for cell in cells_with_distance]
    agl_values = [cell['agl'] for cell in cells_with_distance]
    
    correlation = np.corrcoef(distances, agl_values)[0, 1]
    
    print("📈 STATISTICAL ANALYSIS:")
    print("-" * 30)
    print(f"Correlation (distance vs AGL): {correlation:.3f}")
    
    if correlation > 0.5:
        print("✅ POSITIVE correlation: AGL increases with distance (expected)")
    elif correlation < -0.5:
        print("❌ NEGATIVE correlation: AGL decreases with distance (unexpected)")
    else:
        print("⚠️ WEAK correlation: No clear relationship")
    
    print()
    
    # Distance-based analysis
    print("📏 DISTANCE-BASED ANALYSIS:")
    print("-" * 30)
    
    # Split into distance ranges
    close_cells = [cell for cell in cells_with_distance if cell['distance'] <= 1]
    mid_cells = [cell for cell in cells_with_distance if 1 < cell['distance'] <= 2.5]
    far_cells = [cell for cell in cells_with_distance if cell['distance'] > 2.5]
    
    print(f"Close cells (0-1km): {len(close_cells)} cells")
    if close_cells:
        close_agl = [cell['agl'] for cell in close_cells]
        print(f"  - Mean AGL: {np.mean(close_agl):.1f}m")
        print(f"  - Min AGL: {np.min(close_agl)}m")
        print(f"  - Max AGL: {np.max(close_agl)}m")
    
    print(f"Mid cells (1-2.5km): {len(mid_cells)} cells")
    if mid_cells:
        mid_agl = [cell['agl'] for cell in mid_cells]
        print(f"  - Mean AGL: {np.mean(mid_agl):.1f}m")
        print(f"  - Min AGL: {np.min(mid_agl)}m")
        print(f"  - Max AGL: {np.max(mid_agl)}m")
    
    print(f"Far cells (2.5-5km): {len(far_cells)} cells")
    if far_cells:
        far_agl = [cell['agl'] for cell in far_cells]
        print(f"  - Mean AGL: {np.mean(far_agl):.1f}m")
        print(f"  - Min AGL: {np.min(far_agl)}m")
        print(f"  - Max AGL: {np.max(far_agl)}m")
    
    return cells_with_distance

if __name__ == "__main__":
    test_realistic_config() 