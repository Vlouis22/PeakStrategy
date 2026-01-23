# PeakStrategy

A React-based investment strategy and portfolio management application with Firebase authentication.

## Overview

PeakStrategy is a frontend application built with React and Vite that provides:
- Dashboard for portfolio overview
- Research tools
- Portfolio Builder
- Chat functionality
- Firebase-based authentication (Sign Up/Sign In)

## Project Structure

```
peakstrategy-frontend/    # React/Vite frontend application
  src/
    firebase.js           # Firebase configuration
  vite.config.js          # Vite configuration (port 5000, all hosts allowed)
  package.json            # Frontend dependencies

backend/                  # Flask API backend
  app/                    # Flask application
    api/v1/               # API routes
      portfolios.py       # Portfolio endpoints
      monitoring.py       # Health check, metrics, status endpoints
    services/             # Business logic
      stock_price_service.py  # Stock price fetching with Yahoo Finance
      redis_service.py        # Upstash Redis caching with fallbacks
      api_metrics_service.py  # Centralized API metrics tracking
      logging_service.py      # Structured logging with request tracing
      cache_warming_service.py # Background cache warming for popular symbols
    config.py             # Configuration
  run.py                  # Backend entry point
  requirements.txt        # Python dependencies
```

## Environment Variables

### Frontend (Vite)
- `VITE_FIREBASE_API_KEY` - Firebase Web API Key
- `VITE_FIREBASE_APP_ID` - Firebase App ID
- `VITE_FIREBASE_MESSAGING_SENDER_ID` - Firebase Messaging Sender ID
- `VITE_FIREBASE_AUTH_DOMAIN` - Firebase Auth Domain
- `VITE_FIREBASE_PROJECT_ID` - Firebase Project ID
- `VITE_FIREBASE_STORAGE_BUCKET` - Firebase Storage Bucket

### Backend (Flask)
- `FLASK_SECRET_KEY` - Flask secret key
- `FLASK_ENV` - Environment (development/production)
- `FIREBASE_SERVICE_ACCOUNT_PATH` - Path to Firebase service account JSON
- `UPSTASH_REDIS_REST_URL` - Upstash Redis REST URL for caching
- `UPSTASH_REDIS_REST_TOKEN` - Upstash Redis REST token

## Running the Application

### Frontend
The frontend runs on port 5000 via the "Frontend" workflow:
```bash
cd peakstrategy-frontend && npm run dev
```

### Backend (Optional)
To run the backend API on port 5001:
```bash
cd backend && python run.py
```

## Tech Stack

- **Frontend**: React 19, Vite 7, TailwindCSS 4, React Router, Recharts
- **Authentication**: Firebase Auth
- **Backend**: Flask, Flask-CORS, Firebase Admin SDK
- **Data**: Yahoo Finance for stock data
- **Caching**: Upstash Redis (cloud) with in-memory fallback

## Backend Architecture

### Caching Strategy
- Two-tier caching architecture:
  - L1: Local in-memory cache (60s TTL) - instant access, no network latency
  - L2: Upstash Redis (cloud, 15min TTL) - shared persistent cache
- True batch operations: MGET for reads, pipeline for writes (single network round-trip)
- Stale-while-revalidate pattern: returns cached data instantly while refreshing in background
- Request deduplication prevents concurrent API calls for same symbols
- Cache warming service pre-warms frequently accessed symbols

### Stock Price Provider
- Yahoo Finance (yfinance) with User-Agent rotation and retry logic

### Monitoring Endpoints
- `GET /api/v1/monitoring/health` - Health check
- `GET /api/v1/monitoring/metrics` - API usage metrics
- `GET /api/v1/monitoring/status` - Full system status
- `POST /api/v1/monitoring/warm-cache` - Trigger cache warming

## Recent Changes

- 2026-01-23: Yahoo Finance reliability improvements
  - Added User-Agent rotation with 17 realistic browser agents (Chrome, Firefox, Safari, Edge)
  - Implemented retry with exponential backoff (up to 3 attempts) for all yfinance requests
  - Added optional proxy support via PROXY_URL environment variable
  - Each request uses a fresh session with rotated headers to avoid blocking

- 2026-01-23: Caching efficiency improvements
  - Implemented two-tier cache (L1 local + L2 Redis) for reduced latency
  - Added true batch operations with MGET and pipeline for network efficiency
  - Added stale-while-revalidate pattern for instant responses with background refresh
  - Added cache stats monitoring endpoint: `GET /api/v1/monitoring/cache/stats`

- 2026-01-23: Backend scalability refactoring
  - Implemented request deduplication for stock price API calls
  - Added Upstash Redis integration for production caching
  - Implemented structured logging with request tracing
  - Added API metrics service for tracking usage
  - Added cache warming service for popular symbols
  - Created monitoring endpoints for health checks and metrics

- 2026-01-23: Configured for Replit environment
  - Set Vite to run on port 5000 with all hosts allowed
  - Added required Firebase environment variables
  - Updated CORS settings for development
