package main

import (
	"fmt"
	"log"

	"backend/models"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

func mustInitDB() *gorm.DB {
	host := envOr("POSTGRES_HOST", "localhost")
	user := envOr("POSTGRES_USER", "admin")
	password := envOr("POSTGRES_PASSWORD", "")
	dbname := envOr("POSTGRES_DB", "postgres")
	port := envOr("POSTGRES_PORT", "5432")

	dsn := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		host, port, user, password, dbname)

	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		log.Fatalf("failed to connect to database: %v", err)
	}

	sqlDB, err := db.DB()
	if err != nil {
		log.Fatalf("failed to get underlying sql.DB: %v", err)
	}
	sqlDB.SetMaxOpenConns(5)

	// Auto-migrate tables.
	if err := db.AutoMigrate(&models.UserCounter{}, &models.GalleryImage{}); err != nil {
		log.Fatalf("failed to migrate database: %v", err)
	}

	return db
}

func listGalleryImages(db *gorm.DB) ([]models.GalleryImage, error) {
	var images []models.GalleryImage
	err := db.Order("created_at desc").Find(&images).Error
	return images, err
}

func getCount(db *gorm.DB, username string) (int, error) {
	var counter models.UserCounter
	err := db.Where("username = ?", username).First(&counter).Error
	if err == gorm.ErrRecordNotFound {
		return 0, nil
	}
	return counter.Count, err
}

func incrementCount(db *gorm.DB, username string) (int, error) {
	var counter models.UserCounter
	err := db.Where("username = ?", username).First(&counter).Error
	if err == gorm.ErrRecordNotFound {
		counter = models.UserCounter{Username: username, Count: 1}
		if err := db.Create(&counter).Error; err != nil {
			return 0, err
		}
		return 1, nil
	}
	if err != nil {
		return 0, err
	}
	counter.Count++
	if err := db.Save(&counter).Error; err != nil {
		return 0, err
	}
	return counter.Count, nil
}

func insertGalleryImage(db *gorm.DB, key, title, contentType string, size int, uploadedBy string) (*models.GalleryImage, error) {
	img := &models.GalleryImage{
		Key:         key,
		Title:       title,
		ContentType: contentType,
		Size:        size,
		UploadedBy:  uploadedBy,
	}
	if err := db.Create(img).Error; err != nil {
		return nil, err
	}
	return img, nil
}

func deleteGalleryImage(db *gorm.DB, key string) error {
	result := db.Where("key = ?", key).Delete(&models.GalleryImage{})
	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return gorm.ErrRecordNotFound
	}
	return nil
}

func galleryImageExists(db *gorm.DB, key string) bool {
	var count int64
	db.Model(&models.GalleryImage{}).Where("key = ?", key).Count(&count)
	return count > 0
}
