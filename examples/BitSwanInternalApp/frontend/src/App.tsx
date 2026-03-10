import { useState, useEffect } from 'react'
import { backend, getUserInfo, getAccessToken, getTokenInfo, type UserInfo, type TokenInfo } from './api'
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
  const [user, setUser] = useState<UserInfo | null>(null)
  const [tokenInfo, setTokenInfo] = useState<TokenInfo | null>(null)

  useEffect(() => {
    backend.get<RootResponse>('/')
      .then(data => setMessage(data.message))
      .catch(err => setMessage(`Error: ${err.message}`))

    getUserInfo()
      .then(setUser)
      .catch(err => console.error('Failed to fetch user info:', err))

    // Fetch token so we can display its info
    getAccessToken()
      .then(() => setTokenInfo(getTokenInfo()))
      .catch(() => {})
  }, [])

  // Update TTL every second
  useEffect(() => {
    const interval = setInterval(() => {
      const info = getTokenInfo()
      if (info) setTokenInfo(info)
    }, 1000)
    return () => clearInterval(interval)
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
      <h1>React + FastAPI</h1>

      {user && (
        <div className="card">
          <h2>User Info</h2>
          {user.email && <p>Email: {user.email}</p>}
          {user.preferredUsername && <p>Username: {user.preferredUsername}</p>}
          {user.groups && user.groups.length > 0 && (
            <p>Groups: {user.groups.join(', ')}</p>
          )}
          <button className="sign-out" onClick={() => window.location.href = '/oauth2/sign_out'}>
            Sign Out
          </button>
        </div>
      )}

      {tokenInfo && (
        <div className="card">
          <h2>Token Info</h2>
          <p>Issued: {tokenInfo.issuedAt.toLocaleTimeString()}</p>
          <p>Expires: {tokenInfo.expiresAt.toLocaleTimeString()}</p>
          <p className={tokenInfo.ttlSeconds <= 0 ? 'expired' : ''}>
            TTL: {tokenInfo.ttlSeconds}s {tokenInfo.ttlSeconds <= 0 ? '(expired)' : ''}
          </p>
        </div>
      )}

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
