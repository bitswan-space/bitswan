import { useState, useEffect } from 'react'
import { backend } from './api'
import { getUserInfo, logout } from './keycloak'
import './App.css'

interface RootResponse {
  message: string
}

interface CountResponse {
  count: number
}

function App() {
  const [message, setMessage] = useState('Loading...')
  const [count, setCount] = useState(0)
  const user = getUserInfo()

  useEffect(() => {
    backend.get<RootResponse>('/')
      .then(data => setMessage(data.message))
      .catch(err => setMessage(`Error: ${err.message}`))
  }, [])

  const incrementCount = async () => {
    try {
      const data = await backend.post<CountResponse>('/count')
      setCount(data.count)
    } catch (err) {
      console.error('Failed to increment count:', err)
    }
  }

  return (
    <div className="app">
      <div className="user-bar">
        <span>Welcome, {user?.name || user?.username || 'User'}</span>
        <button onClick={logout} className="logout-btn">Logout</button>
      </div>
      <h1>React + FastAPI + Keycloak</h1>
      <p className="message">Backend says: {message}</p>
      <div className="card">
        <button onClick={incrementCount}>
          Count: {count}
        </button>
        <p>Click the button to call the backend API</p>
      </div>
      {user && (
        <div className="user-info">
          <h3>User Info</h3>
          <p>Username: {user.username}</p>
          <p>Email: {user.email}</p>
          <p>Name: {user.name}</p>
        </div>
      )}
    </div>
  )
}

export default App
