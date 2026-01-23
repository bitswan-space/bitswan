#!/bin/sh
set -e

ln -sf /deps/node_modules /app/node_modules
ln -sf /deps/package.json /app/package.json

# Config content for frontend
CONFIG_CONTENT="window.__BITSWAN_CONFIG__ = {
  workspaceName: \"${BITSWAN_WORKSPACE_NAME}\",
  deploymentId: \"${BITSWAN_DEPLOYMENT_ID}\",
  stage: \"${BITSWAN_AUTOMATION_STAGE}\",
  domain: \"${BITSWAN_GITOPS_DOMAIN}\"
};"

# Live dev mode: run Vite dev server with hot reload
if [ "$BITSWAN_AUTOMATION_STAGE" = "live-dev" ]; then
  echo "Starting in live-dev mode with hot reload..."

  # Ensure public directory exists (may not exist if source is mounted directly)
  mkdir -p /app/public

  # Write config to public directory for Vite dev server
  echo "$CONFIG_CONTENT" > /app/public/config.js

  # Run Vite dev server (listens on 0.0.0.0:8080)
  exec npm run dev -- --host 0.0.0.0 --port 8080
fi

# Production mode: build and serve static files
npm run build

# Write config to dist directory for production
echo "$CONFIG_CONTENT" > dist/config.js

exec serve -s dist -l 8080
