import { useState, useEffect } from 'react'
import './App.css'

// Helper to construct automation URLs using the config components
const getAutomationUrl = (deploymentId) => {
  const config = window.__BITSWAN_CONFIG__
  if (config?.urlPrefix && config?.urlSuffix) {
    return `${config.urlPrefix}${deploymentId}${config.urlSuffix}`
  }
  return null
}

// Get backend URL from runtime config
const getBackendUrl = () => {
  const config = window.__BITSWAN_CONFIG__
  console.log('BitSwan config:', config)

  // Use pre-computed backend URL from config
  if (config?.backendUrl) {
    return config.backendUrl
  }

  // Fallback: try to derive from current URL
  const currentUrl = window.location.origin
  if (currentUrl.includes('-frontend')) {
    return currentUrl.replace(/-frontend/g, '-backend')
  }

  return null
}

function App() {
  const [message, setMessage] = useState('Loading...')
  const [count, setCount] = useState(0)
  const [backendUrl] = useState(getBackendUrl)

  useEffect(() => {
    if (!backendUrl) {
      setMessage('Backend URL not configured')
      return
    }

    console.log('Fetching from:', backendUrl)

    fetch(`${backendUrl}/`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then(data => setMessage(data.message))
      .catch(err => {
        console.error('Backend fetch error:', err)
        setMessage(`Failed: ${err.message}`)
      })
  }, [backendUrl])

  const incrementCount = async () => {
    if (!backendUrl) return
    try {
      const res = await fetch(`${backendUrl}/count`, { method: 'POST' })
      const data = await res.json()
      setCount(data.count)
    } catch (err) {
      console.error('Failed to increment count:', err)
    }
  }

  return (
    <div className="app">
      <h1>React + FastAPI</h1>
      <p className="message">Backend says: {message}</p>
      <div className="card">
        <button onClick={incrementCount}>
          Count: {count}
        </button>
        <p>Click the button to call the backend API</p>
      </div>
    </div>
  )
}

export default App
