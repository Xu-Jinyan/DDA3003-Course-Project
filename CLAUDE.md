# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PFGW (Pandemic-Flight Global Watcher) is a Flask-based backend service that provides COVID-19 and flight data visualization APIs for a D3.js frontend.

## Commands

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Development Server
```bash
python3 app.py
```
Server runs at http://localhost:5000 with hot reload enabled.

### Run Tests
`test_api.py` is an HTTP integration test — the Flask server must already be running before executing it:
```bash
python3 test_api.py              # tests against http://localhost:5000
python3 test_api.py <base_url>   # tests against a custom URL
```
The script polls for server readiness for up to 30 seconds before running.

## API Architecture

The Flask application (`app.py`) provides RESTful endpoints that all return JSON responses:

- **Health Check**: `GET /api/health` - Basic service health status
- **Date Range**: `GET /api/date-range` - Returns available data date range {start, end, total_days}
- **COVID Data**: `GET /api/covid-data?date=YYYY-MM-DD` - Returns global cases and country-level data for top 50 affected countries
- **Flights**: `GET /api/flights?date=YYYY-MM-DD&max_flights=50` - Returns sampled flight routes with coordinates
- **Airports**: `GET /api/airports` - Returns all airport coordinates extracted from flight data
- **Snapshot**: `GET /api/snapshot?date=YYYY-MM-DD&max_flights=50` - Combined COVID + flights response
- **Global Trend**: `GET /api/global-trend` - All dates' global cumulative/new case totals (cached in memory after first call; used for the trend chart)
- **Country History**: `GET /api/country-history?country=USA` - Full time-series for one country by ISO3 code

Flask also serves the D3.js frontend: `GET /` returns `index.html` from the project root (configured via `static_folder='.'`). All API routes include comprehensive error handling with try/except blocks and return appropriate HTTP status codes (400, 404, 500).

## Data Service Architecture

`data_service.py` implements a singleton `DataService` class that:

1. **Eager Loading**: Loads WHO COVID data and airport coordinates synchronously at `__init__` time — startup will be slow if data files are large
2. **WHO Data Processing**: Reads Excel file, creates country mappings, and provides case data by date with fallback to nearest available date
3. **Flight Data Access**: Reads Parquet files on-demand by month, filters by date, samples results to prevent overwhelming the frontend
4. **Airport Extraction**: Dynamically extracts airport coordinates from flight data sample, falls back to preset airports if data unavailable
5. **Caching Strategy**: Caches date ranges and WHO data in memory; flight data cached at month-granularity by Parquet format

### Key Implementation Details

- **Parquet File Lookup**: Flight data is looked up as `flightlist_YYYYMM01_YYYYMM31.parquet` first, then falls back to any `flightlist_YYYYMM*.parquet` glob match
- **Date Handling**: All dates use ISO 8601 format (YYYY-MM-DD). Date filtering in flights uses timestamp comparison in UTC; falls back to full-file read + pandas filter if PyArrow pushdown filters fail
- **Coordinate Format**: All geographic coordinates return as [longitude, latitude] arrays for D3.js compatibility
- **Sampling Strategy**: Flight data limited to `max_flights` parameter (default 50) using fixed random seed (42) for reproducibility
- **Error Resilience**: WHO data falls back to nearest date; missing flight data returns empty arrays rather than errors
- **Memory Management**: WHO data (~77K records) fully loaded; flight data read in filtered chunks via Parquet

## Data Storage

- **WHO COVID Data**: `data/WHO-COVID-19-global-data.xlsx` (Excel format, ~3.5MB)
- **Flight Data**: `data/clean/flightlist_YYYYMMDD_YYYYMMDD.parquet` (Parquet format, 6.2GB total)
- **Airports**: Dynamically extracted from flight data, not stored separately

Parquet files use monthly partitions with columns: origin, destination, latitude_1, longitude_1, latitude_2, longitude_2, day (timestamp)