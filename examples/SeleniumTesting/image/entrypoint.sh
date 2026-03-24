#!/bin/bash
# Keep the container running so the agent can exec tests into it
echo "Selenium testing container ready."
echo "Run tests with: bitswan-agent deployments exec DEPLOYMENT_ID -- pytest /app/tests/"
exec tail -f /dev/null
