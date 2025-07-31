# Sensor Coverage API

[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![API Status](https://img.shields.io/badge/API-Live-green.svg)](https://sensor-radar.onrender.com)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue.svg)](https://github.com/dunnerz/sensor-radar)

A backend Python API for computing 3D coverage data for RF receiver antennas based on real terrain data. The API calculates minimum AGL (Above Ground Level) heights at which aircraft can be detected by sensors, taking into account terrain elevation and signal propagation.

## 🚀 Live API

**Base URL**: `https://sensor-radar.onrender.com`

## 📋 Features

- ✅ **Terrain-based Coverage Calculation** - Uses real terrain data for accurate coverage
- ✅ **AGL Height Computation** - Calculates minimum aircraft heights for detection
- ✅ **Fresnel Zone Analysis** - Advanced signal propagation modeling
- ✅ **Progress Tracking** - Real-time job progress monitoring
- ✅ **Performance Monitoring** - System statistics and cache management
- ✅ **RESTful API** - Simple HTTP endpoints for easy integration

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python)
- **Terrain Processing**: Rasterio, GDAL
- **Signal Processing**: SciPy, NumPy
- **Deployment**: Render
- **Documentation**: OpenAPI/Swagger

## 📖 Documentation

For complete API documentation and integration examples, see:
- **[API Documentation](API_DOCUMENTATION.md)** - Comprehensive integration guide
- **[Raw API Documentation](README_RAW_API.md)** - Technical implementation details

## 🧪 Testing

Run the test script to verify API functionality:

```bash
python test/api_test.py
```

## 🔧 Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python main.py

# Or use the start script
python start_server.py
```

## 📊 API Endpoints

- `POST /` - Submit coverage computation job
- `GET /progress/{job_id}` - Get job progress and results
- `GET /performance/stats` - System performance statistics
- `GET /performance/clear-cache` - Clear system caches
- `GET /debug/terrain` - Terrain data status
- `GET /docs` - Interactive API documentation

## 📈 Performance

- **Processing Speed**: ~0.016 seconds per cell
- **Terrain Data**: 150MB London area GeoTIFF
- **Coverage Range**: Up to 50km
- **Height Range**: 0-1000m AGL
- **Typical Response**: 1-5 seconds for 100 cells

## 🔗 Quick Start

```bash
# Submit a coverage job
curl -X POST https://sensor-radar.onrender.com/ \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "test-sensor",
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
      "rxSensitivity": -90,
      "gridResolution": 0.5,
      "fresnelSamplingDensity": 500,
      "maxCells": 100
    }
  }'
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
