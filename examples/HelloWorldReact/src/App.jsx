import { useState } from 'react'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div style={{
      fontFamily: 'system-ui, sans-serif',
      maxWidth: '600px',
      margin: '100px auto',
      textAlign: 'center'
    }}>
      <h1>Hello World!</h1>
      <p>Welcome to your BitSwan React automation.</p>
      <div style={{ marginTop: '2rem' }}>
        <button
          onClick={() => setCount(c => c + 1)}
          style={{
            padding: '10px 20px',
            fontSize: '16px',
            cursor: 'pointer'
          }}
        >
          Count: {count}
        </button>
      </div>
    </div>
  )
}

export default App
