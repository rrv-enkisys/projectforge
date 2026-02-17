package middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestRateLimit(t *testing.T) {
	// Create rate limiter with 2 requests per second
	rateLimiter := NewRateLimiter(2)

	// Create middleware
	rateLimitMiddleware := RateLimit(rateLimiter)

	// Create a test handler
	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	// Wrap handler with middleware
	handler := rateLimitMiddleware(testHandler)

	// Test that first 2 requests succeed
	for i := 0; i < 2; i++ {
		req := httptest.NewRequest(http.MethodGet, "/test", nil)
		rr := httptest.NewRecorder()

		handler.ServeHTTP(rr, req)

		if rr.Code != http.StatusOK {
			t.Errorf("Request %d: Expected status 200, got %d", i+1, rr.Code)
		}
	}

	// Test that 3rd request is rate limited
	req := httptest.NewRequest(http.MethodGet, "/test", nil)
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if rr.Code != http.StatusTooManyRequests {
		t.Errorf("Expected status 429, got %d", rr.Code)
	}

	// Wait for rate limiter to refill
	time.Sleep(time.Second)

	// Test that request succeeds after waiting
	req = httptest.NewRequest(http.MethodGet, "/test", nil)
	rr = httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Errorf("Expected status 200 after wait, got %d", rr.Code)
	}
}

func TestRateLimitMiddleware_HighThroughput(t *testing.T) {
	// Create rate limiter with 100 requests per second
	rateLimiter := NewRateLimiter(100)

	// Create middleware
	rateLimitMiddleware := RateLimit(rateLimiter)

	// Create a test handler
	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	// Wrap handler with middleware
	handler := rateLimitMiddleware(testHandler)

	// Test that we can make many requests quickly
	successCount := 0
	rateLimitedCount := 0

	for i := 0; i < 150; i++ {
		req := httptest.NewRequest(http.MethodGet, "/test", nil)
		rr := httptest.NewRecorder()

		handler.ServeHTTP(rr, req)

		if rr.Code == http.StatusOK {
			successCount++
		} else if rr.Code == http.StatusTooManyRequests {
			rateLimitedCount++
		}
	}

	// Should have approximately 100 successes and 50 rate limited
	if successCount < 90 || successCount > 110 {
		t.Errorf("Expected ~100 successful requests, got %d", successCount)
	}

	if rateLimitedCount < 40 || rateLimitedCount > 60 {
		t.Errorf("Expected ~50 rate limited requests, got %d", rateLimitedCount)
	}
}
