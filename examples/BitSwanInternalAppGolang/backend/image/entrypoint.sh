#!/bin/sh
set -e

cd /app

# Copy module files and download dependencies (source is mounted at /app at runtime)
cp /deps/go.mod /deps/go.sum .
echo "Downloading Go dependencies..."
go mod download

# Live dev mode: watch for file changes and auto-rebuild using Air
if [ "$BITSWAN_AUTOMATION_STAGE" = "live-dev" ]; then
  echo "Starting in live-dev mode with auto-rebuild (Air)..."
  exec air -c /etc/air.toml
fi

# Production mode: build once and run
echo "Building Go server..."
CGO_ENABLED=0 go build -o /tmp/server .
echo "Starting server..."
exec /tmp/server
