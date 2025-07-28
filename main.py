
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from coverage_engine import compute_min_agl

app = FastAPI()

class SensorRequest(BaseModel):
    sensor_id: str
    latitude: float
    longitude: float
    height: float  # sensor antenna height above terrain
    config: Dict[str, Any]

@app.post("/")
async def run_coverage(data: SensorRequest):
    try:
        results = compute_min_agl(
            sensor_id=data.sensor_id,
            sensor_position=[data.latitude, data.longitude, data.height],
            config=data.config
        )
        return {"results": results}
    except Exception as e:
        return {"error": str(e)}
