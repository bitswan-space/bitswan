import Keycloak from 'keycloak-js'

declare global {
  interface Window {
    __BITSWAN_CONFIG__?: BitswanConfig | null
  }
}

interface KeycloakConfig {
  url?: string
  realm?: string
  clientId?: string
}

interface BitswanConfig {
  workspaceName?: string
  deploymentId?: string
  stage?: string
  domain?: string
  keycloak?: KeycloakConfig
}

export interface UserInfo {
  username?: string
  email?: string
  name?: string
}

const getConfig = (): BitswanConfig => window.__BITSWAN_CONFIG__ || {}

let keycloakInstance: Keycloak | null = null

export const initKeycloak = (): Promise<Keycloak | null> => {
  const config = getConfig()

  if (!config.keycloak?.url || !config.keycloak?.realm || !config.keycloak?.clientId) {
    console.warn('Keycloak configuration not available')
    return Promise.resolve(null)
  }

  keycloakInstance = new Keycloak({
    url: config.keycloak.url,
    realm: config.keycloak.realm,
    clientId: config.keycloak.clientId,
  })

  return keycloakInstance.init({
    onLoad: 'login-required',
    checkLoginIframe: false,
  }).then(authenticated => {
    if (authenticated) {
      console.log('User authenticated')
      return keycloakInstance
    } else {
      console.log('User not authenticated')
      return null
    }
  }).catch(err => {
    console.error('Keycloak init failed:', err)
    return null
  })
}

export const getKeycloak = (): Keycloak | null => keycloakInstance

export const logout = (): void => {
  if (keycloakInstance) {
    keycloakInstance.logout()
  }
}

export const getToken = (): string | undefined => {
  return keycloakInstance?.token
}

export const getUserInfo = (): UserInfo | null => {
  if (!keycloakInstance?.tokenParsed) return null

  return {
    username: keycloakInstance.tokenParsed.preferred_username as string | undefined,
    email: keycloakInstance.tokenParsed.email as string | undefined,
    name: keycloakInstance.tokenParsed.name as string | undefined,
  }
}
