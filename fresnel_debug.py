#!/usr/bin/env python3
"""
Detailed Fresnel zone radius analysis and terrain comparison.
"""

from terrain import get_elevation
import numpy as np
from geopy.distance import geodesic

def analyze_fresnel_radius():
    """Analyze Fresnel zone radius calculations and terrain comparison."""
    
    print("🔍 Fresnel Zone Radius Analysis")
    print("=" * 50)
    
    # Sensor position
    sensor_lat = 51.528210
    sensor_lon = -0.244990
    sensor_alt = 5.0  # Sensor at 5m height
    
    # Cell position (500m south)
    cell_lat = 51.523719
    cell_lon = -0.244990
    
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
    
    # Constants
    c = 3e8  # speed of light
    frequency_hz = 1090e6  # 1090 MHz
    wavelength = c / frequency_hz
    clearance_factor = 0.6
    
    print(f"\n📊 Fresnel Zone Parameters:")
    print(f"  - Frequency: {frequency_hz/1e6:.0f} MHz")
    print(f"  - Wavelength: {wavelength:.6f}m")
    print(f"  - Distance: {distance*1000:.1f}m")
    print(f"  - Clearance factor: {clearance_factor}")
    
    # Calculate maximum Fresnel radius (at midpoint)
    d = distance * 1000  # Convert to meters
    max_fresnel_radius = ((wavelength * d * d) / (2 * d)) ** 0.5
    print(f"  - Max Fresnel radius (at midpoint): {max_fresnel_radius:.3f}m")
    
    print("\n🧪 DETAILED FRESNEL ANALYSIS:")
    print("=" * 50)
    
    for agl in test_heights:
        print(f"\n📡 AGL {agl}m Analysis:")
        print("-" * 30)
        
        # Aircraft position
        aircraft_alt_asl = cell_terrain + agl
        print(f"Aircraft ASL: {aircraft_alt_asl:.1f}m")
        
        # Sample points (t=0.167, 0.333, 0.500, 0.667, 0.833)
        t_values = [0.167, 0.333, 0.500, 0.667, 0.833]
        
        for i, t in enumerate(t_values):
            # Interpolate position along the path
            lat = sensor_lat + t * (cell_lat - sensor_lat)
            lon = sensor_lon + t * (cell_lon - sensor_lon)
            alt = sensor_alt + t * (aircraft_alt_asl - sensor_alt)
            
            # Calculate distances from sensor and aircraft
            d1 = t * d  # Distance from sensor to sample point
            d2 = d - d1  # Distance from sample point to aircraft
            
            # Calculate Fresnel zone radius at this point
            # Formula: r = sqrt((λ * d1 * d2) / (d1 + d2))
            r_fresnel = ((wavelength * d1 * d2) / d) ** 0.5
            
            # Calculate required clearance
            clearance_required = clearance_factor * r_fresnel
            
            # Calculate the altitude of the Fresnel zone centerline
            fresnel_centerline_alt = alt
            
            # Calculate the minimum altitude needed to clear terrain
            terrain_height = get_elevation(lat, lon)
            min_altitude_needed = terrain_height + clearance_required
            
            # Check if we have clearance
            has_clearance = fresnel_centerline_alt >= min_altitude_needed
            margin = fresnel_centerline_alt - min_altitude_needed
            
            print(f"\n  Sample {i+1} (t={t:.3f}):")
            print(f"    - Position: ({lat:.6f}, {lon:.6f})")
            print(f"    - Path altitude: {alt:.1f}m")
            print(f"    - Distances: d1={d1:.1f}m, d2={d2:.1f}m")
            print(f"    - Fresnel radius: {r_fresnel:.3f}m")
            print(f"    - Clearance required: {clearance_required:.3f}m")
            print(f"    - Terrain height: {terrain_height:.1f}m")
            print(f"    - Min altitude needed: {min_altitude_needed:.1f}m")
            print(f"    - Fresnel centerline altitude: {fresnel_centerline_alt:.1f}m")
            print(f"    - Margin: {margin:.1f}m")
            print(f"    - Status: {'✅ CLEAR' if has_clearance else '❌ OBSTRUCTED'}")
            
            # Additional analysis
            print(f"    - Fresnel zone extends from {fresnel_centerline_alt - r_fresnel:.1f}m to {fresnel_centerline_alt + r_fresnel:.1f}m")
            print(f"    - Terrain is at {terrain_height:.1f}m")
            print(f"    - Need {clearance_required:.3f}m clearance above terrain")
        
        print("\n" + "="*50)

if __name__ == "__main__":
    analyze_fresnel_radius() 