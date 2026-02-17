package middleware

import (
	"context"
	"net/http"

	"github.com/google/uuid"
)

// RequestIDKey is the context key for request ID
const RequestIDKey ContextKey = "request_id"

// RequestIDHeader is the HTTP header name for request ID
const RequestIDHeader = "X-Request-ID"

// RequestID middleware generates a unique ID for each request
func RequestID() func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Check if request ID already exists in header
			requestID := r.Header.Get(RequestIDHeader)

			// If not, generate a new one
			if requestID == "" {
				requestID = uuid.New().String()
			}

			// Add request ID to context
			ctx := context.WithValue(r.Context(), RequestIDKey, requestID)

			// Add request ID to response header
			w.Header().Set(RequestIDHeader, requestID)

			// Continue with the request
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

// GetRequestID retrieves the request ID from context
func GetRequestID(ctx context.Context) string {
	if reqID, ok := ctx.Value(RequestIDKey).(string); ok {
		return reqID
	}
	return ""
}
