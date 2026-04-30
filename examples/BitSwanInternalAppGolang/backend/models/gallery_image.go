package models

import "time"

// GalleryImage stores metadata for uploaded images.
type GalleryImage struct {
	ID          uint      `gorm:"primaryKey" json:"id"`
	Key         string    `gorm:"uniqueIndex:idx_gallery_images_key;type:text;not null" json:"key"`
	Title       string    `gorm:"type:text;not null" json:"title"`
	ContentType string    `gorm:"type:text;not null" json:"content_type"`
	Size        int       `gorm:"not null" json:"size"`
	UploadedBy  string    `gorm:"type:text;not null" json:"uploaded_by"`
	CreatedAt   time.Time `gorm:"autoCreateTime" json:"created_at"`
}
