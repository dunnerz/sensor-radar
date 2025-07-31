#!/usr/bin/env python3
"""
GeoTIFF export functionality for coverage visualization.
Exports coverage results as GeoTIFF files for visualization.
"""

import numpy as np
from rasterio.transform import from_bounds
from rasterio.warp import reproject, Resampling
import rasterio
from rasterio.crs import CRS
import json
import os
from datetime import datetime

def export_coverage_to_geotiff(results, sensor_lat, sensor_lon, max_range_km, output_path=None):
    """
    Export coverage results to GeoTIFF format.
    
    Args:
        results: List of coverage results with lat, lon, agl
        sensor_lat: Sensor latitude
        sensor_lon: Sensor longitude
        max_range_km: Maximum range in kilometers
        output_path: Output file path (optional)
        
    Returns:
        Path to the generated GeoTIFF file
    """
    if not results:
        print("❌ No results to export")
        return None
    
    # Extract coordinates and AGL values
    lats = [result['latitude'] for result in results]
    lons = [result['longitude'] for result in results]
    agl_values = [result.get('agl', 0) for result in results]
    
    # Calculate bounds
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    
    # Calculate appropriate grid resolution based on cell density
    # Use a higher resolution grid to ensure continuous coverage
    grid_size = max(200, int(np.sqrt(len(results)) * 2))  # Ensure at least 200x200 grid
    
    # Create a regular grid with higher resolution
    lat_step = (max_lat - min_lat) / grid_size
    lon_step = (max_lon - min_lon) / grid_size
    
    # Create coordinate arrays
    lat_coords = np.arange(min_lat, max_lat + lat_step, lat_step)
    lon_coords = np.arange(min_lon, max_lon + lon_step, lon_step)
    
    # Create empty raster
    raster = np.full((len(lat_coords), len(lon_coords)), np.nan, dtype=np.float32)
    
    # Create interpolation grid for smooth coverage
    from scipy.interpolate import griddata
    
    # Extract coordinates and values for interpolation
    points = np.array([[result['longitude'], result['latitude']] for result in results])
    values = np.array([result.get('agl', 0) for result in results])
    
    # Create meshgrid for interpolation
    lon_mesh, lat_mesh = np.meshgrid(lon_coords, lat_coords)
    grid_points = np.column_stack((lon_mesh.ravel(), lat_mesh.ravel()))
    
    # Interpolate values to create smooth raster
    interpolated_values = griddata(points, values, grid_points, method='linear', fill_value=np.nan)
    
    # Reshape back to 2D raster
    raster = interpolated_values.reshape(lat_coords.shape[0], lon_coords.shape[0])
    
    # Generate output filename if not provided
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"coverage_export_{timestamp}.tif"
    
    # Create transform
    transform = from_bounds(min_lon, min_lat, max_lon, max_lat, len(lon_coords), len(lat_coords))
    
    # Write GeoTIFF
    with rasterio.open(
        output_path,
        'w',
        driver='GTiff',
        height=len(lat_coords),
        width=len(lon_coords),
        count=1,
        dtype=raster.dtype,
        crs=CRS.from_epsg(4326),  # WGS84
        transform=transform,
        nodata=np.nan
    ) as dst:
        dst.write(raster, 1)
    
    print(f"✅ Coverage exported to: {output_path}")
    print(f"📊 Raster size: {len(lat_coords)}x{len(lon_coords)}")
    print(f"📈 AGL range: {np.nanmin(raster):.1f}m - {np.nanmax(raster):.1f}m")
    
    return output_path

def create_coverage_metadata(results, sensor_lat, sensor_lon, config):
    """
    Create metadata for coverage visualization.
    
    Args:
        results: Coverage results
        sensor_lat: Sensor latitude
        sensor_lon: Sensor longitude
        config: Configuration used
        
    Returns:
        Dictionary with metadata
    """
    agl_values = [result.get('agl', 0) for result in results]
    
    metadata = {
        "sensor_location": {
            "latitude": sensor_lat,
            "longitude": sensor_lon
        },
        "configuration": config,
        "statistics": {
            "total_cells": len(results),
            "min_agl": min(agl_values) if agl_values else 0,
            "max_agl": max(agl_values) if agl_values else 0,
            "mean_agl": np.mean(agl_values) if agl_values else 0,
            "cells_with_zero_agl": len([agl for agl in agl_values if agl == 0]),
            "cells_with_coverage": len([agl for agl in agl_values if agl > 0])
        },
        "export_timestamp": datetime.now().isoformat()
    }
    
    return metadata

def export_coverage_with_metadata(results, sensor_lat, sensor_lon, config, max_range_km, output_dir="exports"):
    """
    Export coverage results with metadata.
    
    Args:
        results: Coverage results
        sensor_lat: Sensor latitude
        sensor_lon: Sensor longitude
        config: Configuration used
        max_range_km: Maximum range
        output_dir: Output directory
        
    Returns:
        Dictionary with file paths
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Export GeoTIFF
    geotiff_path = os.path.join(output_dir, f"coverage_{timestamp}.tif")
    geotiff_file = export_coverage_to_geotiff(results, sensor_lat, sensor_lon, max_range_km, geotiff_path)
    
    # Export metadata
    metadata = create_coverage_metadata(results, sensor_lat, sensor_lon, config)
    metadata_path = os.path.join(output_dir, f"coverage_{timestamp}_metadata.json")
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Metadata exported to: {metadata_path}")
    
    return {
        "geotiff": geotiff_file,
        "metadata": metadata_path,
        "timestamp": timestamp
    } 