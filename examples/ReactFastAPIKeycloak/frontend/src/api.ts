// BitSwan API client for connecting to backend automations

import { getToken } from './keycloak'

interface BitswanConfig {
  workspaceName?: string
  deploymentId?: string
  stage?: string
  domain?: string
}

const getConfig = (): BitswanConfig => window.__BITSWAN_CONFIG__ || {}

// Get the base deployment ID (without stage suffix)
// e.g., "myapp-frontend-dev" with stage "dev" -> "myapp-frontend"
const getBaseDeploymentId = (): string | null => {
  const config = getConfig()
  if (!config.deploymentId) {
    return null
  }

  let baseId = config.deploymentId

  // Strip stage suffix if present (deployment ID might include it)
  if (config.stage && baseId.endsWith(`-${config.stage}`)) {
    baseId = baseId.slice(0, -(config.stage.length + 1))
  }

  return baseId
}

// Build URL for a deployment from components
// URL format: https://{workspace}-{deployment_id}-{stage}.{domain} (dev/staging)
// URL format: https://{workspace}-{deployment_id}.{domain} (production)
const buildUrl = (baseDeploymentId: string): string | null => {
  const config = getConfig()
  if (!config.workspaceName || !config.domain) {
    return null
  }

  // Stage is appended to deployment ID (dev/staging), or omitted (production)
  const fullDeploymentId = config.stage
    ? `${baseDeploymentId}-${config.stage}`
    : baseDeploymentId

  return `https://${config.workspaceName}-${fullDeploymentId}.${config.domain}`
}

// Get URL for any automation by replacing our suffix (e.g., "frontend" -> "backend")
export const getAutomationUrl = (automationSuffix: string): string | null => {
  const baseId = getBaseDeploymentId()
  if (!baseId) {
    return null
  }

  // Replace "frontend" with the requested suffix
  const targetDeploymentId = baseId.replace('-frontend', `-${automationSuffix}`)
  return buildUrl(targetDeploymentId)
}

// Get the backend URL by replacing "frontend" with "backend"
export const getBackendUrl = (): string | null => {
  const baseId = getBaseDeploymentId()
  if (!baseId) {
    return null
  }

  // e.g., "myapp-frontend" -> "myapp-backend"
  const backendDeploymentId = baseId.replace('-frontend', '-backend')
  return buildUrl(backendDeploymentId)
}

// Backend API client
class BackendClient {
  baseUrl: string | null

  constructor(baseUrl: string | null = null) {
    this.baseUrl = baseUrl || getBackendUrl()
  }

  async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    if (!this.baseUrl) {
      throw new Error('Backend URL not configured')
    }

    const url = `${this.baseUrl}${path}`
    const token = getToken()
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    return response.json()
  }

  get<T>(path: string): Promise<T> {
    return this.request<T>(path)
  }

  post<T>(path: string, data?: unknown): Promise<T> {
    return this.request<T>(path, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  put<T>(path: string, data: unknown): Promise<T> {
    return this.request<T>(path, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  delete<T>(path: string): Promise<T> {
    return this.request<T>(path, { method: 'DELETE' })
  }
}

// Singleton instance
export const backend = new BackendClient()

export default BackendClient
