package handler

import (
	"log/slog"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
	"time"
)

func TestProxyHandler_Success(t *testing.T) {
	// Create a mock backend server
	backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Verify headers were forwarded
		if r.Header.Get("X-Forwarded-For") == "" {
			t.Error("Expected X-Forwarded-For header")
		}

		w.WriteHeader(http.StatusOK)
		w.Write([]byte("backend response"))
	}))
	defer backend.Close()

	// Create logger
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))

	// Create proxy handler
	proxyHandler := NewProxyHandler(backend.URL, backend.URL, backend.URL, logger)

	// Create test request
	req := httptest.NewRequest(http.MethodGet, "/api/v1/projects", nil)
	rr := httptest.NewRecorder()

	// Execute request
	handler := proxyHandler.ProxyToCore()
	handler.ServeHTTP(rr, req)

	// Check response
	if rr.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", rr.Code)
	}

	if rr.Body.String() != "backend response" {
		t.Errorf("Expected 'backend response', got '%s'", rr.Body.String())
	}
}

func TestProxyHandler_BackendError(t *testing.T) {
	// Create a mock backend server that returns an error
	backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte("backend error"))
	}))
	defer backend.Close()

	// Create logger
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))

	// Create proxy handler
	proxyHandler := NewProxyHandler(backend.URL, backend.URL, backend.URL, logger)

	// Create test request
	req := httptest.NewRequest(http.MethodGet, "/api/v1/projects", nil)
	rr := httptest.NewRecorder()

	// Execute request (with retries, should eventually return 500)
	handler := proxyHandler.ProxyToCore()
	handler.ServeHTTP(rr, req)

	// Circuit breaker might handle this differently, but we expect some error response
	if rr.Code < 500 {
		t.Errorf("Expected status 5xx, got %d", rr.Code)
	}
}

func TestProxyHandler_HeaderForwarding(t *testing.T) {
	// Create a mock backend server
	backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Check that custom headers are forwarded
		if r.Header.Get("X-Organization-ID") != "org-123" {
			t.Errorf("Expected X-Organization-ID header to be forwarded")
		}

		if r.Header.Get("X-User-ID") != "user-456" {
			t.Errorf("Expected X-User-ID header to be forwarded")
		}

		w.WriteHeader(http.StatusOK)
	}))
	defer backend.Close()

	// Create logger
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))

	// Create proxy handler
	proxyHandler := NewProxyHandler(backend.URL, backend.URL, backend.URL, logger)

	// Create test request with custom headers
	req := httptest.NewRequest(http.MethodGet, "/api/v1/projects", nil)
	req.Header.Set("X-Organization-ID", "org-123")
	req.Header.Set("X-User-ID", "user-456")
	rr := httptest.NewRecorder()

	// Execute request
	handler := proxyHandler.ProxyToCore()
	handler.ServeHTTP(rr, req)

	// Check response
	if rr.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", rr.Code)
	}
}

func TestProxyHandler_Timeout(t *testing.T) {
	// Create a mock backend server that is slow
	backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(35 * time.Second) // Longer than client timeout
		w.WriteHeader(http.StatusOK)
	}))
	defer backend.Close()

	// Create logger
	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))

	// Create proxy handler
	proxyHandler := NewProxyHandler(backend.URL, backend.URL, backend.URL, logger)

	// Create test request
	req := httptest.NewRequest(http.MethodGet, "/api/v1/projects", nil)
	rr := httptest.NewRecorder()

	// Execute request (should timeout)
	handler := proxyHandler.ProxyToCore()
	handler.ServeHTTP(rr, req)

	// Should get timeout or gateway timeout
	if rr.Code != http.StatusGatewayTimeout && rr.Code != http.StatusBadGateway && rr.Code != http.StatusServiceUnavailable {
		t.Errorf("Expected timeout error (504, 502, or 503), got %d", rr.Code)
	}
}
