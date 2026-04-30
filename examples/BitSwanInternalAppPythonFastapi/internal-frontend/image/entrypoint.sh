#!/bin/sh
set -e
export VITE_BITSWAN_WORKSPACE_NAME="${BITSWAN_WORKSPACE_NAME}"
export VITE_BITSWAN_DEPLOYMENT_ID="${BITSWAN_DEPLOYMENT_ID}"
export VITE_BITSWAN_AUTOMATION_STAGE="${BITSWAN_AUTOMATION_STAGE}"
export VITE_BITSWAN_GITOPS_DOMAIN="${BITSWAN_GITOPS_DOMAIN}"
export VITE_BITSWAN_URL_TEMPLATE="${BITSWAN_URL_TEMPLATE}"

cp /app/vite.config.mjs /deps/vite.config.mjs

cd /app

if [ "$BITSWAN_AUTOMATION_STAGE" = "live-dev" ]; then
  echo "Starting in live-dev mode with hot reload..."
  exec npx vite --config /deps/vite.config.mjs --host 0.0.0.0 --port 8080
fi

# Production: build into /tmp/dist (writable) and serve.
echo "Building production bundle..."
npx vite build --config /deps/vite.config.mjs --outDir /tmp/dist --emptyOutDir
exec serve -s /tmp/dist -l 8080
