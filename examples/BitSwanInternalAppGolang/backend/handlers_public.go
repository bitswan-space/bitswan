package main

import (
	"net/http"
)

func (app *App) handleHealth(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (app *App) handlePublicRoot(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{"message": "Hello from the public API!"})
}

func (app *App) handleListGallery(w http.ResponseWriter, r *http.Request) {
	images, err := listGalleryImages(app.db)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to list gallery")
		return
	}

	type imageJSON struct {
		ID          uint   `json:"id"`
		Key         string `json:"key"`
		Title       string `json:"title"`
		ContentType string `json:"content_type"`
		Size        int    `json:"size"`
		UploadedBy  string `json:"uploaded_by"`
		CreatedAt   string `json:"created_at"`
	}

	result := make([]imageJSON, 0, len(images))
	for _, img := range images {
		result = append(result, imageJSON{
			ID:          img.ID,
			Key:         img.Key,
			Title:       img.Title,
			ContentType: img.ContentType,
			Size:        img.Size,
			UploadedBy:  img.UploadedBy,
			CreatedAt:   img.CreatedAt.Format("2006-01-02T15:04:05.000000-07:00"),
		})
	}
	writeJSON(w, http.StatusOK, map[string]any{"images": result})
}

func (app *App) handleGetGalleryImage(w http.ResponseWriter, r *http.Request) {
	filename := r.PathValue("filename")
	data, contentType, err := getFile(app.mc, filename)
	if err != nil {
		writeError(w, http.StatusNotFound, "Image not found")
		return
	}
	w.Header().Set("Content-Type", contentType)
	w.Write(data)
}
