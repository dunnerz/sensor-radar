#!/usr/bin/env python3
"""
Test script to verify terrain loading works correctly.
Run this before deployment to ensure terrain data is accessible.
"""

import os
import sys

def test_terrain_loading():
    """Test terrain loading functionality."""
    print("🧪 Testing terrain loading...")
    
    try:
        # Test 1: Check if file exists
        terrain_file = "london-terrain-test.tif"
        print(f"🔍 Checking if terrain file exists: {terrain_file}")
        
        if os.path.exists(terrain_file):
            file_size = os.path.getsize(terrain_file)
            print(f"✅ File exists, size: {file_size / (1024*1024):.1f} MB")
        else:
            print(f"❌ File not found: {terrain_file}")
            return False
        
        # Test 2: Try to import and load terrain
        print("🔍 Testing rasterio import...")
        import rasterio
        print("✅ rasterio imported successfully")
        
        # Test 3: Try to open the terrain file
        print("🔍 Testing terrain file opening...")
        raster = rasterio.open(terrain_file)
        print(f"✅ Terrain file opened successfully")
        print(f"   Bounds: {raster.bounds}")
        print(f"   CRS: {raster.crs}")
        print(f"   Shape: {raster.shape}")
        print(f"   Data type: {raster.dtypes[0]}")
        raster.close()
        
        # Test 4: Test terrain module functions
        print("🔍 Testing terrain module...")
        from terrain import validate_terrain_data, get_cache_stats
        
        # Test validation
        terrain_valid = validate_terrain_data()
        print(f"✅ Terrain validation: {terrain_valid}")
        
        # Test cache stats
        cache_stats = get_cache_stats()
        print(f"✅ Cache stats: {cache_stats}")
        
        print("🎉 All terrain tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Terrain test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_terrain_loading()
    sys.exit(0 if success else 1) 