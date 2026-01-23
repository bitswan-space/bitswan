import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [message, setMessage] = useState('Loading...')
  const [count, setCount] = useState(0)

  useEffect(() => {
    fetch('/api/')
      .then(res => res.json())
      .then(data => setMessage(data.message))
      .catch(() => setMessage('Failed to connect to backend'))
  }, [])

  const incrementCount = async () => {
    try {
      const res = await fetch('/api/count', { method: 'POST' })
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
