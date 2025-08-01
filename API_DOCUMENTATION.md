# Sensor Coverage API Documentation

## Overview

The Sensor Coverage API computes 3D coverage data for RF receiver antennas based on real terrain data. It calculates the minimum AGL (Above Ground Level) heights at which aircraft can be detected by sensors, taking into account terrain elevation and signal propagation.

**Base URL**: `https://sensor-radar.onrender.com`

## Quick Start

### 1. Submit a Coverage Job

```bash
curl -X POST https://sensor-radar.onrender.com/ \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "my-sensor-1",
    "latitude": 51.5074,
    "longitude": -0.1278,
    "height": 5.0,
    "config": {
      "maxRange": 5.0,
      "minHeight": 0,
      "maxHeight": 200,
      "heightRes": 10,
      "txFrequency": 2400,
      "txPower": 30,
      "txGain": 0,
      "rxGain": 0,
      "rxSensitivity": -90,
      "gridResolution": 0.5,
      "fresnelSamplingDensity": 500,
      "maxCells": 100
    }
  }'
```

**Response**:
```json
{
  "job_id": "f23ed16a-5a37-42de-9e71-0af8dedc0a10",
  "status": "started",
  "message": "Coverage computation started. Use /progress/{job_id} to track progress."
}
```

### 2. Monitor Progress

```bash
curl https://sensor-radar.onrender.com/progress/f23ed16a-5a37-42de-9e71-0af8dedc0a10
```

**Response**:
```json
{
  "job_id": "f23ed16a-5a37-42de-9e71-0af8dedc0a10",
  "status": "completed",
  "progress": 100,
  "results": [
    {
      "latitude": 51.462484,
      "longitude": -0.127800,
      "agl": 80,
      "signal_strength": null,
      "terrain_asl": 18.5
    }
  ],
  "total_points": 100
}
```

## API Endpoints

### POST / - Submit Coverage Job

Starts a new coverage computation job.

**Request Body**:
```json
{
  "sensor_id": "string",
  "latitude": "float",
  "longitude": "float", 
  "height": "float",
  "config": {
    "maxRange": "float",
    "minHeight": "float",
    "maxHeight": "float",
    "heightRes": "float",
    "txFrequency": "float",
    "txPower": "float",
    "txGain": "float",
    "rxGain": "float",
    "rxSensitivity": "float",
    "gridResolution": "float",
    "fresnelSamplingDensity": "integer",
    "maxCells": "integer"
  }
}
```

**Response**:
```json
{
  "job_id": "string",
  "status": "string",
  "message": "string"
}
```

### GET /progress/{job_id} - Get Job Progress

Retrieves the current status and results of a coverage job.

**Path Parameters**:
- `job_id` (string): The job ID returned from the POST request

**Response**:
```json
{
  "job_id": "string",
  "status": "string",
  "progress": "integer",
  "stage": "string",
  "substage": "string",
  "results": [
    {
      "latitude": "float",
      "longitude": "float",
      "agl": "float",
      "signal_strength": "float|null",
      "terrain_asl": "float"
    }
  ],
  "total_points": "integer"
}
```

### GET / - API Information

Returns basic API information and available endpoints.

**Response**:
```json
{
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
```

### GET /debug/terrain - Terrain Debug Information

Returns terrain data status and validation information.

**Response**:
```json
{
  "terrain_file": {
    "exists": "boolean",
    "size_bytes": "integer",
    "size_mb": "float"
  },
  "terrain_validation": "boolean",
  "cache_stats": {
    "size": "integer",
    "memory_usage_mb": "float",
    "bounds": "object|null",
    "loaded": "boolean"
  },
  "working_directory": "string",
  "files_in_directory": ["string"]
}
```

### GET /performance/stats - Performance Statistics

Returns system performance and cache statistics.

**Response**:
```json
{
  "terrain_cache": {
    "size": "integer",
    "memory_usage_mb": "float",
    "loaded": "boolean",
    "bounds": "object|null"
  },
  "distance_cache": {
    "hits": "integer",
    "misses": "integer",
    "hit_rate": "float",
    "cache_size": "integer"
  },
  "active_jobs": "integer"
}
```

### GET /performance/clear-cache - Clear Cache

Clears all system caches to free memory.

**Response**:
```json
{
  "message": "All caches cleared successfully",
  "terrain_cache_cleared": "boolean",
  "distance_cache_cleared": "boolean"
}
```

## Request Parameters

### Main Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `sensor_id` | string | Unique identifier for the sensor | "sensor-001" |
| `latitude` | float | Sensor latitude (WGS84) | 51.5074 |
| `longitude` | float | Sensor longitude (WGS84) | -0.1278 |
| `height` | float | Sensor height above ground (meters) | 5.0 |

### Configuration Parameters

