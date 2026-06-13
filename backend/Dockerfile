# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.12-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Set the working directory in the container to the root of the app
WORKDIR /app

# Install system dependencies required for OpenCV and other packages
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy backend and data directories
# We assume the build context is the repository root
COPY backend/ backend/
COPY data/ data/

# Install production dependencies.
RUN pip install --no-cache-dir -r backend/requirements.txt

# Service must listen to $PORT environment variable.
ENV PORT 8080

# Add backend directory to PYTHONPATH so imports like 'from database import ...' work
ENV PYTHONPATH=/app/backend

# Run the web service on container startup using gunicorn webserver
# with uvicorn workers.
# We run 'main:app' because /app/backend is in PYTHONPATH.
CMD exec gunicorn --bind :$PORT --workers 1 --worker-class uvicorn.workers.UvicornWorker --threads 8 --timeout 0 main:app
