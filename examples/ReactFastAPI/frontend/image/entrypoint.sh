#!/bin/sh
set -e

ln -s /deps/node_modules /app/node_modules
ln -s /deps/package.json /app/package.json

npm run build

# Pass URL components to the frontend
# URL format: https://{workspace}-{deployment_id}.{domain}
# The frontend derives backend URL by replacing "frontend" with "backend" in deployment ID

cat > dist/config.js << EOF
window.__BITSWAN_CONFIG__ = {
  workspaceName: "${BITSWAN_WORKSPACE_NAME}",
  deploymentId: "${BITSWAN_DEPLOYMENT_ID}",
  stage: "${BITSWAN_AUTOMATION_STAGE}",
  domain: "${BITSWAN_GITOPS_DOMAIN}"
};
EOF

exec serve -s dist -l 8080
