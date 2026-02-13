package handler

import (
	"net/http"
	"time"

	"github.com/projectforge/api-gateway/pkg/response"
)

// HealthHandler handles health check requests
type HealthHandler struct {
	startTime time.Time
}

// NewHealthHandler creates a new health handler
func NewHealthHandler() *HealthHandler {
	return &HealthHandler{
		startTime: time.Now(),
	}
}

// HealthResponse represents the health check response
type HealthResponse struct {
	Status  string        `json:"status"`
	Service string        `json:"service"`
	Uptime  time.Duration `json:"uptime_seconds"`
	Time    time.Time     `json:"time"`
}

// Check handles GET /health
func (h *HealthHandler) Check(w http.ResponseWriter, r *http.Request) {
	uptime := time.Since(h.startTime)

	healthResp := HealthResponse{
		Status:  "healthy",
		Service: "api-gateway",
		Uptime:  uptime,
		Time:    time.Now(),
	}

	response.JSON(w, http.StatusOK, healthResp)
}
