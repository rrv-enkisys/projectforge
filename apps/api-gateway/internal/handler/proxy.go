package handler

import (
	"context"
	"io"
	"log/slog"
	"net/http"
	"net/url"
	"strings"
	"time"
)

// ProxyHandler handles reverse proxy requests to backend services
type ProxyHandler struct {
	client         *http.Client
	coreServiceURL string
	aiServiceURL   string
	logger         *slog.Logger
}

// NewProxyHandler creates a new proxy handler
func NewProxyHandler(coreServiceURL, aiServiceURL string, logger *slog.Logger) *ProxyHandler {
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
	}
}

// ProxyTo creates a handler that proxies requests to the specified service
func (p *ProxyHandler) ProxyTo(serviceURL string) http.HandlerFunc {
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

		// Create new request
		proxyReq, err := http.NewRequestWithContext(r.Context(), r.Method, targetURL.String(), r.Body)
		if err != nil {
			p.logger.Error("Failed to create proxy request", "error", err)
			http.Error(w, "Internal server error", http.StatusInternalServerError)
			return
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

		// Execute the request
		resp, err := p.client.Do(proxyReq)
		if err != nil {
			if err == context.DeadlineExceeded {
				p.logger.Error("Proxy request timeout", "url", targetURL.String())
				http.Error(w, "Gateway timeout", http.StatusGatewayTimeout)
			} else {
				p.logger.Error("Proxy request failed", "url", targetURL.String(), "error", err)
				http.Error(w, "Bad gateway", http.StatusBadGateway)
			}
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
	return p.ProxyTo(p.coreServiceURL)
}

// ProxyToAI proxies requests to the AI Service
func (p *ProxyHandler) ProxyToAI() http.HandlerFunc {
	return p.ProxyTo(p.aiServiceURL)
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
