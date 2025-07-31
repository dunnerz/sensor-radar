from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import asyncio
import os
from coverage_engine import compute_min_agl_with_progress, compute_min_agl_parallel, get_distance_stats
from terrain import get_cache_stats
from progress_store import set_progress, get_progress, remove_progress, get_active_jobs_count

app = FastAPI(
    title="Sensor Coverage API",
    description="API for computing minimum AGL heights for sensor coverage",
    version="1.0.0"
)

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

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get port from environment variable (for Render)
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(app, host="0.0.0.0", port=port) 