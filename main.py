
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, validator
from coverage_engine import compute_min_agl

app = FastAPI(
    title="Sensor Coverage API",
    description="API for computing 3D coverage data for RF receiver antennas based on real terrain data",
    version="1.0.0"
)

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
async def run_coverage(data: CoverageRequest):
    """
    Compute minimum AGL (Above Ground Level) heights for sensor coverage.
    
    This endpoint calculates the minimum heights at which aircraft can be detected
    by the specified sensor, taking into account terrain data and signal propagation.
    
    Args:
        data: CoverageRequest containing sensor parameters and configuration
        
    Returns:
        Dictionary containing coverage results with sensor_id, coverage_points, and total_points
    """
    try:
        results = compute_min_agl(
            data.sensor_id,
            data.latitude,
            data.longitude,
            data.height,
            data.config
        )
        return {
            "sensor_id": data.sensor_id,
            "coverage_points": results,
            "total_points": len(results)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
