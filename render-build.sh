#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Installing Python dependencies..."
# Upgrade pip to latest to handle modern wheels
pip install --upgrade pip

if [ -f "backend/requirements-render.txt" ]; then
    echo "Using requirements-render.txt for lightweight deployment..."
    pip install --no-cache-dir -r backend/requirements-render.txt
else
    pip install --no-cache-dir -r backend/requirements.txt
fi

# Frontend build is skipped because this is a backend-only service.
# Frontend should be deployed separately (e.g. Netlify, Vercel).
echo "Skipping Frontend Build (Backend-only deployment)"

echo "Build complete."
