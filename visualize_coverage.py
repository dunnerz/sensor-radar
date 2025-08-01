#!/usr/bin/env python3
"""
Visualization script for coverage data showing AGL variation around sensor.
"""

import requests
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Circle
import json
from datetime import datetime
from scipy import stats

def fetch_and_visualize_coverage():
    """Fetch coverage data and create visualization."""
    
    print("🎨 Creating Coverage Visualization")
    print("=" * 50)
    
    # Test configuration (same as before)
    test_config = {
        "sensor_id": "uk-test-sensor",
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
    max_range = test_config['config']['maxRange']
    
    print(f"📍 Sensor location: {sensor_lat}, {sensor_lon}")
    print(f"📡 Range: {max_range}km")
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
    start_time = datetime.now()
    
    while True:
        try:
            progress_response = requests.get(f"http://localhost:8000/progress/{job_id}")
            if progress_response.status_code == 200:
                progress_data = progress_response.json()
                
                if progress_data.get("status") == "completed":
                    results = progress_data.get("results", [])
                    print(f"✅ Job completed! Processing {len(results)} cells...")
                    break
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return None
            
        import time
        time.sleep(1)
    
    # Process results for visualization
    print("🎨 Creating visualization...")
    
    # Extract coordinates and AGL values
    lats = []
    lons = []
    agl_values = []
    
    for result in results:
        lat = result.get('latitude', 0)
        lon = result.get('longitude', 0)
        agl = result.get('agl', 0)
        
        if lat != 0 and lon != 0:  # Skip invalid coordinates
            lats.append(lat)
            lons.append(lon)
            agl_values.append(agl)
    
    if not lats:
        print("❌ No valid data points found")
        return None
    
    # Create visualization
    create_coverage_heatmap(lats, lons, agl_values, sensor_lat, sensor_lon, max_range)
    create_distance_trend_analysis(lats, lons, agl_values, sensor_lat, sensor_lon, max_range)
    
    return results

def create_distance_trend_analysis(lats, lons, agl_values, sensor_lat, sensor_lon, max_range):
    """Create a detailed trend analysis of AGL vs distance from sensor."""
    
    # Convert to numpy arrays
    lats = np.array(lats)
    lons = np.array(lons)
    agl_values = np.array(agl_values)
    
    # Calculate distances from sensor using geodesic distance
    from geopy.distance import geodesic
    distances = []
    for lat, lon in zip(lats, lons):
        distance = geodesic((sensor_lat, sensor_lon), (lat, lon)).km
        distances.append(distance)
    
    distances = np.array(distances)
    
    # Create figure with multiple subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # Plot 1: Scatter plot with trend line
    scatter = ax1.scatter(distances, agl_values, c=agl_values, cmap='viridis', alpha=0.6, s=30)
    
    # Add trend line
    z = np.polyfit(distances, agl_values, 1)
    p = np.poly1d(z)
    ax1.plot(distances, p(distances), "r--", alpha=0.8, linewidth=2, label=f'Trend: y={z[0]:.1f}x+{z[1]:.1f}')
    
    ax1.set_xlabel('Distance from Sensor (km)')
    ax1.set_ylabel('AGL (meters)')
    ax1.set_title('AGL vs Distance with Trend Line')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax1)
    cbar.set_label('AGL (meters)', rotation=270, labelpad=20)
    
    # Plot 2: Moving average trend
    # Sort by distance for moving average
    sorted_indices = np.argsort(distances)
    sorted_distances = distances[sorted_indices]
    sorted_agl = agl_values[sorted_indices]
    
    # Calculate moving average
    window_size = max(1, len(sorted_distances) // 20)  # 5% of data points
    moving_avg = np.convolve(sorted_agl, np.ones(window_size)/window_size, mode='valid')
    moving_avg_distances = sorted_distances[window_size-1:]
    
    ax2.plot(sorted_distances, sorted_agl, 'o', alpha=0.4, markersize=4, label='Individual cells')
    ax2.plot(moving_avg_distances, moving_avg, 'r-', linewidth=3, label=f'Moving average (window={window_size})')
    ax2.set_xlabel('Distance from Sensor (km)')
    ax2.set_ylabel('AGL (meters)')
    ax2.set_title('AGL vs Distance with Moving Average')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Distance bins analysis
    # Create distance bins
    num_bins = 10
    bin_edges = np.linspace(0, max_range, num_bins + 1)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    bin_means = []
    bin_stds = []
    bin_counts = []
    
    for i in range(len(bin_edges) - 1):
        mask = (distances >= bin_edges[i]) & (distances < bin_edges[i + 1])
        if np.any(mask):
            bin_agl = agl_values[mask]
            bin_means.append(np.mean(bin_agl))
            bin_stds.append(np.std(bin_agl))
            bin_counts.append(len(bin_agl))
        else:
            bin_means.append(0)
            bin_stds.append(0)
            bin_counts.append(0)
    
    ax3.bar(bin_centers, bin_means, width=bin_edges[1]-bin_edges[0], alpha=0.7, 
            yerr=bin_stds, capsize=5, label='Mean AGL per distance bin')
    ax3.set_xlabel('Distance from Sensor (km)')
    ax3.set_ylabel('Mean AGL (meters)')
    ax3.set_title('Mean AGL by Distance Bins')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Add count annotations
    for i, (center, mean, count) in enumerate(zip(bin_centers, bin_means, bin_counts)):
        if count > 0:
            ax3.text(center, mean + bin_stds[i] + 5, f'n={count}', 
                    ha='center', va='bottom', fontsize=8)
    
    # Plot 4: Statistical summary
    # Calculate correlation
    correlation, p_value = stats.pearsonr(distances, agl_values)
    
    # Calculate statistics by distance ranges
    close_mask = distances <= max_range / 3
    mid_mask = (distances > max_range / 3) & (distances <= 2 * max_range / 3)
    far_mask = distances > 2 * max_range / 3
    
    stats_text = f"""
Statistical Analysis:
• Correlation: {correlation:.3f} (p={p_value:.3f})
• Total cells: {len(agl_values)}

Distance Ranges:
• Close (0-{max_range/3:.1f}km): {np.sum(close_mask)} cells
  - Mean AGL: {np.mean(agl_values[close_mask]):.1f}m
  - Std AGL: {np.std(agl_values[close_mask]):.1f}m

• Mid ({max_range/3:.1f}-{2*max_range/3:.1f}km): {np.sum(mid_mask)} cells
  - Mean AGL: {np.mean(agl_values[mid_mask]):.1f}m
  - Std AGL: {np.std(agl_values[mid_mask]):.1f}m

• Far ({2*max_range/3:.1f}-{max_range:.1f}km): {np.sum(far_mask)} cells
  - Mean AGL: {np.mean(agl_values[far_mask]):.1f}m
  - Std AGL: {np.std(agl_values[far_mask]):.1f}m
    """
    
    ax4.text(0.05, 0.95, stats_text, transform=ax4.transAxes, 
             verticalalignment='top', fontsize=10,
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    ax4.set_xlim(0, 1)
    ax4.set_ylim(0, 1)
    ax4.axis('off')
    ax4.set_title('Statistical Summary')
    
    plt.tight_layout()
    
    # Save plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"distance_trend_analysis_{timestamp}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"📊 Distance trend analysis saved as: {filename}")
    
    # Show plot
    plt.show()
    
    # Print detailed statistics
    print("\n📈 DISTANCE TREND ANALYSIS:")
    print(f"   • Correlation coefficient: {correlation:.3f}")
    print(f"   • P-value: {p_value:.3f}")
    print(f"   • Trend slope: {z[0]:.1f} m/km")
    print(f"   • Trend intercept: {z[1]:.1f} m")
    
    if correlation > 0.7:
        print("   • Strong positive correlation: AGL increases with distance")
    elif correlation > 0.3:
        print("   • Moderate positive correlation: AGL tends to increase with distance")
    elif correlation > -0.3:
        print("   • Weak correlation: No clear trend")
    elif correlation > -0.7:
        print("   • Moderate negative correlation: AGL tends to decrease with distance")
    else:
        print("   • Strong negative correlation: AGL decreases with distance")

def create_coverage_heatmap(lats, lons, agl_values, sensor_lat, sensor_lon, max_range):
    """Create a heatmap visualization of AGL coverage."""
    
    # Convert to numpy arrays
    lats = np.array(lats)
    lons = np.array(lons)
    agl_values = np.array(agl_values)
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Plot 1: Scatter plot with AGL values
    scatter = ax1.scatter(lons, lats, c=agl_values, cmap='viridis', s=50, alpha=0.7)
    
    # Add sensor location
    ax1.scatter(sensor_lon, sensor_lat, color='red', s=200, marker='*', label='Sensor', zorder=5)
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax1)
    cbar.set_label('AGL (meters)', rotation=270, labelpad=20)
    
    # Customize plot
    ax1.set_xlabel('Longitude')
    ax1.set_ylabel('Latitude')
    ax1.set_title(f'AGL Coverage Heatmap\nRange: {max_range}km')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Distance-based visualization
    # Calculate distances from sensor
    distances = []
    for lat, lon in zip(lats, lons):
        # Simple distance calculation (approximate)
        lat_diff = lat - sensor_lat
        lon_diff = lon - sensor_lon
        distance = np.sqrt(lat_diff**2 + lon_diff**2) * 111  # Rough km conversion
        distances.append(distance)
    
    distances = np.array(distances)
    
    # Create distance vs AGL plot
    ax2.scatter(distances, agl_values, c=agl_values, cmap='viridis', alpha=0.6, s=30)
    ax2.set_xlabel('Distance from Sensor (km)')
    ax2.set_ylabel('AGL (meters)')
    ax2.set_title('AGL vs Distance from Sensor')
    ax2.grid(True, alpha=0.3)
    
    # Add statistics
    stats_text = f"""
Statistics:
• Min AGL: {np.min(agl_values):.1f}m
• Max AGL: {np.max(agl_values):.1f}m
• Mean AGL: {np.mean(agl_values):.1f}m
• Total cells: {len(agl_values)}
• Coverage radius: {max_range}km
    """
    
    ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes, 
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Add range circle
    circle = Circle((sensor_lon, sensor_lat), max_range/111, fill=False, 
                   color='red', linestyle='--', linewidth=2, label=f'{max_range}km Range')
    ax1.add_patch(circle)
    
    plt.tight_layout()
    
    # Save plot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"coverage_visualization_{timestamp}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"📊 Visualization saved as: {filename}")
    
    # Show plot
    plt.show()
    
    # Print summary statistics
    print("\n📈 COVERAGE STATISTICS:")
    print(f"   • Total cells: {len(agl_values)}")
    print(f"   • Minimum AGL: {np.min(agl_values):.1f}m")
    print(f"   • Maximum AGL: {np.max(agl_values):.1f}m")
    print(f"   • Mean AGL: {np.mean(agl_values):.1f}m")
    print(f"   • Standard deviation: {np.std(agl_values):.1f}m")
    
    # Distance-based analysis
    print(f"\n📏 DISTANCE ANALYSIS:")
    print(f"   • Average distance: {np.mean(distances):.1f}km")
    print(f"   • Max distance: {np.max(distances):.1f}km")
    print(f"   • Cells within 10km: {np.sum(distances <= 10)}")
    print(f"   • Cells within 15km: {np.sum(distances <= 15)}")
    print(f"   • Cells at max range: {np.sum(distances >= max_range*0.9)}")

if __name__ == "__main__":
    fetch_and_visualize_coverage() 