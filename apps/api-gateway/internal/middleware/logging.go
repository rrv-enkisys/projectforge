package middleware

import (
	"log/slog"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5/middleware"
)

// responseWriter wraps http.ResponseWriter to capture status code
type responseWriter struct {
	http.ResponseWriter
	statusCode int
	written    bool
}

func (rw *responseWriter) WriteHeader(statusCode int) {
	if !rw.written {
		rw.statusCode = statusCode
		rw.written = true
		rw.ResponseWriter.WriteHeader(statusCode)
	}
}

func (rw *responseWriter) Write(b []byte) (int, error) {
	if !rw.written {
		rw.WriteHeader(http.StatusOK)
	}
	return rw.ResponseWriter.Write(b)
}

// StructuredLogger creates a structured logging middleware
func StructuredLogger(logger *slog.Logger) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()

			// Get request ID from context (set by chi's RequestID middleware)
			requestID := middleware.GetReqID(r.Context())

			// Wrap response writer to capture status code
			wrapped := &responseWriter{
				ResponseWriter: w,
				statusCode:     http.StatusOK,
				written:        false,
			}

			// Process request
			next.ServeHTTP(wrapped, r)

			// Calculate duration
			duration := time.Since(start)

			// Get user context if available
			userUID := GetUserUID(r.Context())
			organizationID := GetOrganizationID(r.Context())

			// Log request
			attrs := []slog.Attr{
				slog.String("request_id", requestID),
				slog.String("method", r.Method),
				slog.String("path", r.URL.Path),
				slog.String("remote_addr", r.RemoteAddr),
				slog.Int("status", wrapped.statusCode),
				slog.Duration("duration", duration),
				slog.String("user_agent", r.UserAgent()),
			}

			if userUID != "" {
				attrs = append(attrs, slog.String("user_uid", userUID))
			}
			if organizationID != "" {
				attrs = append(attrs, slog.String("organization_id", organizationID))
			}

			// Log at appropriate level based on status code
			if wrapped.statusCode >= 500 {
				logger.LogAttrs(r.Context(), slog.LevelError, "HTTP request", attrs...)
			} else if wrapped.statusCode >= 400 {
				logger.LogAttrs(r.Context(), slog.LevelWarn, "HTTP request", attrs...)
			} else {
				logger.LogAttrs(r.Context(), slog.LevelInfo, "HTTP request", attrs...)
			}
		})
	}
}
