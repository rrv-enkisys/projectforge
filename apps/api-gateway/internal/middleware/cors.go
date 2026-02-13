package middleware

import (
	"net/http"

	"github.com/go-chi/cors"
)

// CORS creates a CORS middleware with the specified allowed origins
func CORS(allowedOrigins []string) func(http.Handler) http.Handler {
	return cors.Handler(cors.Options{
		AllowedOrigins: allowedOrigins,
		AllowedMethods: []string{
			http.MethodGet,
			http.MethodPost,
			http.MethodPut,
			http.MethodPatch,
			http.MethodDelete,
			http.MethodOptions,
		},
		AllowedHeaders: []string{
			"Accept",
			"Authorization",
			"Content-Type",
			"X-CSRF-Token",
			"X-Organization-ID",
			"X-User-ID",
			"X-User-Email",
			"X-User-Role",
		},
		ExposedHeaders: []string{
			"Link",
			"X-Total-Count",
			"X-Organization-ID",
		},
		AllowCredentials: true,
		MaxAge:           300, // Maximum value not ignored by any of major browsers
	})
}
