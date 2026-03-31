#!/bin/bash

# Exit on error
set -e

# Wait for Postgres to be ready
echo "Waiting for Postgres to be ready..."
until pg_isready -h postgres -p 5432 -U bravola_user; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done

echo "Postgres is up - running migrations"

# Run database migrations
alembic upgrade head

# Start the application
echo "Starting FastAPI application..."
exec uvicorn api.main:app --host 0.0.0.0 --port 8000 ${UVICORN_RELOAD:+--reload}
