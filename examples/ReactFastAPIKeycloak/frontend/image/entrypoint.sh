#!/bin/sh
set -e

ln -sf /deps/node_modules /app/node_modules
ln -sf /deps/package.json /app/package.json

# Config content for frontend (including Keycloak settings)
CONFIG_CONTENT="window.__BITSWAN_CONFIG__ = {
  workspaceName: \"${BITSWAN_WORKSPACE_NAME}\",
  deploymentId: \"${BITSWAN_DEPLOYMENT_ID}\",
  stage: \"${BITSWAN_AUTOMATION_STAGE}\",
  domain: \"${BITSWAN_GITOPS_DOMAIN}\",
  keycloak: {
    url: \"${KEYCLOAK_URL}\",
    realm: \"${KEYCLOAK_REALM}\",
    clientId: \"${KEYCLOAK_CLIENT_ID}\"
  }
};"

# Live dev mode: run Vite dev server with hot reload
if [ "$BITSWAN_AUTOMATION_STAGE" = "live-dev" ]; then
  echo "Starting in live-dev mode with hot reload..."

  # Ensure public directory exists (may not exist if source is mounted directly)
  mkdir -p /app/public

  # Write config to public directory for Vite dev server
  echo "$CONFIG_CONTENT" > /app/public/config.js

  # Create vite config that allows hosts from the domain env var
  cat > /app/vite.config.live-dev.js << EOF
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: ['.${BITSWAN_GITOPS_DOMAIN}'],
  },
})
EOF

  # Run Vite dev server with live-dev config
  exec npm run dev -- --config vite.config.live-dev.js --host 0.0.0.0 --port 8080
fi

# Production mode: build and serve static files
npm run build

# Write config to dist directory for production
echo "$CONFIG_CONTENT" > dist/config.js

exec serve -s dist -l 8080
