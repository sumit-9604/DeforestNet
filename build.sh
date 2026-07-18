#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Build the Frontend
echo "Building Frontend React static assets..."
cd frontend
npm install
npm run build
cd ..

# 2. Install Backend Python dependencies
echo "Installing Backend Python dependencies..."
pip install -r backend/requirements.txt
