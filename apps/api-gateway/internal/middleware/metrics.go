package middleware

import (
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5/middleware"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

// Metrics holds all Prometheus metrics
type Metrics struct {
	RequestsTotal   *prometheus.CounterVec
	RequestDuration *prometheus.HistogramVec
	RequestsActive  prometheus.Gauge
}

// NewMetrics creates and registers Prometheus metrics
func NewMetrics() *Metrics {
	m := &Metrics{
		RequestsTotal: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "api_gateway_requests_total",
				Help: "Total number of HTTP requests processed",
			},
			[]string{"method", "path", "status"},
		),
		RequestDuration: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "api_gateway_request_duration_seconds",
				Help:    "HTTP request latencies in seconds",
				Buckets: prometheus.DefBuckets, // 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10
			},
			[]string{"method", "path"},
		),
		RequestsActive: promauto.NewGauge(
			prometheus.GaugeOpts{
				Name: "api_gateway_requests_active",
				Help: "Number of requests currently being processed",
			},
		),
	}

	return m
}

// MetricsMiddleware returns a middleware that collects Prometheus metrics
func MetricsMiddleware(m *Metrics) func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Increment active requests
			m.RequestsActive.Inc()
			defer m.RequestsActive.Dec()

			// Start timer
			start := time.Now()

			// Wrap response writer to capture status code
			ww := middleware.NewWrapResponseWriter(w, r.ProtoMajor)

			// Process request
			next.ServeHTTP(ww, r)

			// Record metrics
			duration := time.Since(start).Seconds()
			status := strconv.Itoa(ww.Status())
			path := r.URL.Path
			method := r.Method

			// Simplify path for metrics (avoid cardinality explosion)
			// Replace UUIDs and IDs with placeholders
			simplifiedPath := simplifyPath(path)

			m.RequestsTotal.WithLabelValues(method, simplifiedPath, status).Inc()
			m.RequestDuration.WithLabelValues(method, simplifiedPath).Observe(duration)
		})
	}
}

// simplifyPath simplifies paths to avoid high cardinality in metrics
// Replaces UUIDs and numeric IDs with placeholders
func simplifyPath(path string) string {
	// For now, return the path as-is
	// In production, you'd want to replace UUIDs/IDs with {id}
	// This can be done with regex or by using the Chi route pattern

	// Example: /api/v1/projects/123e4567-e89b-12d3-a456-426614174000 -> /api/v1/projects/{id}
	// For simplicity, we'll use the full path for now
	// TODO: Implement path simplification to avoid cardinality issues

	return path
}
