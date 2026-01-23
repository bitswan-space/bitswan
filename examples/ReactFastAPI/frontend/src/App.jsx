import { useState, useEffect } from 'react'
import './App.css'

// Get backend URL from runtime config (set by entrypoint.sh)
const getBackendUrl = () => {
  const config = window.__BITSWAN_CONFIG__
  console.log('BitSwan config:', config)

  if (config?.backendUrl) {
    return config.backendUrl
  }

  // Fallback: try to derive from current URL by replacing '-frontend' with '-backend'
  const currentUrl = window.location.origin
  if (currentUrl.includes('-frontend')) {
    return currentUrl.replace(/-frontend/g, '-backend')
  }

  // Last resort for local development
  return 'http://localhost:8000'
}

function App() {
  const [message, setMessage] = useState('Loading...')
  const [count, setCount] = useState(0)
  const [backendUrl] = useState(getBackendUrl)

  useEffect(() => {
    console.log('Fetching from:', backendUrl)

    if (!backendUrl || backendUrl === 'http://localhost:8000') {
      setMessage(`Config not loaded. Trying: ${backendUrl}`)
    }

    fetch(`${backendUrl}/`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then(data => setMessage(data.message))
      .catch(err => {
        console.error('Backend fetch error:', err)
        setMessage(`Failed to connect to ${backendUrl}: ${err.message}`)
      })
  }, [backendUrl])

  const incrementCount = async () => {
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
