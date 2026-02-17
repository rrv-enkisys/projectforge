package middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestCORSMiddleware(t *testing.T) {
	// Create CORS middleware with allowed origins
	allowedOrigins := []string{"https://example.com", "https://app.example.com"}
	corsMiddleware := CORS(allowedOrigins)

	// Create a test handler
	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	// Wrap handler with middleware
	handler := corsMiddleware(testHandler)

	tests := []struct {
		name           string
		origin         string
		method         string
		expectedStatus int
		expectCORS     bool
	}{
		{
			name:           "Allowed origin",
			origin:         "https://example.com",
			method:         http.MethodGet,
			expectedStatus: http.StatusOK,
			expectCORS:     true,
		},
		{
			name:           "Another allowed origin",
			origin:         "https://app.example.com",
			method:         http.MethodGet,
			expectedStatus: http.StatusOK,
			expectCORS:     true,
		},
		{
			name:           "Disallowed origin",
			origin:         "https://evil.com",
			method:         http.MethodGet,
			expectedStatus: http.StatusOK,
			expectCORS:     false,
		},
		{
			name:           "OPTIONS preflight",
			origin:         "https://example.com",
			method:         http.MethodOptions,
			expectedStatus: http.StatusNoContent,
			expectCORS:     true,
		},
		{
			name:           "No origin header",
			origin:         "",
			method:         http.MethodGet,
			expectedStatus: http.StatusOK,
			expectCORS:     false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req := httptest.NewRequest(tt.method, "/test", nil)
			if tt.origin != "" {
				req.Header.Set("Origin", tt.origin)
			}
			rr := httptest.NewRecorder()

			handler.ServeHTTP(rr, req)

			// Check status code
			if rr.Code != tt.expectedStatus {
				t.Errorf("Expected status %d, got %d", tt.expectedStatus, rr.Code)
			}

			// Check CORS headers
			if tt.expectCORS {
				allowOrigin := rr.Header().Get("Access-Control-Allow-Origin")
				if allowOrigin != tt.origin {
					t.Errorf("Expected Access-Control-Allow-Origin '%s', got '%s'", tt.origin, allowOrigin)
				}

				allowMethods := rr.Header().Get("Access-Control-Allow-Methods")
				if allowMethods == "" {
					t.Error("Expected Access-Control-Allow-Methods header, got empty")
				}
			} else {
				allowOrigin := rr.Header().Get("Access-Control-Allow-Origin")
				if allowOrigin != "" && tt.origin != "" {
					t.Errorf("Expected no Access-Control-Allow-Origin for disallowed origin, got '%s'", allowOrigin)
				}
			}
		})
	}
}

func TestCORSMiddleware_Wildcard(t *testing.T) {
	// Create CORS middleware with wildcard
	allowedOrigins := []string{"*"}
	corsMiddleware := CORS(allowedOrigins)

	// Create a test handler
	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	// Wrap handler with middleware
	handler := corsMiddleware(testHandler)

	// Test that any origin is allowed
	origins := []string{
		"https://example.com",
		"https://evil.com",
		"http://localhost:3000",
	}

	for _, origin := range origins {
		req := httptest.NewRequest(http.MethodGet, "/test", nil)
		req.Header.Set("Origin", origin)
		rr := httptest.NewRecorder()

		handler.ServeHTTP(rr, req)

		allowOrigin := rr.Header().Get("Access-Control-Allow-Origin")
		if allowOrigin != "*" {
			t.Errorf("Expected Access-Control-Allow-Origin '*', got '%s' for origin '%s'", allowOrigin, origin)
		}
	}
}
