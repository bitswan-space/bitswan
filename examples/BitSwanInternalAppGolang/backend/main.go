package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"strings"
	"unicode"

	"github.com/minio/minio-go/v7"
	"gorm.io/gorm"
)

// App holds shared dependencies.
type App struct {
	db   *gorm.DB
	mc   *minio.Client
	jwks *JWKSProvider
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func mustEnv(key string) string {
	v := os.Getenv(key)
	if v == "" {
		log.Fatalf("required environment variable %s is not set", key)
	}
	return v
}

// capitalizeWords uppercases the first letter of each space-separated word.
func capitalizeWords(s string) string {
	words := strings.Fields(s)
	for i, w := range words {
		if len(w) > 0 {
			runes := []rune(w)
			runes[0] = unicode.ToUpper(runes[0])
			words[i] = string(runes)
		}
	}
	return strings.Join(words, " ")
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v)
}

func writeError(w http.ResponseWriter, status int, msg string) {
	writeJSON(w, status, map[string]string{"detail": msg})
}

// corsMiddleware wraps an http.Handler with permissive CORS headers.
func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func main() {
	db := mustInitDB()
	sqlDB, _ := db.DB()
	defer sqlDB.Close()

	mc := mustInitMinio()
	ensureBucket(mc)
	preseedLogo(mc, db)

	issuerURL := mustEnv("KEYCLOAK_ISSUER_URL")
	jwks := NewJWKSProvider(issuerURL)

	app := &App{db: db, mc: mc, jwks: jwks}

	mux := http.NewServeMux()

	// Health (no auth)
	mux.HandleFunc("GET /health", app.handleHealth)

	// Public routes (no auth)
	mux.HandleFunc("GET /public/", app.handlePublicRoot)
	mux.HandleFunc("GET /public/gallery", app.handleListGallery)
	mux.HandleFunc("GET /public/gallery/{filename...}", app.handleGetGalleryImage)

	// Internal routes (auth required)
	mux.Handle("GET /internal/", app.requireAuth(http.HandlerFunc(app.handleInternalRoot)))
	mux.Handle("GET /internal/count", app.requireAuth(http.HandlerFunc(app.handleGetCount)))
	mux.Handle("POST /internal/count", app.requireAuth(http.HandlerFunc(app.handleIncrementCount)))
	mux.Handle("GET /internal/gallery", app.requireAuth(http.HandlerFunc(app.handleListGallery)))
	mux.Handle("GET /internal/gallery/{filename...}", app.requireAuth(http.HandlerFunc(app.handleGetGalleryImage)))
	mux.Handle("POST /internal/gallery/upload", app.requireAuth(http.HandlerFunc(app.handleUploadGalleryImage)))
	mux.Handle("DELETE /internal/gallery/{filename...}", app.requireAuth(http.HandlerFunc(app.handleDeleteGalleryImage)))

	handler := corsMiddleware(mux)

	log.Println("listening on :8080")
	if err := http.ListenAndServe(":8080", handler); err != nil {
		log.Fatal(err)
	}
}
