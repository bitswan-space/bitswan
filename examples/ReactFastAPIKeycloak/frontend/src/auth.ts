// AOC-based authentication for deployment frontends.
// Replaces direct Keycloak interaction to prevent PII leakage.

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
  aocUrl?: string
  workspaceId?: string
}

export interface UserInfo {
  username?: string
  sub?: string
  email?: string
  workspace_id?: string
  groups?: string[]
}

const getConfig = (): BitswanConfig => window.__BITSWAN_CONFIG__ || {}

const TOKEN_KEY = 'aoc_access_token'

/**
 * Redirect to AOC login endpoint, which will redirect to Keycloak.
 */
export const login = (): void => {
  const config = getConfig()
  if (!config.aocUrl || !config.workspaceId) {
    console.error('AOC URL or workspace ID not configured')
    return
  }

  const params = new URLSearchParams({
    workspace_id: config.workspaceId,
    redirect_uri: window.location.origin,
  })

  window.location.href = `${config.aocUrl}/api/auth/login?${params}`
}

/**
 * Handle the callback from AOC (after Keycloak login).
 * Exchanges the one-time code for a JWT via POST request.
 * Returns true if authentication succeeded.
 */
export const handleCallback = async (): Promise<boolean> => {
  const params = new URLSearchParams(window.location.search)
  const code = params.get('code')
  const error = params.get('error')

  if (error) {
    console.error('Authentication error:', error)
    return false
  }

  if (!code) {
    return false
  }

  const config = getConfig()
  if (!config.aocUrl) {
    console.error('AOC URL not configured')
    return false
  }

  try {
    const response = await fetch(`${config.aocUrl}/api/auth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code }),
    })

    if (!response.ok) {
      console.error('Token exchange failed:', response.status)
      return false
    }

    const data = await response.json()
    sessionStorage.setItem(TOKEN_KEY, data.access_token)

    // Clean URL (remove code param)
    window.history.replaceState({}, '', window.location.pathname)
    return true
  } catch (err) {
    console.error('Token exchange error:', err)
    return false
  }
}

/**
 * Get the stored access token.
 */
export const getToken = (): string | undefined => {
  return sessionStorage.getItem(TOKEN_KEY) || undefined
}

/**
 * Check if the user is authenticated.
 */
export const isAuthenticated = (): boolean => {
  const token = getToken()
  if (!token) return false

  // Check if token is expired
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.exp > Date.now() / 1000
  } catch {
    return false
  }
}

/**
 * Logout: clear stored token and redirect to home.
 */
export const logout = (): void => {
  sessionStorage.removeItem(TOKEN_KEY)
  window.location.href = window.location.origin
}

/**
 * Get user info from the JWT payload (client-side decode, no verification).
 */
export const getUserInfo = (): UserInfo | null => {
  const token = getToken()
  if (!token) return null

  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return {
      username: payload.preferred_username,
      sub: payload.sub,
      email: payload.email,
      workspace_id: payload.workspace_id,
      groups: payload.groups,
    }
  } catch {
    return null
  }
}
