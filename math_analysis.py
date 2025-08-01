#!/usr/bin/env python3
"""
Detailed mathematical analysis of the path altitude calculation bug.
"""

from terrain import get_elevation
import numpy as np
from geopy.distance import geodesic

def analyze_path_altitude_bug():
    """Analyze the mathematical error in path altitude calculation."""
    
    print("🔍 MATHEMATICAL ANALYSIS: Path Altitude Calculation Bug")
    print("=" * 60)
    
    # Test case: 500m south of sensor
    sensor_lat = 51.528210
    sensor_lon = -0.244990
    sensor_agl = 5.0  # Sensor is 5m above terrain
    
    cell_lat = 51.523719  # 500m south
    cell_lon = -0.244990
    test_agl = 20.0  # Aircraft is 20m above terrain
    
    print(f"📍 Sensor: ({sensor_lat}, {sensor_lon}, {sensor_agl}m AGL)")
    print(f"📍 Aircraft: ({cell_lat}, {cell_lon}, {test_agl}m AGL)")
    
    # Get terrain elevations
    sensor_terrain = get_elevation(sensor_lat, sensor_lon)
    cell_terrain = get_elevation(cell_lat, cell_lon)
    
    print(f"\n🏔️ TERRAIN HEIGHTS:")
    print(f"  Sensor terrain: {sensor_terrain:.1f}m")
    print(f"  Cell terrain: {cell_terrain:.1f}m")
    
    # Calculate absolute altitudes
    sensor_absolute = sensor_terrain + sensor_agl
    aircraft_absolute = cell_terrain + test_agl
    
    print(f"\n📊 ABSOLUTE ALTITUDES:")
    print(f"  Sensor absolute: {sensor_terrain:.1f}m + {sensor_agl}m = {sensor_absolute:.1f}m")
    print(f"  Aircraft absolute: {cell_terrain:.1f}m + {test_agl}m = {aircraft_absolute:.1f}m")
    
    # Calculate distance
    distance = geodesic((sensor_lat, sensor_lon), (cell_lat, cell_lon)).km
    print(f"\n📏 Distance: {distance:.3f}km")
    
    print(f"\n🚨 CURRENT (WRONG) CALCULATION:")
    print("=" * 40)
    
    # Current wrong calculation (from utils.py line 108)
    alt_diff_wrong = test_agl - sensor_agl  # 20m - 5m = 15m
    print(f"  alt_diff = aircraft_agl - sensor_agl = {test_agl}m - {sensor_agl}m = {alt_diff_wrong}m")
    
    # Test at t=0.5 (middle point)
    t = 0.5
    path_agl_wrong = sensor_agl + t * alt_diff_wrong
    print(f"  At t={t}: path_agl = {sensor_agl}m + {t} × {alt_diff_wrong}m = {path_agl_wrong:.1f}m")
    
    print(f"\n✅ CORRECT CALCULATION:")
    print("=" * 40)
    
    # Correct calculation
    alt_diff_correct = aircraft_absolute - sensor_absolute
    print(f"  alt_diff = aircraft_absolute - sensor_absolute = {aircraft_absolute:.1f}m - {sensor_absolute:.1f}m = {alt_diff_correct:.1f}m")
    
    path_absolute_correct = sensor_absolute + t * alt_diff_correct
    print(f"  At t={t}: path_absolute = {sensor_absolute:.1f}m + {t} × {alt_diff_correct:.1f}m = {path_absolute_correct:.1f}m")
    
    # Get terrain at midpoint for comparison
    mid_lat = sensor_lat + t * (cell_lat - sensor_lat)
    mid_lon = sensor_lon + t * (cell_lon - sensor_lon)
    mid_terrain = get_elevation(mid_lat, mid_lon)
    path_agl_correct = path_absolute_correct - mid_terrain
    
    print(f"  Midpoint terrain: {mid_terrain:.1f}m")
    print(f"  Path AGL (correct): {path_absolute_correct:.1f}m - {mid_terrain:.1f}m = {path_agl_correct:.1f}m")
    
    print(f"\n📊 COMPARISON:")
    print("=" * 40)
    print(f"  Current (wrong) path AGL: {path_agl_wrong:.1f}m")
    print(f"  Correct path AGL: {path_agl_correct:.1f}m")
    print(f"  Difference: {path_agl_correct - path_agl_wrong:.1f}m")
    print(f"  Error factor: {path_agl_correct / path_agl_wrong:.1f}x")
    
    print(f"\n🚨 IMPACT ON FRESNEL CALCULATION:")
    print("=" * 40)
    
    # Fresnel zone calculation
    c = 3e8
    frequency_hz = 1090e6
    wavelength = c / frequency_hz
    clearance_factor = 0.6
    
    d = distance * 1000  # Convert to meters
    d1 = t * d  # Distance from sensor to midpoint
    d2 = d - d1  # Distance from midpoint to aircraft
    
    r_fresnel = ((wavelength * d1 * d2) / d) ** 0.5
    clearance_required = clearance_factor * r_fresnel
    
    print(f"  Fresnel radius at midpoint: {r_fresnel:.3f}m")
    print(f"  Clearance required: {clearance_required:.3f}m")
    
    # Current wrong logic
    clearance_height_wrong = path_agl_wrong - clearance_required
    print(f"  Current logic: clearance_height = {path_agl_wrong:.1f}m - {clearance_required:.3f}m = {clearance_height_wrong:.1f}m")
    
    # Correct logic
    min_altitude_needed = mid_terrain + clearance_required
    print(f"  Correct logic: min_altitude_needed = {mid_terrain:.1f}m + {clearance_required:.3f}m = {min_altitude_needed:.1f}m")
    
    # Check if path clears terrain
    path_absolute_wrong = mid_terrain + path_agl_wrong
    path_absolute_correct = mid_terrain + path_agl_correct
    
    print(f"\n🔍 OBSTRUCTION CHECK:")
    print(f"  Path absolute (wrong): {path_absolute_wrong:.1f}m")
    print(f"  Path absolute (correct): {path_absolute_correct:.1f}m")
    print(f"  Min altitude needed: {min_altitude_needed:.1f}m")
    
    obstructed_wrong = path_absolute_wrong < min_altitude_needed
    obstructed_correct = path_absolute_correct < min_altitude_needed
    
    print(f"  Current logic says: {'❌ OBSTRUCTED' if obstructed_wrong else '✅ CLEAR'}")
    print(f"  Correct logic says: {'❌ OBSTRUCTED' if obstructed_correct else '✅ CLEAR'}")
    
    print(f"\n💡 ROOT CAUSE:")
    print("=" * 40)
    print("The current code interpolates between AGL heights, but should interpolate")
    print("between absolute altitudes. This causes the path to be calculated much")
    print("lower than it should be, making Fresnel zone clearance calculations wrong.")
    print("\nCurrent: path_agl = sensor_agl + t × (aircraft_agl - sensor_agl)")
    print("Correct: path_absolute = sensor_absolute + t × (aircraft_absolute - sensor_absolute)")

if __name__ == "__main__":
    analyze_path_altitude_bug() 