package models

// UserCounter tracks per-user click counts.
type UserCounter struct {
	Username string `gorm:"primaryKey;type:text"`
	Count    int    `gorm:"not null;default:0"`
}
