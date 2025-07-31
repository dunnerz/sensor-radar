#!/usr/bin/env python3
"""
Terrain data downloader for Render deployment.
Downloads terrain data if not available locally.
"""

import os
import requests
from pathlib import Path

def download_terrain_data():
    """Download terrain data if not available locally."""
    terrain_file = "london-terrain-test.tif"
    
    if os.path.exists(terrain_file):
        print(f"✅ Terrain file already exists: {terrain_file}")
        return True
    
    print(f"📥 Downloading terrain data: {terrain_file}")
    
    # You would need to host this file somewhere accessible
    # For now, we'll create a placeholder
    terrain_url = "https://your-terrain-host.com/london-terrain-test.tif"
    
    try:
        response = requests.get(terrain_url, stream=True)
        response.raise_for_status()
        
        with open(terrain_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Terrain data downloaded successfully: {terrain_file}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to download terrain data: {e}")
        print("⚠️  You need to provide terrain data manually")
        return False

if __name__ == "__main__":
    download_terrain_data() 