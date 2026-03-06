// BitSwan API client for connecting to backend automations

declare global {
  interface Window {
    __BITSWAN_CONFIG__?: BitswanConfig | null
  }
}

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

// Access token management for authenticated backend calls.
// The token is fetched from oauth2-proxy's /oauth2/auth endpoint
// which returns the Keycloak access token in a response header.
let cachedToken: string | null = null

async function fetchAccessToken(): Promise<string | null> {
  try {
    const response = await fetch('/oauth2/auth')
    if (!response.ok) return null
    const token = response.headers.get('X-Auth-Request-Access-Token')
    if (token) cachedToken = token
    return token
  } catch {
    return null
  }
}

export async function getAccessToken(): Promise<string | null> {
  if (cachedToken) return cachedToken
  return fetchAccessToken()
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

    const token = await getAccessToken()
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const url = `${this.baseUrl}${path}`
    let response = await fetch(url, { ...options, headers })

    // If 401, token may have expired — refresh and retry once
    if (response.status === 401 && token) {
      cachedToken = null
      const newToken = await fetchAccessToken()
      if (newToken) {
        headers['Authorization'] = `Bearer ${newToken}`
        response = await fetch(url, { ...options, headers })
      }
    }

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

// OAuth2 Proxy user info
export interface UserInfo {
  email?: string
  user?: string
  groups?: string[]
  preferredUsername?: string
}

export async function getUserInfo(): Promise<UserInfo> {
  const response = await fetch('/oauth2/userinfo')
  if (!response.ok) {
    throw new Error(`Failed to fetch user info: ${response.status}`)
  }
  const data = await response.json()
  return {
    email: data.email,
    user: data.user,
    groups: data.groups,
    preferredUsername: data.preferredUsername || data.preferred_username,
  }
}

export default BackendClient
