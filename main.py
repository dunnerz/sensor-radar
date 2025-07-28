
from fastapi import FastAPI, Request
from pydantic import BaseModel
from coverage_engine import compute_min_agl

app = FastAPI()

class CoverageRequest(BaseModel):
    sensor_id: str
    latitude: float
    longitude: float
    height: float
    config: dict

@app.post("/")
async def run_coverage(data: CoverageRequest):
    try:
        results = compute_min_agl(
            sensor_id=data.sensor_id,
            latitude=data.latitude,
            longitude=data.longitude,
            height=data.height,
            config=data.config
        )
        return results
    except Exception as e:
        return {"error": str(e)}
