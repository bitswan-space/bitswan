import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { backend, getImageUrl } from './api'
import './App.css'

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

function GalleryImg({ path, alt }: { path: string; alt: string }) {
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
  const [gallery, setGallery] = useState<GalleryImage[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    backend.get<GalleryResponse>('/gallery')
      .then(data => setGallery(data.images))
      .catch(err => setError(err.message))
  }, [])

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

      {error && <p className="message">{t('error.prefix')}: {error}</p>}

      <div className="card">
        <h2>{t('gallery.title')}</h2>
        <p>{t('gallery.description')}</p>
        <div className="gallery-grid">
          {gallery.map(img => (
            <div key={img.id} className="gallery-item">
              <GalleryImg path={`/gallery/${img.key}`} alt={img.title} />
              <div className="gallery-item-info">
                <span className="gallery-item-name" title={img.key}>{img.title}</span>
                <span className="gallery-item-meta">
                  by {img.uploaded_by} &middot; {new Date(img.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          ))}
          {gallery.length === 0 && !error && <p>{t('gallery.empty')}</p>}
        </div>
      </div>
    </div>
  )
}

export default App
