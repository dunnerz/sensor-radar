from fastapi import FastAPI
from pydantic import BaseModel
from coverage_engine import compute_min_agl

app = FastAPI()

class SensorRequest(BaseModel):
    sensor_id: str
    latitude: float
    longitude: float
    height: float
    config: dict

@app.post("/")
async def run_coverage(data: SensorRequest):
    results = compute_min_agl(
        sensor_id=data.sensor_id,
        sensor_lat=data.latitude,
        sensor_lon=data.longitude,
        sensor_alt=data.height,
        config=data.config
    )
    return {"results": results}
