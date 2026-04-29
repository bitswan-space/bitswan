#!/bin/sh
set -e

# BitSwan workspace metadata is exposed to the React app via Vite's
# `import.meta.env.VITE_*` mechanism. Vite picks up env vars whose name
# starts with VITE_ and inlines them into the bundle (production) or
# serves them via `import.meta.env` (dev). The app reads them in src/api.ts.
export VITE_BITSWAN_WORKSPACE_NAME="${BITSWAN_WORKSPACE_NAME}"
export VITE_BITSWAN_DEPLOYMENT_ID="${BITSWAN_DEPLOYMENT_ID}"
export VITE_BITSWAN_AUTOMATION_STAGE="${BITSWAN_AUTOMATION_STAGE}"
export VITE_BITSWAN_GITOPS_DOMAIN="${BITSWAN_GITOPS_DOMAIN}"
export VITE_BITSWAN_URL_TEMPLATE="${BITSWAN_URL_TEMPLATE}"

# Source is bind-mounted at /app. It contains committed symlinks
# `package.json` → `/deps/package.json` and `node_modules` → `/deps/node_modules`
# so Vite finds dependencies in the image's writable layer without anything
# being created at runtime (the source mount is read-only in live-dev).
#
# Vite bundles every config file through esbuild and writes the result
# (`<config>.timestamp-….mjs`) next to the original before evaluating it.
# We copy the config into /deps (writable, and crucially next to
# `node_modules`) so both the temp-file write and the bundled module's
# `import 'vite'` resolution land on writable, populated paths.
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
