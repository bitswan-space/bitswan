import { useState, useEffect, useRef } from 'react'
import { backend, getUserInfo, getAccessToken, getTokenInfo, getImageUrl, type UserInfo, type TokenInfo } from './api'
import './App.css'

interface RootResponse {
  message: string
}

interface CountResponse {
  count: number
  user?: string
}

interface GalleryImage {
  id: number
  key: string
  title: string
  content_type: string
  size: number
  uploaded_by: string
  created_at: string
}

interface GalleryResponse {
  images: GalleryImage[]
}

function AuthImage({ path, alt }: { path: string; alt: string }) {
  const [src, setSrc] = useState<string>('')
  useEffect(() => {
    let revoke = ''
    getImageUrl(path).then(url => { setSrc(url); revoke = url }).catch(() => {})
    return () => { if (revoke) URL.revokeObjectURL(revoke) }
  }, [path])
  if (!src) return <div className="gallery-placeholder">Loading...</div>
  return <img src={src} alt={alt} />
}

function App() {
  const [message, setMessage] = useState('Loading...')
  const [count, setCount] = useState(0)
  const [user, setUser] = useState<UserInfo | null>(null)
  const [tokenInfo, setTokenInfo] = useState<TokenInfo | null>(null)
  const [gallery, setGallery] = useState<GalleryImage[]>([])
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    backend.get<RootResponse>('/')
      .then(data => setMessage(data.message))
      .catch(err => setMessage(`Error: ${err.message}`))

    backend.get<CountResponse>('/count')
      .then(data => setCount(data.count))
      .catch(err => console.error('Failed to fetch count:', err))

    getUserInfo()
      .then(setUser)
      .catch(err => console.error('Failed to fetch user info:', err))

    backend.get<GalleryResponse>('/gallery')
      .then(data => setGallery(data.images))
      .catch(err => console.error('Failed to fetch gallery:', err))

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

  const refreshGallery = async () => {
    try {
      const data = await backend.get<GalleryResponse>('/gallery')
      setGallery(data.images)
    } catch (err) {
      console.error('Failed to refresh gallery:', err)
    }
  }

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      await backend.uploadFile('/gallery/upload', file)
      await refreshGallery()
    } catch (err) {
      console.error('Failed to upload:', err)
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleDelete = async (key: string) => {
    try {
      await backend.delete(`/gallery/${key}`)
      await refreshGallery()
    } catch (err) {
      console.error('Failed to delete:', err)
    }
  }

  return (
    <div className="app">
      <h1>BitSwan Internal App</h1>

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
          Your Count: {count}
        </button>
        <p>Click the button to increment your personal counter (stored in PostgreSQL)</p>
      </div>

      <div className="card">
        <h2>Image Gallery</h2>
        <p>Upload images to the shared MinIO gallery. Public users can view these.</p>
        <div className="upload-area">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleUpload}
            disabled={uploading}
          />
          {uploading && <span className="uploading">Uploading...</span>}
        </div>
        <div className="gallery-grid">
          {gallery.map(img => (
            <div key={img.id} className="gallery-item">
              <AuthImage path={`/gallery/${img.key}`} alt={img.title} />
              <div className="gallery-item-info">
                <span className="gallery-item-name" title={img.key}>{img.title}</span>
                <span className="gallery-item-meta">
                  by {img.uploaded_by} &middot; {new Date(img.created_at).toLocaleDateString()}
                </span>
                <button className="delete-btn" onClick={() => handleDelete(img.key)}>Delete</button>
              </div>
            </div>
          ))}
          {gallery.length === 0 && <p>No images yet.</p>}
        </div>
      </div>
    </div>
  )
}

export default App
