#!/bin/sh
set -e

ln -s /deps/node_modules /app/node_modules
ln -s /deps/package.json /app/package.json

npm run build

# Generate runtime config with URL components
# Backend deployment ID is derived by replacing 'frontend' with 'backend'
BACKEND_DEPLOYMENT_ID=$(echo "$BITSWAN_DEPLOYMENT_ID" | sed 's/frontend/backend/')
BACKEND_URL="${BITSWAN_URL_PREFIX}${BACKEND_DEPLOYMENT_ID}${BITSWAN_URL_SUFFIX}"

cat > dist/config.js << EOF
window.__BITSWAN_CONFIG__ = {
  backendUrl: "${BACKEND_URL}",
  automationUrl: "${BITSWAN_AUTOMATION_URL}",
  deploymentId: "${BITSWAN_DEPLOYMENT_ID}",
  stage: "${BITSWAN_AUTOMATION_STAGE}",
  urlPrefix: "${BITSWAN_URL_PREFIX}",
  urlSuffix: "${BITSWAN_URL_SUFFIX}"
};
EOF

exec serve -s dist -l 8080
