
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel, validator
from coverage_engine import compute_min_agl
import asyncio
import json
from typing import Dict, Any

app = FastAPI(
    title="Sensor Coverage API",
    description="API for computing 3D coverage data for RF receiver antennas based on real terrain data",
    version="1.0.0"
)

# Global storage for progress tracking
progress_store: Dict[str, Dict[str, Any]] = {}

class CoverageRequest(BaseModel):
    sensor_id: str
    latitude: float
    longitude: float
    height: float
    config: dict
    
    @validator('latitude')
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v
    
    @validator('longitude')
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v
    
    @validator('height')
    def validate_height(cls, v):
        if v < 0:
            raise ValueError('Height must be non-negative')
        return v
    
    @validator('config')
    def validate_config(cls, v):
        required_keys = ['rxSensitivity', 'txPower', 'txFrequency', 'maxRange', 'minHeight', 'maxHeight', 'heightRes']
        missing_keys = [key for key in required_keys if key not in v]
        if missing_keys:
            raise ValueError(f'Missing required config keys: {missing_keys}')
        
        if v['minHeight'] > v['maxHeight']:
            raise ValueError('minHeight cannot be greater than maxHeight')
        
        if v['heightRes'] <= 0:
            raise ValueError('heightRes must be positive')
        
        return v

@app.post("/", response_model=dict)
async def run_coverage(data: CoverageRequest, background_tasks: BackgroundTasks):
    """
    Compute minimum AGL (Above Ground Level) heights for sensor coverage.
    
    This endpoint calculates the minimum heights at which aircraft can be detected
    by the specified sensor, taking into account terrain data and signal propagation.
    
    Args:
        data: CoverageRequest containing sensor parameters and configuration
        
    Returns:
        Dictionary containing job_id for progress tracking
    """
    try:
        # Generate a unique job ID
        import uuid
        job_id = str(uuid.uuid4())
        
        # Initialize progress tracking
        progress_store[job_id] = {
            "status": "starting",
            "progress": 0,
            "total_cells": 0,
            "processed_cells": 0,
            "results": [],
            "error": None
        }
        
        # Start the computation in background
        background_tasks.add_task(
            compute_coverage_with_progress,
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

@app.get("/progress/{job_id}")
async def get_progress(job_id: str):
    """
    Get the progress of a coverage computation job.
    
    Args:
        job_id: The job ID returned by the coverage computation endpoint
        
    Returns:
        Dictionary containing current progress information
    """
    if job_id not in progress_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    progress_info = progress_store[job_id]
    
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
        del progress_store[job_id]
        return result
    
    elif progress_info["status"] == "error":
        error_msg = progress_info["error"]
        del progress_store[job_id]
        raise HTTPException(status_code=500, detail=f"Computation failed: {error_msg}")
    
    else:
        return {
            "job_id": job_id,
            "status": progress_info["status"],
            "progress": progress_info["progress"],
            "total_cells": progress_info["total_cells"],
            "processed_cells": progress_info["processed_cells"]
        }

async def compute_coverage_with_progress(
    job_id: str,
    sensor_id: str,
    lat: float,
    lon: float,
    alt: float,
    config: dict
):
    """
    Compute coverage with progress tracking.
    """
    try:
        progress_store[job_id]["status"] = "computing"
        
        # Import the modified function
        from coverage_engine import compute_min_agl_with_progress
        
        results = await compute_min_agl_with_progress(
            job_id,
            sensor_id,
            lat,
            lon,
            alt,
            config
        )
        
        progress_store[job_id].update({
            "status": "completed",
            "progress": 100,
            "results": results
        })
        
    except Exception as e:
        progress_store[job_id].update({
            "status": "error",
            "error": str(e)
        })
