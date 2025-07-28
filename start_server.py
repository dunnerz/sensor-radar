#!/usr/bin/env python3
"""
Start the FastAPI server with progress tracking enabled.
"""

import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Sensor Coverage API with progress tracking...")
    print("📊 API will be available at: http://localhost:8000")
    print("📈 Progress tracking endpoint: http://localhost:8000/progress/{job_id}")
    print("📖 API documentation: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 