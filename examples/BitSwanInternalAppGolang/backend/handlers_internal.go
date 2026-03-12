package main

import (
	"io"
	"net/http"
	"path"
	"strings"
)

func (app *App) handleInternalRoot(w http.ResponseWriter, r *http.Request) {
	username := getUsername(r)
	writeJSON(w, http.StatusOK, map[string]string{
		"message": "Hello from Go!",
		"user":    username,
	})
}

func (app *App) handleGetCount(w http.ResponseWriter, r *http.Request) {
	username := getUsername(r)
	count, err := getCount(app.db, username)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to get count")
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"count": count, "user": username})
}

func (app *App) handleIncrementCount(w http.ResponseWriter, r *http.Request) {
	username := getUsername(r)
	count, err := incrementCount(app.db, username)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to increment count")
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"count": count, "user": username})
}

func (app *App) handleUploadGalleryImage(w http.ResponseWriter, r *http.Request) {
	// Limit upload size to 32 MB.
	r.Body = http.MaxBytesReader(w, r.Body, 32<<20)

	file, header, err := r.FormFile("file")
	if err != nil {
		writeError(w, http.StatusBadRequest, "missing or invalid file")
		return
	}
	defer file.Close()

	contentType := header.Header.Get("Content-Type")
	if !strings.HasPrefix(contentType, "image/") {
		writeError(w, http.StatusBadRequest, "Only image files are allowed")
		return
	}

	data, err := io.ReadAll(file)
	if err != nil {
		writeError(w, http.StatusBadRequest, "failed to read file")
		return
	}

	key := header.Filename
	if err := uploadFile(app.mc, key, data, contentType); err != nil {
		writeError(w, http.StatusInternalServerError, "failed to upload file")
		return
	}

	username := getUsername(r)
	name := strings.TrimSuffix(key, path.Ext(key))
	title := strings.NewReplacer("-", " ", "_", " ").Replace(name)
	// Capitalize first letter of each word (strings.Title is deprecated).
	title = capitalizeWords(title)

	record, err := insertGalleryImage(app.db, key, title, contentType, len(data), username)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "failed to save image record")
		return
	}

	writeJSON(w, http.StatusOK, map[string]any{
		"id":          record.ID,
		"key":         record.Key,
		"title":       record.Title,
		"uploaded_by": record.UploadedBy,
		"size":        record.Size,
	})
}

func (app *App) handleDeleteGalleryImage(w http.ResponseWriter, r *http.Request) {
	filename := r.PathValue("filename")

	if err := deleteGalleryImage(app.db, filename); err != nil {
		writeError(w, http.StatusNotFound, "Image not found")
		return
	}

	if err := deleteFile(app.mc, filename); err != nil {
		writeError(w, http.StatusInternalServerError, "failed to delete file from storage")
		return
	}

	writeJSON(w, http.StatusOK, map[string]string{"deleted": filename})
}
