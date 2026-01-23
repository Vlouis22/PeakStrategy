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

backend/                  # Flask API backend (not currently running as workflow)
  app/                    # Flask application
    api/                  # API routes
    services/             # Business logic
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
- **Data**: yfinance for stock data

## Recent Changes

- 2026-01-23: Configured for Replit environment
  - Set Vite to run on port 5000 with all hosts allowed
  - Added required Firebase environment variables
  - Updated CORS settings for development
