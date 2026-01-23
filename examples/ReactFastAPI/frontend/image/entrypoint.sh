#!/bin/sh
set -e

ln -s /deps/node_modules /app/node_modules
ln -s /deps/package.json /app/package.json

npm run build

# Generate runtime config with backend URL
# Backend deployment ID is derived by replacing 'frontend' with 'backend' in our deployment ID
BACKEND_ID=$(echo "$BITSWAN_DEPLOYMENT_ID" | sed 's/-frontend$/-backend/')
BACKEND_URL="https://${BITSWAN_WORKSPACE_NAME}-${BACKEND_ID}-${BITSWAN_AUTOMATION_STAGE}.${BITSWAN_GITOPS_DOMAIN}"

cat > dist/config.js << EOF
window.__BITSWAN_CONFIG__ = {
  backendUrl: "${BACKEND_URL}",
  stage: "${BITSWAN_AUTOMATION_STAGE}",
  deploymentId: "${BITSWAN_DEPLOYMENT_ID}",
  workspaceName: "${BITSWAN_WORKSPACE_NAME}"
};
EOF

exec serve -s dist -l 8080
