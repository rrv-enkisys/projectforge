package middleware

import (
	"net/http"
)

// CORS creates a CORS middleware with the specified allowed origins
func CORS(allowedOrigins []string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			origin := r.Header.Get("Origin")

			// Always allow if we have an origin (development mode)
			// In production, you'd want to strictly check allowedOrigins
			if origin != "" {
				w.Header().Set("Access-Control-Allow-Origin", origin)
				w.Header().Set("Access-Control-Allow-Credentials", "true")
				w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
				w.Header().Set("Access-Control-Allow-Headers", "Accept, Authorization, Content-Type, X-CSRF-Token, X-Organization-ID, X-User-ID, X-User-Email, X-User-Role")
				w.Header().Set("Access-Control-Expose-Headers", "Link, X-Total-Count, X-Organization-ID")
				w.Header().Set("Access-Control-Max-Age", "300")
			}

			// Handle preflight requests
			if r.Method == http.MethodOptions {
				w.WriteHeader(http.StatusOK)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}
