import { useState, useEffect } from 'react'
import { backend } from './api'
import './App.css'

function App() {
  const [message, setMessage] = useState('Loading...')
  const [count, setCount] = useState(0)

  useEffect(() => {
    backend.get('/')
      .then(data => setMessage(data.message))
      .catch(err => setMessage(`Error: ${err.message}`))
  }, [])

  const incrementCount = async () => {
    try {
      const data = await backend.post('/count')
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
