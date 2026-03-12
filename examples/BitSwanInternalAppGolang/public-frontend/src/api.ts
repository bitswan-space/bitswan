// BitSwan API client for the public app (no authentication required)

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
  urlTemplate?: string
}

const getConfig = (): BitswanConfig => window.__BITSWAN_CONFIG__ || {}

// Build URL for a named automation using the URL template.
// BITSWAN_URL_TEMPLATE looks like: https://editor-sandbox-{name}-live-dev.sandbox.bitswan.ai
// Replace {name} with the automation name (e.g., "backend", "frontend").
export const getAutomationUrl = (name: string): string | null => {
  const config = getConfig()
  if (config.urlTemplate) {
    return config.urlTemplate.replace('{name}', name)
  }
  return null
}

// Get the backend URL (public endpoints live under /public)
export const getBackendUrl = (): string | null => {
  const base = getAutomationUrl('backend')
  return base ? `${base}/public` : null
}

// Backend API client (no auth — public app)
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
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers as Record<string, string>),
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    return response.json()
  }

  get<T>(path: string): Promise<T> {
    return this.request<T>(path)
  }
}

// Singleton instance
export const backend = new BackendClient()

// Fetch an image from the backend (no auth needed)
export async function getImageUrl(path: string): Promise<string> {
  if (!backend.baseUrl) throw new Error('Backend URL not configured')
  const response = await fetch(`${backend.baseUrl}${path}`)
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  const blob = await response.blob()
  return URL.createObjectURL(blob)
}

export default BackendClient
