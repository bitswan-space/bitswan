#!/bin/sh
set -e

cd /app

# go.mod / go.sum are baked into the image at /deps; we point go at them
# via -modfile so the runtime never has to write into the (read-only) source.

# Live dev mode: watch for file changes and auto-rebuild using Air.
# Air reads its build command from /etc/air.toml (which uses -modfile=/deps/go.mod
# and writes its build artifacts under /tmp).
if [ "$BITSWAN_AUTOMATION_STAGE" = "live-dev" ]; then
  echo "Starting in live-dev mode with auto-rebuild (Air)..."
  exec air -c /etc/air.toml
fi

# Production mode: build once and run.
echo "Building Go server..."
CGO_ENABLED=0 go build -modfile=/deps/go.mod -o /tmp/server .
echo "Starting server..."
exec /tmp/server
