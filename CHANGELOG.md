# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI/CD pipeline
- Comprehensive API documentation
- Professional README with badges
- Issue and pull request templates
- Contributing guidelines
- Security policy

### Changed
- Improved terrain loading with multiple path resolution
- Enhanced error handling and logging
- Added startup validation for terrain data
- Updated deployment configuration for Render

### Fixed
- Terrain file loading issues on Render deployment
- Git LFS configuration for large terrain files
- Path resolution for different deployment environments

## [1.0.0] - 2025-01-31

### Added
- Initial release of Sensor Coverage API
- Terrain-based coverage calculation
- AGL (Above Ground Level) height computation
- Fresnel zone analysis
- Progress tracking system
- Performance monitoring
- RESTful API endpoints
- London terrain data (150MB GeoTIFF)
- Coverage range up to 50km
- Height range 0-1000m AGL
- FastAPI backend with automatic documentation
- Render deployment configuration
- Docker support

### Technical Details
- Processing speed: ~0.016 seconds per cell
- Typical response time: 1-5 seconds for 100 cells
- Memory usage: ~150MB terrain data
- Supported Python version: 3.11
- Framework: FastAPI
- Terrain processing: Rasterio, GDAL
- Signal processing: SciPy, NumPy

[Unreleased]: https://github.com/dunnerz/sensor-radar/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/dunnerz/sensor-radar/releases/tag/v1.0.0 