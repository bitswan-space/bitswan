// BitSwan API client for connecting to backend automations

const getConfig = () => window.__BITSWAN_CONFIG__ || {}

// Build URL for a deployment from components
// URL format: https://{workspace}-{deployment_id}.{domain}
const buildUrl = (deploymentId) => {
  const config = getConfig()
  if (!config.workspaceName || !config.domain) {
    return null
  }
  return `https://${config.workspaceName}-${deploymentId}.${config.domain}`
}

// Get URL for any automation in this group by replacing our suffix
// e.g., if we are "myapp-frontend-dev", getAutomationUrl("backend") returns URL for "myapp-backend-dev"
export const getAutomationUrl = (automationSuffix) => {
  const config = getConfig()
  if (!config.deploymentId) {
    return null
  }

  // Replace "frontend" with the requested suffix in our deployment ID
  const targetDeploymentId = config.deploymentId.replace('-frontend', `-${automationSuffix}`)
  return buildUrl(targetDeploymentId)
}

// Get the backend URL by replacing "frontend" with "backend" in our deployment ID
export const getBackendUrl = () => {
  const config = getConfig()
  if (!config.deploymentId) {
    return null
  }

  // Our deployment ID is like "myapp-frontend-dev"
  // Replace "frontend" with "backend" to get "myapp-backend-dev"
  const backendDeploymentId = config.deploymentId.replace('-frontend', '-backend')
  return buildUrl(backendDeploymentId)
}

// Backend API client
class BackendClient {
  constructor(baseUrl = null) {
    this.baseUrl = baseUrl || getBackendUrl()
  }

  async request(path, options = {}) {
    if (!this.baseUrl) {
      throw new Error('Backend URL not configured')
    }

    const url = `${this.baseUrl}${path}`
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    return response.json()
  }

  get(path) {
    return this.request(path)
  }

  post(path, data) {
    return this.request(path, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  put(path, data) {
    return this.request(path, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  delete(path) {
    return this.request(path, { method: 'DELETE' })
  }
}

// Singleton instance
export const backend = new BackendClient()

export default BackendClient
