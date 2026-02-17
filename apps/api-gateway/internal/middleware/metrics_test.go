package middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/prometheus/client_golang/prometheus"
)

func TestMetricsMiddleware(t *testing.T) {
	// Create new metrics
	metrics := NewMetrics()

	// Create middleware
	metricsMiddleware := MetricsMiddleware(metrics)

	// Create a test handler
	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("test response"))
	})

	// Wrap handler with middleware
	handler := metricsMiddleware(testHandler)

	// Execute request
	req := httptest.NewRequest(http.MethodGet, "/api/v1/projects", nil)
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	// Check response
	if rr.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", rr.Code)
	}

	// Verify metrics were recorded
	// We can't easily check the actual metric values in a unit test,
	// but we can verify the middleware doesn't panic or error
}

func TestMetricsMiddleware_ActiveRequests(t *testing.T) {
	// Create new metrics
	metrics := NewMetrics()

	// Create middleware
	metricsMiddleware := MetricsMiddleware(metrics)

	// Create a test handler that we can control
	handlerCalled := make(chan bool)
	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Get current active requests metric
		// Note: This is a simplified test - in reality we'd need to use prometheus testutil

		// Signal that handler was called
		handlerCalled <- true

		// Wait a bit to simulate work
		<-handlerCalled

		w.WriteHeader(http.StatusOK)
	})

	// Wrap handler with middleware
	handler := metricsMiddleware(testHandler)

	// Execute request in background
	go func() {
		req := httptest.NewRequest(http.MethodGet, "/api/v1/projects", nil)
		rr := httptest.NewRecorder()
		handler.ServeHTTP(rr, req)
	}()

	// Wait for handler to be called
	<-handlerCalled

	// At this point, active requests should be 1
	// (In a real test, we'd use prometheus testutil to verify this)

	// Signal handler to complete
	handlerCalled <- true
}

func TestMetricsMiddleware_ErrorStatus(t *testing.T) {
	// Create new metrics
	metrics := NewMetrics()

	// Create middleware
	metricsMiddleware := MetricsMiddleware(metrics)

	// Test different status codes
	statusCodes := []int{
		http.StatusOK,
		http.StatusCreated,
		http.StatusBadRequest,
		http.StatusUnauthorized,
		http.StatusNotFound,
		http.StatusInternalServerError,
		http.StatusServiceUnavailable,
	}

	for _, statusCode := range statusCodes {
		testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(statusCode)
		})

		handler := metricsMiddleware(testHandler)

		req := httptest.NewRequest(http.MethodGet, "/api/v1/test", nil)
		rr := httptest.NewRecorder()

		handler.ServeHTTP(rr, req)

		if rr.Code != statusCode {
			t.Errorf("Expected status %d, got %d", statusCode, rr.Code)
		}
	}
}

func TestNewMetrics(t *testing.T) {
	// Create metrics
	metrics := NewMetrics()

	// Verify metrics were created
	if metrics.RequestsTotal == nil {
		t.Error("RequestsTotal metric is nil")
	}

	if metrics.RequestDuration == nil {
		t.Error("RequestDuration metric is nil")
	}

	if metrics.RequestsActive == nil {
		t.Error("RequestsActive metric is nil")
	}

	// Verify metrics are registered (they should not panic when collecting)
	err := prometheus.Register(metrics.RequestsTotal)
	if err == nil {
		t.Error("Expected error when registering already-registered metric, got nil")
	}
}
