package main

import (
	"context"
	"crypto/rsa"
	"crypto/tls"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"math/big"
	"net/http"
	"strings"
	"sync"

	jwtv5 "github.com/golang-jwt/jwt/v5"
)

type contextKey string

const claimsKey contextKey = "claims"

// JWKSProvider fetches and caches RSA public keys from a Keycloak JWKS endpoint.
type JWKSProvider struct {
	jwksURL string
	mu      sync.Mutex
	keys    map[string]*rsa.PublicKey
}

func NewJWKSProvider(issuerURL string) *JWKSProvider {
	return &JWKSProvider{
		jwksURL: issuerURL + "/protocol/openid-connect/certs",
	}
}

type jwksResponse struct {
	Keys []jwkKey `json:"keys"`
}

type jwkKey struct {
	Kid string `json:"kid"`
	N   string `json:"n"`
	E   string `json:"e"`
}

func (p *JWKSProvider) fetchKeys() error {
	client := &http.Client{
		Transport: &http.Transport{
			TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
		},
	}
	resp, err := client.Get(p.jwksURL)
	if err != nil {
		return fmt.Errorf("fetching JWKS: %w", err)
	}
	defer resp.Body.Close()

	var jwks jwksResponse
	if err := json.NewDecoder(resp.Body).Decode(&jwks); err != nil {
		return fmt.Errorf("decoding JWKS: %w", err)
	}

	keys := make(map[string]*rsa.PublicKey, len(jwks.Keys))
	for _, k := range jwks.Keys {
		nBytes, err := base64.RawURLEncoding.DecodeString(k.N)
		if err != nil {
			continue
		}
		eBytes, err := base64.RawURLEncoding.DecodeString(k.E)
		if err != nil {
			continue
		}
		n := new(big.Int).SetBytes(nBytes)
		e := 0
		for _, b := range eBytes {
			e = e<<8 + int(b)
		}
		keys[k.Kid] = &rsa.PublicKey{N: n, E: e}
	}
	p.keys = keys
	return nil
}

func (p *JWKSProvider) getKey(kid string) (*rsa.PublicKey, error) {
	p.mu.Lock()
	defer p.mu.Unlock()

	if p.keys != nil {
		if key, ok := p.keys[kid]; ok {
			return key, nil
		}
	}
	// Refetch once on miss (key rotation).
	if err := p.fetchKeys(); err != nil {
		return nil, err
	}
	key, ok := p.keys[kid]
	if !ok {
		return nil, fmt.Errorf("unknown signing key kid=%s", kid)
	}
	return key, nil
}

// requireAuth returns middleware that validates a Bearer JWT and stores claims in context.
func (app *App) requireAuth(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		auth := r.Header.Get("Authorization")
		if !strings.HasPrefix(auth, "Bearer ") {
			writeError(w, http.StatusUnauthorized, "Missing authorization token")
			return
		}
		tokenStr := strings.TrimPrefix(auth, "Bearer ")

		token, err := jwtv5.Parse(tokenStr, func(t *jwtv5.Token) (any, error) {
			if _, ok := t.Method.(*jwtv5.SigningMethodRSA); !ok {
				return nil, fmt.Errorf("unexpected signing method: %v", t.Header["alg"])
			}
			kid, _ := t.Header["kid"].(string)
			return app.jwks.getKey(kid)
		})
		if err != nil {
			writeError(w, http.StatusUnauthorized, "Invalid token: "+err.Error())
			return
		}

		claims, ok := token.Claims.(jwtv5.MapClaims)
		if !ok || !token.Valid {
			writeError(w, http.StatusUnauthorized, "Invalid token claims")
			return
		}

		ctx := context.WithValue(r.Context(), claimsKey, claims)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

func getUsername(r *http.Request) string {
	claims, ok := r.Context().Value(claimsKey).(jwtv5.MapClaims)
	if !ok {
		return "anonymous"
	}
	if u, ok := claims["preferred_username"].(string); ok {
		return u
	}
	return "anonymous"
}
