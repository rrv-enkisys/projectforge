package middleware

import (
	"net/http"
	"sync"

	"github.com/projectforge/api-gateway/pkg/response"
	"golang.org/x/time/rate"
)

// RateLimiter holds rate limiters per organization
type RateLimiter struct {
	limiters map[string]*rate.Limiter
	mu       sync.RWMutex
	rps      int
}

// NewRateLimiter creates a new rate limiter
func NewRateLimiter(rps int) *RateLimiter {
	return &RateLimiter{
		limiters: make(map[string]*rate.Limiter),
		rps:      rps,
	}
}

// getLimiter gets or creates a rate limiter for a specific key (organization_id)
func (rl *RateLimiter) getLimiter(key string) *rate.Limiter {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	limiter, exists := rl.limiters[key]
	if !exists {
		// Create new limiter: rps requests per second with burst of rps*2
		limiter = rate.NewLimiter(rate.Limit(rl.rps), rl.rps*2)
		rl.limiters[key] = limiter
	}

	return limiter
}

// RateLimit creates a rate limiting middleware per organization
func RateLimit(rl *RateLimiter) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Get organization ID from context (set by Tenant middleware)
			organizationID := GetOrganizationID(r.Context())

			// If no organization ID, use IP address as fallback
			key := organizationID
			if key == "" {
				key = r.RemoteAddr
			}

			// Get limiter for this key
			limiter := rl.getLimiter(key)

			// Check if request is allowed
			if !limiter.Allow() {
				response.TooManyRequests(w, "Rate limit exceeded")
				return
			}

			// Continue with the request
			next.ServeHTTP(w, r)
		})
	}
}
