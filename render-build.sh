#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Installing Python dependencies..."
pip install -r backend/requirements.txt

echo "Building Frontend..."
cd frontend
npm install
npm run build
cd ..

echo "Build complete."
