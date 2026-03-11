#!/bin/sh
set -e

# Live dev mode: run with auto-reload
if [ "$BITSWAN_AUTOMATION_STAGE" = "live-dev" ]; then
  echo "Starting in live-dev mode with auto-reload..."
  exec uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload --reload-dir /app
fi

# Production mode: run without reload
exec uvicorn app.main:app --host 0.0.0.0 --port 8080
