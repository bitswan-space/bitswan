import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import { initKeycloak } from './keycloak'
import './index.css'

const root = createRoot(document.getElementById('root')!)

// Show loading state while initializing Keycloak
root.render(<div className="app"><h1>Loading...</h1></div>)

// Initialize Keycloak, then render the app
initKeycloak().then((keycloak) => {
  if (keycloak) {
    root.render(
      <StrictMode>
        <App />
      </StrictMode>,
    )
  } else {
    root.render(
      <div className="app">
        <h1>Authentication Error</h1>
        <p>Could not initialize authentication. Please check the configuration.</p>
      </div>
    )
  }
})
