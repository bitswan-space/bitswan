import Keycloak from 'keycloak-js'

const getConfig = () => window.__BITSWAN_CONFIG__ || {}

let keycloakInstance = null

export const initKeycloak = () => {
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

export const getKeycloak = () => keycloakInstance

export const logout = () => {
  if (keycloakInstance) {
    keycloakInstance.logout()
  }
}

export const getToken = () => {
  return keycloakInstance?.token
}

export const getUserInfo = () => {
  if (!keycloakInstance?.tokenParsed) return null
  
  return {
    username: keycloakInstance.tokenParsed.preferred_username,
    email: keycloakInstance.tokenParsed.email,
    name: keycloakInstance.tokenParsed.name,
  }
}
