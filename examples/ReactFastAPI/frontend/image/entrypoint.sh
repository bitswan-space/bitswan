#!/bin/sh
set -e

ln -s /deps/node_modules /app/node_modules
ln -s /deps/package.json /app/package.json

npm run build

# Generate runtime config with backend URL
# Backend URL is derived by replacing 'frontend' with 'backend' in our automation URL
BACKEND_URL=$(echo "$BITSWAN_AUTOMATION_URL" | sed 's/-frontend/-backend/')

cat > dist/config.js << EOF
window.__BITSWAN_CONFIG__ = {
  backendUrl: "${BACKEND_URL}",
  automationUrl: "${BITSWAN_AUTOMATION_URL}",
  stage: "${BITSWAN_AUTOMATION_STAGE}",
  deploymentId: "${BITSWAN_DEPLOYMENT_ID}"
};
EOF

exec serve -s dist -l 8080
