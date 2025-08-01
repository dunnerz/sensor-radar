#!/usr/bin/env python3
"""
Debug script to test line-of-sight calculation for cells close to sensor.
"""

from terrain import get_elevation
from utils import true_fresnel_check
import numpy as np

def debug_close_cell():
    """Debug line-of-sight calculation for a cell very close to sensor."""
    
    print("🔍 Debugging Line-of-Sight Calculation")
    print("=" * 50)
    
    # Sensor position
    sensor_lat = 51.528210
    sensor_lon = -0.244990
    sensor_alt = 5.0  # Sensor at 5m height
    
    # Test cell very close to sensor (1km away)
    cell_lat = 51.519227  # 1km south
    cell_lon = -0.244990  # Same longitude
    
    print(f"📍 Sensor: ({sensor_lat}, {sensor_lon}, {sensor_alt}m)")
    print(f"📍 Cell: ({cell_lat}, {cell_lon})")
    
    # Get terrain elevations
    sensor_terrain = get_elevation(sensor_lat, sensor_lon)
    cell_terrain = get_elevation(cell_lat, cell_lon)
    
    print(f"🏔️ Sensor terrain: {sensor_terrain}m")
    print(f"🏔️ Cell terrain: {cell_terrain}m")
    
    # Calculate distance
    from geopy.distance import geodesic
    distance = geodesic((sensor_lat, sensor_lon), (cell_lat, cell_lon)).km
    print(f"📏 Distance: {distance:.2f}km")
    
    # Test different AGL heights
    test_heights = [0, 20, 40, 60, 80, 100, 120, 140, 160, 180, 200]
    
    print("\n🧪 Testing Line-of-Sight at Different Heights:")
    print("-" * 50)
    
    for agl in test_heights:
        # Aircraft position
        aircraft_alt_asl = cell_terrain + agl
        aircraft_pos = (cell_lat, cell_lon, aircraft_alt_asl)
        sensor_pos = (sensor_lat, sensor_lon, sensor_alt)
        
        # Test line-of-sight
        frequency_hz = 1090e6  # 1090 MHz
        los_clear = true_fresnel_check(sensor_pos, aircraft_pos, get_elevation, frequency_hz, debug=False)
        
        print(f"AGL {agl:3d}m -> Aircraft ASL {aircraft_alt_asl:5.1f}m -> LOS: {'✅' if los_clear else '❌'}")
        
        if los_clear:
            print(f"  ✅ FOUND MINIMUM AGL: {agl}m")
            break
    
    print("\n🔍 Detailed Analysis of First Clear Height:")
    if los_clear:
        # Re-run with debug enabled
        aircraft_alt_asl = cell_terrain + agl
        aircraft_pos = (cell_lat, cell_lon, aircraft_alt_asl)
        sensor_pos = (sensor_lat, sensor_lon, sensor_alt)
        
        print(f"\nTesting AGL {agl}m with debug:")
        true_fresnel_check(sensor_pos, aircraft_pos, get_elevation, frequency_hz, debug=True)

if __name__ == "__main__":
    debug_close_cell() 