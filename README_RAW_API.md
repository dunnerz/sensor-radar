# Raw API - Original Sensor Coverage API

This folder contains the original Sensor Coverage API files before any Supabase integration, authentication, or Lovable app modifications.

## 📁 Contents

### Core API Files
- `main.py` - Original FastAPI application (no authentication, no Supabase)
- `coverage_engine.py` - Core coverage calculation engine
- `terrain.py` - Terrain data processing and caching
- `progress_store.py` - Progress tracking system
- `utils.py` - Utility functions
- `start_server.py` - Server startup script

### Export & Visualization
- `geotiff_export.py` - GeoTIFF export functionality

### Testing
- `test_template.py` - Test template for coverage calculations

### Deployment
- `requirements.txt` - Python dependencies (no Supabase)
- `render.yaml` - Render deployment config (no Supabase env vars)
- `Dockerfile` - Docker container configuration
- `docker-compose.yml` - Docker Compose setup
- `deploy.py` - Deployment script
- `DEPLOYMENT.md` - Deployment documentation

### Documentation
- `README.md` - Original project README
- `LICENSE` - Project license

## 🔄 Key Differences from Current API

### No Authentication
- No API key requirements
- No Bearer token authentication
- Open access to all endpoints

### No Supabase Integration
- No database storage
- No user management
- No computation history
- No Row Level Security

### Simple CORS
- Allows all origins (`*`)
- No restricted origins

### Basic Request Format
```json
{
  "sensor_id": "test-sensor",
  "latitude": 51.493,
  "longitude": -0.0669,
  "height": 5.0,
  "config": {
    "maxRange": 10.0,
    "minHeight": 0,
    "maxHeight": 200,
    "heightRes": 10,
    "txFrequency": 1090,
    "txPower": 20,
    "txGain": 0,
    "rxGain": 0,
    "rxSensitivity": -110,
    "gridResolution": 1.0,
    "fresnelSamplingDensity": 500
  }
}
```

## 🚀 Usage

### Local Development
```bash
cd "Raw API"
pip install -r requirements.txt
python start_server.py
```

### Render Deployment
1. Connect this folder to Render
2. Use the provided `render.yaml`
3. No environment variables needed

### API Endpoints
- `POST /` - Start coverage computation
- `GET /progress/{job_id}` - Get progress
- `GET /performance/stats` - Performance stats
- `GET /performance/clear-cache` - Clear cache
- `GET /docs` - API documentation

## 📊 Features

### Core Functionality
- ✅ Terrain-based coverage calculation
- ✅ AGL (Above Ground Level) computation
- ✅ Fresnel zone analysis
- ✅ Progress tracking
- ✅ Performance monitoring
- ✅ GeoTIFF export

### Missing Features (vs Current API)
- ❌ User authentication
- ❌ Database storage
- ❌ Computation history
- ❌ User isolation
- ❌ API key security
- ❌ Supabase integration

## 🔧 Testing

Use the included `test_template.py` to test the API:

```bash
python test_template.py
```

This will run a basic coverage calculation and export results to GeoTIFF.

## 📝 Notes

This is the "clean" version of the API that focuses purely on the core coverage calculation functionality without any external integrations or security features. It's useful for:

- Understanding the core algorithm
- Testing basic functionality
- Development without external dependencies
- Reference implementation
- Deployment to simple environments

The current main API builds upon this foundation by adding Supabase integration, authentication, and Lovable app support. 