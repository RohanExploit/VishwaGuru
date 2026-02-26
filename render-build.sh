#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Installing Python dependencies..."
if [ -f "backend/requirements-render.txt" ]; then
    echo "Using requirements-render.txt for lightweight deployment..."
    pip install --no-cache-dir -r backend/requirements-render.txt
else
    pip install --no-cache-dir -r backend/requirements.txt
fi

echo "Building Frontend..."
cd frontend
npm install
npm run build
cd ..

echo "Build complete."
