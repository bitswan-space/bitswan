import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import { handleCallback, isAuthenticated, login } from './auth'
import './index.css'

const root = createRoot(document.getElementById('root')!)

// Show loading state while checking auth
root.render(<div className="app"><h1>Loading...</h1></div>)

async function init() {
  // Check if this is a callback from AOC (has ?code= param)
  const params = new URLSearchParams(window.location.search)
  if (params.has('code')) {
    const success = await handleCallback()
    if (!success) {
      root.render(
        <div className="app">
          <h1>Authentication Error</h1>
          <p>Failed to complete authentication. Please try again.</p>
          <button onClick={() => login()}>Retry Login</button>
        </div>
      )
      return
    }
  }

  // Check for error from AOC
  if (params.has('error')) {
    const error = params.get('error')
    root.render(
      <div className="app">
        <h1>Authentication Error</h1>
        <p>Error: {error}</p>
        <button onClick={() => login()}>Retry Login</button>
      </div>
    )
    return
  }

  // If authenticated, render the app
  if (isAuthenticated()) {
    root.render(
      <StrictMode>
        <App />
      </StrictMode>,
    )
  } else {
    // Not authenticated, redirect to login
    login()
  }
}

init()
