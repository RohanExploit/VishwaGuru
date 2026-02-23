#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Installing Python dependencies..."
if [ -f "backend/requirements-render.txt" ]; then
    echo "Using requirements-render.txt for lightweight deployment..."
    pip install -r backend/requirements-render.txt
else
    pip install -r backend/requirements.txt
fi

echo "Building Frontend..."
# Optimization: Use --no-audit and --no-fund to save time and memory on Render
cd frontend
npm install --no-audit --no-fund
# Use CI=false to prevent build failure on non-critical lint warnings
CI=false npm run build
cd ..

echo "Build complete."
