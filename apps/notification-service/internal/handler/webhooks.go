package handler

import (
	"encoding/json"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/projectforge/notification-service/internal/model"
	"github.com/projectforge/notification-service/internal/service"
	"github.com/projectforge/notification-service/pkg/respond"
)

// WebhookHandler handles webhook subscription management endpoints.
type WebhookHandler struct {
	webhookSvc *service.WebhookService
}

// NewWebhookHandler creates a new WebhookHandler.
func NewWebhookHandler(webhookSvc *service.WebhookService) *WebhookHandler {
	return &WebhookHandler{webhookSvc: webhookSvc}
}

// Create handles POST /webhooks
func (h *WebhookHandler) Create(w http.ResponseWriter, r *http.Request) {
	orgID := r.Header.Get("X-Organization-ID")
	if orgID == "" {
		respond.BadRequest(w, "X-Organization-ID header is required")
		return
	}

	var req model.CreateWebhookRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respond.BadRequest(w, "invalid request body: "+err.Error())
		return
	}

	sub, err := h.webhookSvc.CreateSubscription(orgID, &req)
	if err != nil {
		respond.BadRequest(w, err.Error())
		return
	}
	respond.JSON(w, http.StatusCreated, sub)
}

// List handles GET /webhooks
func (h *WebhookHandler) List(w http.ResponseWriter, r *http.Request) {
	orgID := r.Header.Get("X-Organization-ID")
	if orgID == "" {
		respond.BadRequest(w, "X-Organization-ID header is required")
		return
	}

	subs := h.webhookSvc.ListSubscriptions(orgID)
	respond.JSON(w, http.StatusOK, map[string]any{
		"data":  subs,
		"total": len(subs),
	})
}

// Get handles GET /webhooks/{id}
func (h *WebhookHandler) Get(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	orgID := r.Header.Get("X-Organization-ID")
	if orgID == "" {
		respond.BadRequest(w, "X-Organization-ID header is required")
		return
	}

	sub, err := h.webhookSvc.GetSubscription(id, orgID)
	if err != nil {
		respond.NotFound(w, "webhook subscription")
		return
	}
	// Mask secret in response
	copy := *sub
	copy.Secret = ""
	respond.JSON(w, http.StatusOK, &copy)
}

// Update handles PATCH /webhooks/{id}
func (h *WebhookHandler) Update(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	orgID := r.Header.Get("X-Organization-ID")
	if orgID == "" {
		respond.BadRequest(w, "X-Organization-ID header is required")
		return
	}

	var req model.UpdateWebhookRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respond.BadRequest(w, "invalid request body: "+err.Error())
		return
	}

	sub, err := h.webhookSvc.UpdateSubscription(id, orgID, &req)
	if err != nil {
		respond.NotFound(w, "webhook subscription")
		return
	}
	respond.JSON(w, http.StatusOK, sub)
}

// Delete handles DELETE /webhooks/{id}
func (h *WebhookHandler) Delete(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	orgID := r.Header.Get("X-Organization-ID")
	if orgID == "" {
		respond.BadRequest(w, "X-Organization-ID header is required")
		return
	}

	if err := h.webhookSvc.DeleteSubscription(id, orgID); err != nil {
		respond.NotFound(w, "webhook subscription")
		return
	}
	respond.NoContent(w)
}

// ListDeliveries handles GET /webhooks/{id}/deliveries
func (h *WebhookHandler) ListDeliveries(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	orgID := r.Header.Get("X-Organization-ID")
	if orgID == "" {
		respond.BadRequest(w, "X-Organization-ID header is required")
		return
	}

	deliveries := h.webhookSvc.ListDeliveries(id, orgID)
	respond.JSON(w, http.StatusOK, map[string]any{
		"data":  deliveries,
		"total": len(deliveries),
	})
}