| Parameter | Type | Description | Default | Range |
|-----------|------|-------------|---------|-------|
| `config.maxRange` | float | Maximum coverage range (kilometers) | 5.0 | 0.1 - 50 |
| `config.minHeight` | float | Minimum aircraft height to test (meters) | 0 | 0 - 1000 |
| `config.maxHeight` | float | Maximum aircraft height to test (meters) | 200 | 10 - 1000 |
| `config.heightRes` | float | Height resolution for testing (meters) | 10 | 1 - 50 |
| `config.txFrequency` | float | Transmit frequency (MHz) | 2400 | 100 - 10000 |
| `config.txPower` | float | Transmit power (dBm) | 30 | -50 - 50 |
| `config.txGain` | float | Transmit antenna gain (dB) | 0 | -50 - 50 |
| `config.rxGain` | float | Receive antenna gain (dB) | 0 | -50 - 50 |
| `config.rxSensitivity` | float | Receiver sensitivity (dBm) | -90 | -150 - -50 |
| `config.gridResolution` | float | Grid resolution (kilometers) | 0.5 | 0.1 - 5 |
| `config.fresnelSamplingDensity` | integer | Fresnel zone sampling density | 500 | 100 - 1000 |
| `config.maxCells` | integer | Maximum cells to process | 100 | 10 - 10000 |

## Response Data

### Coverage Result Object

| Field | Type | Description |
|-------|------|-------------|
| `latitude` | float | Cell latitude (WGS84) |
| `longitude` | float | Cell longitude (WGS84) |
| `agl` | float | Minimum AGL height for coverage (meters) |
| `signal_strength` | float|null | Signal strength at cell (currently null) |
| `terrain_asl` | float | Terrain elevation above sea level (meters) |

### Job Status Values

- `"started"` - Job has been submitted and is processing
- `"completed"` - Job has finished successfully
- `"failed"` - Job failed with an error

## Error Handling

### HTTP Status Codes

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Job not found
- `500` - Internal server error

### Error Response Format

```json
{
  "detail": "Error message describing the issue"
}
```

## Common Error Messages

- `"Computation failed: 'minHeight'"` - Missing required parameter
- `"Job not found"` - Invalid job ID
- `"Failed to load terrain data"` - Terrain data unavailable

## Integration Examples

### JavaScript/Node.js

```javascript
const axios = require('axios');

async function submitCoverageJob() {
  try {
    const response = await axios.post('https://sensor-radar.onrender.com/', {
      sensor_id: 'my-sensor',
      latitude: 51.5074,
      longitude: -0.1278,
      height: 5.0,
      config: {
        maxRange: 5.0,
        minHeight: 0,
        maxHeight: 200,
        heightRes: 10,
        txFrequency: 2400,
        txPower: 30,
        txGain: 0,
        rxGain: 0,
        rxSensitivity: -90,
        gridResolution: 0.5,
        fresnelSamplingDensity: 500,
        maxCells: 100
      }
    });
    
    const jobId = response.data.job_id;
    console.log('Job submitted:', jobId);
    
    // Poll for results
    while (true) {
      const progress = await axios.get(`https://sensor-radar.onrender.com/progress/${jobId}`);
      
      if (progress.data.status === 'completed') {
        console.log('Results:', progress.data.results);
        break;
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}
```

### Python

```python
import requests
import time

def submit_coverage_job():
    url = "https://sensor-radar.onrender.com/"
    
    payload = {
        "sensor_id": "my-sensor",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "height": 5.0,
        "config": {
            "maxRange": 5.0,
            "minHeight": 0,
            "maxHeight": 200,
            "heightRes": 10,
            "txFrequency": 2400,
            "txPower": 30,
            "txGain": 0,
            "rxGain": 0,
            "rxSensitivity": -90,
            "gridResolution": 0.5,
            "fresnelSamplingDensity": 500,
            "maxCells": 100
        }
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        job_id = response.json()["job_id"]
        print(f"Job submitted: {job_id}")
        
        # Poll for results
        while True:
            progress_response = requests.get(f"{url}progress/{job_id}")
            progress_data = progress_response.json()
            
            if progress_data["status"] == "completed":
                print("Results:", progress_data["results"])
                break
            
            time.sleep(1)
            
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
```

## Performance Notes

- **Processing Speed**: ~0.016 seconds per cell
- **Typical Response Time**: 1-5 seconds for 100 cells
- **Memory Usage**: ~150MB terrain data loaded
- **Concurrent Jobs**: Limited by server resources
- **Cache**: Terrain data cached for faster subsequent requests

## Rate Limits

- No strict rate limits currently implemented
- Recommended: Maximum 10 concurrent jobs
- Polling interval: 1 second minimum

## Support

For technical support or questions about integration, please refer to the API documentation at:
`https://sensor-radar.onrender.com/docs`

## Version History

- **v1.0.0** - Initial release with terrain-based coverage calculation
- Terrain data: London area (150MB GeoTIFF)
- Coverage range: Up to 50km
- Height range: 0-1000m AGL  
