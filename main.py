from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import asyncio
import os
from coverage_engine import compute_min_agl_with_progress, compute_min_agl_parallel, get_distance_stats
from terrain import get_cache_stats, validate_terrain_data
from progress_store import set_progress, get_progress, remove_progress, get_active_jobs_count

app = FastAPI(
    title="Sensor Coverage API",
    description="API for computing minimum AGL heights for sensor coverage",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Validate terrain data on startup."""
    print("🚀 Starting Sensor Coverage API...")
    print("🔍 Validating terrain data...")
    
    try:
        # Validate terrain data
        if validate_terrain_data():
            print("✅ Terrain data validation successful")
        else:
            print("⚠️ Terrain data validation failed - some features may not work")
    except Exception as e:
        print(f"❌ Terrain validation error: {str(e)}")
        print("⚠️ API will start but terrain-dependent features may fail")
    
    print("🚀 API startup complete")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CoverageRequest(BaseModel):
    sensor_id: str
    latitude: float
    longitude: float
    height: float
    config: Dict

class CoverageResponse(BaseModel):
    job_id: str
    status: str
    message: str

@app.post("/", response_model=CoverageResponse)
async def run_coverage(data: CoverageRequest, background_tasks: BackgroundTasks):
    """
    Compute minimum AGL (Above Ground Level) heights for sensor coverage.
    
    This endpoint calculates the minimum heights at which aircraft can be detected
    by the specified sensor, taking into account terrain data and signal propagation.
    
    Args:
        data: CoverageRequest containing sensor parameters and configuration
        background_tasks: FastAPI background tasks
        
    Returns:
        Dictionary containing job_id for progress tracking
    """
    try:
        # Generate a unique job ID
        import uuid
        job_id = str(uuid.uuid4())
        
        # Initialize progress tracking
        set_progress(job_id, {
            "status": "starting",
            "progress": 0,
            "total_cells": 0,
            "processed_cells": 0,
            "results": [],
            "error": None
        })
        
        # Start the computation in background with parallel processing
        background_tasks.add_task(
            compute_coverage_with_progress_parallel,
            job_id,
            data.sensor_id,
            data.latitude,
            data.longitude,
            data.height,
            data.config
        )
        
        return {
            "job_id": job_id,
            "status": "started",
            "message": "Coverage computation started. Use /progress/{job_id} to track progress."
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def compute_coverage_with_progress_parallel(job_id: str, sensor_id: str, lat: float, lon: float, alt: float, config: Dict):
    """Run coverage computation with parallel processing."""
    try:
        # Use parallel processing for better performance
        results = await compute_min_agl_parallel(job_id, sensor_id, lat, lon, alt, config, max_workers=4)
        
        from progress_store import update_progress
        update_progress(job_id, {
            "status": "completed",
            "progress": 100,
            "results": results,
            "total_points": len(results)
        })
        
    except Exception as e:
        from progress_store import update_progress
        update_progress(job_id, {
            "status": "error",
            "error": str(e)
        })

@app.get("/progress/{job_id}")
async def get_progress_endpoint(job_id: str):
    """
    Get the progress of a coverage computation job.
    
    Args:
        job_id: The job ID returned by the coverage computation endpoint
        
    Returns:
        Dictionary containing current progress information
    """
    progress_info = get_progress(job_id)
    if not progress_info:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if progress_info["status"] == "completed":
        # Clean up completed jobs after returning results
        result = {
            "job_id": job_id,
            "status": "completed",
            "progress": 100,
            "results": progress_info["results"],
            "total_points": len(progress_info["results"])
        }
        # Remove from store after returning
        remove_progress(job_id)
        return result
    
    elif progress_info["status"] == "error":
        error_msg = progress_info["error"]
        remove_progress(job_id)
        raise HTTPException(status_code=500, detail=f"Computation failed: {error_msg}")
    
    else:
        response = {
            "job_id": job_id,
            "status": progress_info["status"],
            "progress": progress_info["progress"],
            "total_cells": progress_info.get("total_cells", 0),
            "processed_cells": progress_info.get("processed_cells", 0)
        }
        
        # Add detailed progress information if available
        if "stage" in progress_info:
            response["stage"] = progress_info["stage"]
        if "substage" in progress_info:
            response["substage"] = progress_info["substage"]
        if "elapsed_time" in progress_info:
            response["elapsed_time"] = progress_info["elapsed_time"]

        return response

@app.get("/performance/stats")
async def get_performance_stats():
    """
    Get performance statistics for the system.
    
    Returns:
        Dictionary containing performance metrics
    """
    try:
        # Get terrain cache statistics
        terrain_stats = get_cache_stats()
        
        # Get distance cache statistics
        distance_stats = get_distance_stats()
        
        return {
            "terrain_cache": {
                "size": terrain_stats["size"],
                "memory_usage_mb": terrain_stats["memory_usage_mb"],
                "loaded": terrain_stats["loaded"],
                "bounds": terrain_stats["bounds"]
            },
            "distance_cache": {
                "hits": distance_stats["hits"],
                "misses": distance_stats["misses"],
                "hit_rate": distance_stats["hit_rate"],
                "cache_size": distance_stats["cache_size"]
            },
            "active_jobs": get_active_jobs_count()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting performance stats: {str(e)}")

@app.get("/performance/clear-cache")
async def clear_cache():
    """
    Clear all caches to free memory.
    
    Returns:
        Dictionary containing cache clearing results
    """
    try:
        from terrain import cleanup_cache_if_needed
        from coverage_engine import _distance_cache
        
        # Clear terrain cache
        cleanup_cache_if_needed()
        
        # Clear distance cache
        _distance_cache.clear()
        
        return {
            "message": "All caches cleared successfully",
            "terrain_cache_cleared": True,
            "distance_cache_cleared": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Sensor Coverage API",
        "version": "1.0.0",
        "endpoints": {
            "POST /": "Start coverage computation",
            "GET /progress/{job_id}": "Get computation progress",
            "GET /performance/stats": "Get performance statistics",
            "GET /performance/clear-cache": "Clear all caches",
            "GET /docs": "API documentation"
        }
    }

@app.head("/")
async def health_check():
    """Health check endpoint for Render."""
    return {"status": "healthy"}

@app.get("/debug/terrain")
async def debug_terrain():
    """Debug endpoint to check terrain data status."""
    try:
        from terrain import validate_terrain_data, get_cache_stats
        import os
        
        # Check if terrain file exists
        terrain_file = "london-terrain-test.tif"
        file_exists = os.path.exists(terrain_file)
        file_size = os.path.getsize(terrain_file) if file_exists else 0
        
        # Validate terrain data
        terrain_valid = validate_terrain_data()
        
        # Get cache stats
        cache_stats = get_cache_stats()
        
        return {
            "terrain_file": {
                "exists": file_exists,
                "size_bytes": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2) if file_exists else 0
            },
            "terrain_validation": terrain_valid,
            "cache_stats": cache_stats,
            "working_directory": os.getcwd(),
            "files_in_directory": [f for f in os.listdir(".") if f.endswith(".tif")]
        }
    except Exception as e:
        return {
            "error": str(e),
            "working_directory": os.getcwd(),
            "files_in_directory": [f for f in os.listdir(".") if f.endswith(".tif")]
        }

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get port from environment variable (for Render)
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(app, host="0.0.0.0", port=port) 