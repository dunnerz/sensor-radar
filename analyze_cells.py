#!/usr/bin/env python3
"""
Detailed cell analysis script to verify AGL results.
"""

import requests
import numpy as np
from geopy.distance import geodesic
import json
from datetime import datetime

def analyze_individual_cells():
    """Analyze individual cells to verify AGL results."""
    
    print("🔍 Detailed Cell Analysis")
    print("=" * 50)
    
    # Test configuration
    test_config = {
        "sensor_id": "cell-analysis-test",
        "latitude": 51.528210,
        "longitude": -0.244990,
        "height": 5.0,
        "config": {
            "maxRange": 20.0,
            "minHeight": 0,
            "maxHeight": 400,
            "heightRes": 20,
            "txFrequency": 1090,
            "txPower": 20,
            "txGain": 0,
            "rxGain": 0,
            "rxSensitivity": -79,
            "gridResolution": 1.0,
            "fresnelSamplingDensity": 500
        }
    }
    
    sensor_lat = test_config['latitude']
    sensor_lon = test_config['longitude']
    
    print(f"📍 Sensor location: {sensor_lat}, {sensor_lon}")
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
            
        import time
        time.sleep(1)
    
    # Analyze results
    print("\n🔍 ANALYZING CELLS:")
    print("=" * 50)
    
    # Calculate distances and sort cells
    cells_with_distance = []
    
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
    print("📍 CLOSEST CELLS (should have LOW AGL):")
    print("-" * 40)
    for i, cell in enumerate(cells_with_distance[:10]):
        print(f"Cell {i+1}: Distance={cell['distance']:.2f}km, AGL={cell['agl']}m")
    
    print()
    
    # Show farthest cells
    print("📍 FARTHEST CELLS (should have HIGH AGL):")
    print("-" * 40)
    for i, cell in enumerate(cells_with_distance[-10:]):
        print(f"Cell {i+1}: Distance={cell['distance']:.2f}km, AGL={cell['agl']}m")
    
    print()
    
    # Statistical analysis
    distances = [cell['distance'] for cell in cells_with_distance]
    agl_values = [cell['agl'] for cell in cells_with_distance]
    
    # Calculate correlation
    correlation = np.corrcoef(distances, agl_values)[0, 1]
    
    print("📈 STATISTICAL ANALYSIS:")
    print("-" * 40)
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
    print("-" * 40)
    
    # Split into distance ranges
    close_cells = [cell for cell in cells_with_distance if cell['distance'] <= 5]
    mid_cells = [cell for cell in cells_with_distance if 5 < cell['distance'] <= 10]
    far_cells = [cell for cell in cells_with_distance if cell['distance'] > 10]
    
    print(f"Close cells (0-5km): {len(close_cells)} cells")
    if close_cells:
        close_agl = [cell['agl'] for cell in close_cells]
        print(f"  - Mean AGL: {np.mean(close_agl):.1f}m")
        print(f"  - Min AGL: {np.min(close_agl)}m")
        print(f"  - Max AGL: {np.max(close_agl)}m")
    
    print(f"Mid cells (5-10km): {len(mid_cells)} cells")
    if mid_cells:
        mid_agl = [cell['agl'] for cell in mid_cells]
        print(f"  - Mean AGL: {np.mean(mid_agl):.1f}m")
        print(f"  - Min AGL: {np.min(mid_agl)}m")
        print(f"  - Max AGL: {np.max(mid_agl)}m")
    
    print(f"Far cells (10-20km): {len(far_cells)} cells")
    if far_cells:
        far_agl = [cell['agl'] for cell in far_cells]
        print(f"  - Mean AGL: {np.mean(far_agl):.1f}m")
        print(f"  - Min AGL: {np.min(far_agl)}m")
        print(f"  - Max AGL: {np.max(far_agl)}m")
    
    print()
    
    # Check for anomalies
    print("🔍 ANOMALY DETECTION:")
    print("-" * 40)
    
    # Find cells with unexpectedly high AGL close to sensor
    close_high_agl = [cell for cell in close_cells if cell['agl'] > 100]
    if close_high_agl:
        print(f"❌ Found {len(close_high_agl)} cells close to sensor with AGL > 100m:")
        for cell in close_high_agl[:5]:  # Show first 5
            print(f"  - Distance: {cell['distance']:.2f}km, AGL: {cell['agl']}m")
    
    # Find cells with unexpectedly low AGL far from sensor
    far_low_agl = [cell for cell in far_cells if cell['agl'] < 50]
    if far_low_agl:
        print(f"❌ Found {len(far_low_agl)} cells far from sensor with AGL < 50m:")
        for cell in far_low_agl[:5]:  # Show first 5
            print(f"  - Distance: {cell['distance']:.2f}km, AGL: {cell['agl']}m")
    
    if not close_high_agl and not far_low_agl:
        print("✅ No obvious anomalies detected")
    
    print()
    
    # Detailed analysis of first few cells
    print("🔬 DETAILED ANALYSIS OF FIRST 5 CELLS:")
    print("-" * 40)
    
    for i, cell in enumerate(cells_with_distance[:5]):
        print(f"\nCell {i+1}:")
        print(f"  - Coordinates: ({cell['lat']:.6f}, {cell['lon']:.6f})")
        print(f"  - Distance from sensor: {cell['distance']:.2f}km")
        print(f"  - AGL: {cell['agl']}m")
        
        # Expected behavior
        if cell['distance'] <= 5 and cell['agl'] > 100:
            print(f"  - ⚠️ UNEXPECTED: Close cell with high AGL")
        elif cell['distance'] > 10 and cell['agl'] < 50:
            print(f"  - ⚠️ UNEXPECTED: Far cell with low AGL")
        else:
            print(f"  - ✅ Expected behavior")
    
    return cells_with_distance

if __name__ == "__main__":
    analyze_individual_cells() 