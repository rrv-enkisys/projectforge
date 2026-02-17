package handler

import (
	"context"
	"fmt"
	"io"
	"log/slog"
	"math"
	"net/http"
	"net/url"
	"strings"
	"time"

	"github.com/sony/gobreaker"
)

// ProxyHandler handles reverse proxy requests to backend services
type ProxyHandler struct {
	client           *http.Client
	coreServiceURL   string
	aiServiceURL     string
	logger           *slog.Logger
	coreServiceCB    *gobreaker.CircuitBreaker
	aiServiceCB      *gobreaker.CircuitBreaker
	maxRetries       int
	retryBaseDelay   time.Duration
}

// NewProxyHandler creates a new proxy handler
func NewProxyHandler(coreServiceURL, aiServiceURL string, logger *slog.Logger) *ProxyHandler {
	// Circuit breaker settings
	cbSettings := gobreaker.Settings{
		Name:        "backend-service",
		MaxRequests: 5,    // Max requests allowed when half-open
		Interval:    60 * time.Second,  // When to flush counters in closed state
		Timeout:     30 * time.Second,  // How long to stay in open state before trying half-open
		ReadyToTrip: func(counts gobreaker.Counts) bool {
			failureRatio := float64(counts.TotalFailures) / float64(counts.Requests)
			return counts.Requests >= 10 && failureRatio >= 0.5 // 50% failure rate
		},
		OnStateChange: func(name string, from gobreaker.State, to gobreaker.State) {
			logger.Warn("Circuit breaker state changed",
				"service", name,
				"from", from.String(),
				"to", to.String())
		},
	}

	// Create separate circuit breakers for each service
	coreServiceCBSettings := cbSettings
	coreServiceCBSettings.Name = "core-service"

	aiServiceCBSettings := cbSettings
	aiServiceCBSettings.Name = "ai-service"

	return &ProxyHandler{
		client: &http.Client{
			Timeout: 30 * time.Second,
			CheckRedirect: func(req *http.Request, via []*http.Request) error {
				return http.ErrUseLastResponse // Don't follow redirects
			},
		},
		coreServiceURL: strings.TrimSuffix(coreServiceURL, "/"),
		aiServiceURL:   strings.TrimSuffix(aiServiceURL, "/"),
		logger:         logger,
		coreServiceCB:  gobreaker.NewCircuitBreaker(coreServiceCBSettings),
		aiServiceCB:    gobreaker.NewCircuitBreaker(aiServiceCBSettings),
		maxRetries:     3,
		retryBaseDelay: 100 * time.Millisecond,
	}
}

// executeWithRetry executes an HTTP request with exponential backoff retry logic
func (p *ProxyHandler) executeWithRetry(ctx context.Context, req *http.Request) (*http.Response, error) {
	var resp *http.Response
	var err error

	for attempt := 0; attempt <= p.maxRetries; attempt++ {
		// Clone request for retry
		reqClone := req.Clone(ctx)

		resp, err = p.client.Do(reqClone)

		// If successful or non-retryable error, return immediately
		if err == nil {
			// Don't retry on client errors (4xx)
			if resp.StatusCode < 500 {
				return resp, nil
			}

			// Close response body if we're going to retry
			if attempt < p.maxRetries {
				resp.Body.Close()
			} else {
				return resp, nil // Last attempt, return as-is
			}
		}

		// Calculate backoff delay with exponential backoff
		if attempt < p.maxRetries {
			backoff := time.Duration(math.Pow(2, float64(attempt))) * p.retryBaseDelay
			p.logger.Debug("Retrying request after backoff",
				"attempt", attempt+1,
				"max_retries", p.maxRetries,
				"backoff", backoff,
				"error", err)

			select {
			case <-time.After(backoff):
				continue
			case <-ctx.Done():
				return nil, ctx.Err()
			}
		}
	}

	return resp, err
}

// ProxyTo creates a handler that proxies requests to the specified service with circuit breaker
func (p *ProxyHandler) ProxyTo(serviceURL string, cb *gobreaker.CircuitBreaker) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Build target URL
		targetURL, err := url.Parse(serviceURL)
		if err != nil {
			p.logger.Error("Failed to parse service URL", "url", serviceURL, "error", err)
			http.Error(w, "Internal server error", http.StatusInternalServerError)
			return
		}

		// Preserve the original request path
		targetURL.Path = r.URL.Path
		targetURL.RawQuery = r.URL.RawQuery

		// Execute request through circuit breaker
		result, err := cb.Execute(func() (interface{}, error) {
			// Create new request
			proxyReq, err := http.NewRequestWithContext(r.Context(), r.Method, targetURL.String(), r.Body)
			if err != nil {
				return nil, fmt.Errorf("failed to create proxy request: %w", err)
			}

			// Copy headers from original request
			for key, values := range r.Header {
				for _, value := range values {
					proxyReq.Header.Add(key, value)
				}
			}

			// Set X-Forwarded headers
			proxyReq.Header.Set("X-Forwarded-For", r.RemoteAddr)
			proxyReq.Header.Set("X-Forwarded-Proto", getScheme(r))
			proxyReq.Header.Set("X-Forwarded-Host", r.Host)

			// Execute the request with retry logic
			resp, err := p.executeWithRetry(r.Context(), proxyReq)
			if err != nil {
				return nil, fmt.Errorf("proxy request failed: %w", err)
			}

			return resp, nil
		})

		// Handle circuit breaker errors
		if err != nil {
			p.logger.Error("Circuit breaker rejected request or request failed",
				"url", targetURL.String(),
				"error", err,
				"cb_state", cb.State().String())

			// Check if circuit is open
			if err == gobreaker.ErrOpenState {
				http.Error(w, "Service temporarily unavailable", http.StatusServiceUnavailable)
				return
			}

			// Check for timeout
			if err == context.DeadlineExceeded {
				http.Error(w, "Gateway timeout", http.StatusGatewayTimeout)
				return
			}

			// Generic error
			http.Error(w, "Bad gateway", http.StatusBadGateway)
			return
		}

		// Type assert the response
		resp, ok := result.(*http.Response)
		if !ok {
			p.logger.Error("Invalid response type from circuit breaker")
			http.Error(w, "Internal server error", http.StatusInternalServerError)
			return
		}
		defer resp.Body.Close()

		// Copy response headers
		for key, values := range resp.Header {
			for _, value := range values {
				w.Header().Add(key, value)
			}
		}

		// Write status code
		w.WriteHeader(resp.StatusCode)

		// Copy response body
		_, err = io.Copy(w, resp.Body)
		if err != nil {
			p.logger.Error("Failed to copy response body", "error", err)
		}
	}
}

// ProxyToCore proxies requests to the Core Service
func (p *ProxyHandler) ProxyToCore() http.HandlerFunc {
	return p.ProxyTo(p.coreServiceURL, p.coreServiceCB)
}

// ProxyToAI proxies requests to the AI Service
func (p *ProxyHandler) ProxyToAI() http.HandlerFunc {
	return p.ProxyTo(p.aiServiceURL, p.aiServiceCB)
}

// getScheme determines the request scheme (http or https)
func getScheme(r *http.Request) string {
	if r.TLS != nil {
		return "https"
	}
	if scheme := r.Header.Get("X-Forwarded-Proto"); scheme != "" {
		return scheme
	}
	return "http"
}
