#!/usr/bin/env python3
"""
Detailed Fresnel analysis for a specific cell within 1km.
"""

from terrain import get_elevation
from utils import true_fresnel_check
import numpy as np
from geopy.distance import geodesic

def analyze_fresnel_samples():
    """Analyze Fresnel samples for a cell within 1km."""
    
    print("🔍 Fresnel Sample Analysis")
    print("=" * 50)
    
    # Sensor position
    sensor_lat = 51.528210
    sensor_lon = -0.244990
    sensor_alt = 5.0  # Sensor at 5m height
    
    # Pick a cell within 1km (500m south)
    cell_lat = 51.523719  # ~500m south
    cell_lon = -0.244990  # Same longitude
    
    print(f"📍 Sensor: ({sensor_lat}, {sensor_lon}, {sensor_alt}m)")
    print(f"📍 Cell: ({cell_lat}, {cell_lon})")
    
    # Get terrain elevations
    sensor_terrain = get_elevation(sensor_lat, sensor_lon)
    cell_terrain = get_elevation(cell_lat, cell_lon)
    
    print(f"🏔️ Sensor terrain: {sensor_terrain}m")
    print(f"🏔️ Cell terrain: {cell_terrain}m")
    
    # Calculate distance
    distance = geodesic((sensor_lat, sensor_lon), (cell_lat, cell_lon)).km
    print(f"📏 Distance: {distance:.2f}km")
    
    # Test different AGL heights
    test_heights = [0, 20, 40]
    
    print("\n🧪 FRESNEL SAMPLE ANALYSIS:")
    print("=" * 50)
    
    for agl in test_heights:
        print(f"\n📡 AGL {agl}m Analysis:")
        print("-" * 30)
        
        # Aircraft position
        aircraft_alt_asl = cell_terrain + agl
        aircraft_pos = (cell_lat, cell_lon, aircraft_alt_asl)
        sensor_pos = (sensor_lat, sensor_lon, sensor_alt)
        
        print(f"Aircraft ASL: {aircraft_alt_asl:.1f}m")
        
        # Test line-of-sight with debug enabled
        frequency_hz = 1090e6  # 1090 MHz
        los_clear = true_fresnel_check(sensor_pos, aircraft_pos, get_elevation, frequency_hz, fresnel_samples=7, debug=True)
        
        print(f"Line-of-sight result: {'✅ CLEAR' if los_clear else '❌ OBSTRUCTED'}")
        
        # Calculate Fresnel zone parameters manually
        c = 3e8  # speed of light
        wavelength = c / frequency_hz
        d = distance * 1000  # Convert to meters
        
        print(f"\n📊 Fresnel Zone Parameters:")
        print(f"  - Wavelength: {wavelength:.6f}m")
        print(f"  - Distance: {d:.1f}m")
        print(f"  - Max Fresnel radius: {((wavelength * d * d) / (2 * d)) ** 0.5:.3f}m")
        
        # Calculate sample points manually
        print(f"\n📍 Sample Points (t=0.167, 0.333, 0.500, 0.667, 0.833):")
        
        t_values = [0.167, 0.333, 0.500, 0.667, 0.833]
        
        for i, t in enumerate(t_values):
            # Interpolate position
            lat = sensor_lat + t * (cell_lat - sensor_lat)
            lon = sensor_lon + t * (cell_lon - sensor_lon)
            alt = sensor_alt + t * (aircraft_alt_asl - sensor_alt)
            
            # Calculate distances
            d1 = t * d
            d2 = d - d1
            
            # Calculate Fresnel radius
            r_fresnel = ((wavelength * d1 * d2) / d) ** 0.5
            
            # Get terrain at this point
            terrain_height = get_elevation(lat, lon)
            
            # Calculate clearance
            clearance_factor = 0.6
            clearance_height = alt - (clearance_factor * r_fresnel)
            
            print(f"  Sample {i+1}: t={t:.3f}")
            print(f"    - Position: ({lat:.6f}, {lon:.6f}, {alt:.1f}m)")
            print(f"    - Distances: d1={d1:.1f}m, d2={d2:.1f}m")
            print(f"    - Fresnel radius: {r_fresnel:.3f}m")
            print(f"    - Clearance height: {clearance_height:.1f}m")
            print(f"    - Terrain height: {terrain_height:.1f}m")
            print(f"    - Margin: {clearance_height - terrain_height:.1f}m")
            print(f"    - Status: {'✅ CLEAR' if terrain_height < clearance_height else '❌ OBSTRUCTED'}")
        
        print("\n" + "="*50)

if __name__ == "__main__":
    analyze_fresnel_samples() 