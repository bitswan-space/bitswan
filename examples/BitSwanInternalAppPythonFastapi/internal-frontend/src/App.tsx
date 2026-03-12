import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { backend, getUserInfo, getAccessToken, getImageUrl, getTokenInfo, type UserInfo, type TokenInfo } from './api'
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

function useTheme() {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const stored = localStorage.getItem('theme')
    if (stored === 'light' || stored === 'dark') return stored
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggle = () => setTheme(t => t === 'dark' ? 'light' : 'dark')
  return { theme, toggle }
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
  const { t, i18n } = useTranslation()
  const { theme, toggle: toggleTheme } = useTheme()
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

    getAccessToken()
      .then(() => setTokenInfo(getTokenInfo()))
      .catch(() => {})
  }, [])

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

  const toggleLang = () => {
    i18n.changeLanguage(i18n.language === 'cs' ? 'en' : 'cs')
  }

  return (
    <div className="app">
      <div className="toolbar">
        <button onClick={toggleLang}>
          {i18n.language === 'cs' ? t('language.en') : t('language.cs')}
        </button>
        <button onClick={toggleTheme}>
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
      </div>

      <h1>{t('app.title')}</h1>
      <p className="description">{t('app.description')}</p>

      {user && (
        <div className="card">
          <h2>{t('userInfo.title')}</h2>
          {user.email && <p>{t('userInfo.email')}: {user.email}</p>}
          {user.preferredUsername && <p>{t('userInfo.username')}: {user.preferredUsername}</p>}
          {user.groups && user.groups.length > 0 && (
            <p>{t('userInfo.groups')}: {user.groups.join(', ')}</p>
          )}
          <button className="sign-out" onClick={() => window.location.href = '/oauth2/sign_out'}>
            {t('userInfo.signOut')}
          </button>
        </div>
      )}

      {tokenInfo && (
        <div className="card">
          <h2>{t('tokenInfo.title')}</h2>
          <p>{t('tokenInfo.issued')}: {tokenInfo.issuedAt.toLocaleTimeString()}</p>
          <p>{t('tokenInfo.expires')}: {tokenInfo.expiresAt.toLocaleTimeString()}</p>
          <p className={tokenInfo.ttlSeconds <= 0 ? 'expired' : ''}>
            {t('tokenInfo.ttl')}: {tokenInfo.ttlSeconds}s {tokenInfo.ttlSeconds <= 0 ? `(${t('tokenInfo.expired')})` : ''}
          </p>
        </div>
      )}

      <p className="message">Backend says: {message}</p>
      <div className="card">
        <button onClick={incrementCount}>
          {t('counter.title')}: {count}
        </button>
        <p>{t('counter.description')}</p>
      </div>

      <div className="card">
        <h2>{t('gallery.title')}</h2>
        <p>{t('gallery.description')}</p>
        <div className="upload-area">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleUpload}
            disabled={uploading}
          />
          {uploading && <span className="uploading">{t('gallery.uploading')}</span>}
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
                <button className="delete-btn" onClick={() => handleDelete(img.key)}>{t('gallery.delete')}</button>
              </div>
            </div>
          ))}
          {gallery.length === 0 && <p>{t('gallery.empty')}</p>}
        </div>
      </div>
    </div>
  )
}

export default App
