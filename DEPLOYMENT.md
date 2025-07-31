# Sensor Coverage API - Deployment Guide

This guide will help you deploy and test the Sensor Coverage API.

## Prerequisites

- Python 3.9 or higher
- Docker and Docker Compose (optional, for containerized deployment)
- The terrain file `london-terrain-test.tif` must be in the project directory

## Quick Start

### Option 1: Automated Deployment (Recommended)

1. **Run the deployment script:**
   ```bash
   python deploy.py
   ```

2. **Follow the prompts:**
   - The script will check prerequisites
   - Choose between Docker or Python deployment
   - Optionally run tests after deployment

### Option 2: Manual Deployment

#### Using Python (Local Development)

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   ```

2. **Activate virtual environment:**
   - Windows: `venv\Scripts\activate`
   - Unix/Mac: `source venv/bin/activate`

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the server:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

#### Using Docker (Production)

1. **Build and start containers:**
   ```bash
   docker-compose up --build -d
   ```

2. **Check container status:**
   ```bash
   docker-compose ps
   ```

3. **View logs:**
   ```bash
   docker-compose logs -f
   ```

## Testing the API

### Quick Test

Run the quick test script to verify basic functionality:

```bash
python quick_test.py
```

### Comprehensive Test

Run the full test suite with multiple scenarios:

```bash
python test_comprehensive_api.py
```

### Manual Testing

1. **Health Check:**
   ```bash
   curl http://localhost:8000/
   ```

2. **Submit a coverage job:**
   ```bash
   curl -X POST http://localhost:8000/ \
     -H "Content-Type: application/json" \
     -d '{
       "sensor_id": "TestRadar",
       "latitude": 51.493,
       "longitude": -0.0669,
       "height": 5,
       "config": {
         "rxSensitivity": -110,
         "txPower": 20,
         "txFrequency": 1090,
         "maxRange": 1.0,
         "minHeight": 0,
         "maxHeight": 100,
         "heightRes": 20
       }
     }'
   ```

3. **Check progress (replace JOB_ID with actual job ID):**
   ```bash
   curl http://localhost:8000/progress/JOB_ID
   ```

4. **Get performance stats:**
   ```bash
   curl http://localhost:8000/performance/stats
   ```

## API Endpoints

- `POST /` - Submit a coverage computation job
- `GET /progress/{job_id}` - Get job progress
- `GET /performance/stats` - Get performance statistics
- `GET /performance/clear-cache` - Clear all caches
- `GET /docs` - Interactive API documentation

## Configuration

### Environment Variables

- `PYTHONUNBUFFERED=1` - Ensures Python output is not buffered (set in docker-compose.yml)

### Performance Tuning

The API includes several performance optimizations:

1. **Terrain Caching:** Elevation data is cached in memory and persisted to disk
2. **Distance Caching:** Haversine calculations are cached for repeated coordinates
3. **Parallel Processing:** Multiple worker processes for computation
4. **Memory Management:** Automatic cache cleanup when memory usage is high

### Monitoring

- **Health Check:** `GET /` returns API status
- **Performance Stats:** `GET /performance/stats` shows cache statistics
- **Container Health:** Docker health checks are configured

## Troubleshooting

### Common Issues

1. **Terrain file not found:**
   - Ensure `london-terrain-test.tif` is in the project directory
   - Check file permissions

2. **Port already in use:**
   - Change the port in `docker-compose.yml` or `start_server.py`
   - Kill existing processes using the port

3. **Memory issues:**
   - The API automatically manages memory usage
   - Use `GET /performance/clear-cache` to manually clear caches

4. **Docker build fails:**
   - Ensure Docker has sufficient memory (at least 4GB recommended)
   - Check internet connection for downloading dependencies

### Logs

- **Docker logs:** `docker-compose logs -f`
- **Application logs:** Check console output when running with Python
- **Error details:** Check the `/progress/{job_id}` endpoint for job-specific errors

## Production Deployment

For production deployment, consider:

1. **Environment Variables:** Set production-specific configurations
2. **Reverse Proxy:** Use nginx or similar for load balancing
3. **Monitoring:** Add application monitoring (Prometheus, Grafana)
4. **Logging:** Configure structured logging
5. **Security:** Add authentication and rate limiting
6. **SSL/TLS:** Configure HTTPS

## Development

### Adding New Features

1. **API Endpoints:** Add new routes in `main.py`
2. **Computation Logic:** Modify `coverage_engine.py`
3. **Terrain Handling:** Update `terrain.py`
4. **Utilities:** Add helper functions in `utils.py`

### Testing

- **Unit Tests:** Add tests for individual functions
- **Integration Tests:** Use the provided test scripts
- **Performance Tests:** Monitor with the performance endpoints

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review the API documentation at `http://localhost:8000/docs`
3. Check the logs for detailed error messages
4. Verify all prerequisites are met 