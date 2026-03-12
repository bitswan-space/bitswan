import { useState, useEffect } from 'react'
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
  const [gallery, setGallery] = useState<GalleryImage[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    backend.get<GalleryResponse>('/gallery')
      .then(data => setGallery(data.images))
      .catch(err => setError(err.message))
  }, [])

  return (
    <div className="app">
      <h1>BitSwan Public App</h1>

      {error && <p className="message">Error: {error}</p>}

      <div className="card">
        <h2>Image Gallery</h2>
        <p>Images shared by internal users</p>
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
          {gallery.length === 0 && !error && <p>No images yet.</p>}
        </div>
      </div>
    </div>
  )
}

export default App
