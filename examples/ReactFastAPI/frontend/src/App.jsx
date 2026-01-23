import { useState, useEffect } from 'react'
import './App.css'

// Get backend URL from runtime config (set by entrypoint.sh) or use relative path for local dev
const getBackendUrl = () => {
  if (window.__BITSWAN_CONFIG__?.backendUrl) {
    return window.__BITSWAN_CONFIG__.backendUrl
  }
  // Fallback for local development - assume backend is on port 8000
  return 'http://localhost:8000'
}

function App() {
  const [message, setMessage] = useState('Loading...')
  const [count, setCount] = useState(0)
  const backendUrl = getBackendUrl()

  useEffect(() => {
    fetch(`${backendUrl}/`)
      .then(res => res.json())
      .then(data => setMessage(data.message))
      .catch(() => setMessage('Failed to connect to backend'))
  }, [backendUrl])

  const incrementCount = async () => {
    try {
      const res = await fetch(`${backendUrl}/count`, { method: 'POST' })
      const data = await res.json()
      setCount(data.count)
    } catch {
      console.error('Failed to increment count')
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
