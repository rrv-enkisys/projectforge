package handler

import (
	"encoding/json"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/projectforge/notification-service/internal/model"
	"github.com/projectforge/notification-service/internal/service"
	"github.com/projectforge/notification-service/pkg/respond"
)

// NotificationHandler handles notification API endpoints.
type NotificationHandler struct {
	notifSvc *service.NotificationService
	inAppSvc *service.InAppService
}

// NewNotificationHandler creates a new NotificationHandler.
func NewNotificationHandler(notifSvc *service.NotificationService, inAppSvc *service.InAppService) *NotificationHandler {
	return &NotificationHandler{
		notifSvc: notifSvc,
		inAppSvc: inAppSvc,
	}
}

// SendEvent handles POST /notifications/events
// Dispatches a notification event to all specified channels.
func (h *NotificationHandler) SendEvent(w http.ResponseWriter, r *http.Request) {
	var req model.SendEventRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respond.BadRequest(w, "invalid request body: "+err.Error())
		return
	}

	if req.EventType == "" {
		respond.BadRequest(w, "event_type is required")
		return
	}
	if req.OrganizationID == "" {
		respond.BadRequest(w, "organization_id is required")
		return
	}
	if len(req.Channels) == 0 {
		respond.BadRequest(w, "at least one channel is required")
		return
	}

	result := h.notifSvc.Send(r.Context(), &req)
	respond.JSON(w, http.StatusOK, result)
}

// ListInApp handles GET /notifications/in-app
// Lists in-app notifications for a user.
func (h *NotificationHandler) ListInApp(w http.ResponseWriter, r *http.Request) {
	orgID := r.Header.Get("X-Organization-ID")
	userID := r.Header.Get("X-User-ID")

	if orgID == "" || userID == "" {
		respond.BadRequest(w, "X-Organization-ID and X-User-ID headers are required")
		return
	}

	unreadOnly := r.URL.Query().Get("unread_only") == "true"
	limit := 50 // Default limit

	notifications := h.inAppSvc.List(orgID, userID, unreadOnly, limit)
	unreadCount := h.inAppSvc.UnreadCount(orgID, userID)

	respond.JSON(w, http.StatusOK, map[string]any{
		"data":         notifications,
		"unread_count": unreadCount,
		"total":        len(notifications),
	})
}

// MarkAsRead handles PATCH /notifications/in-app/{id}/read
// Marks a specific notification as read.
func (h *NotificationHandler) MarkAsRead(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	orgID := r.Header.Get("X-Organization-ID")
	userID := r.Header.Get("X-User-ID")

	if orgID == "" || userID == "" {
		respond.BadRequest(w, "X-Organization-ID and X-User-ID headers are required")
		return
	}

	if err := h.inAppSvc.MarkAsRead(id, orgID, userID); err != nil {
		respond.NotFound(w, "notification")
		return
	}
	respond.JSON(w, http.StatusOK, map[string]bool{"success": true})
}

// MarkAllAsRead handles PATCH /notifications/in-app/read-all
// Marks all notifications as read for a user.
func (h *NotificationHandler) MarkAllAsRead(w http.ResponseWriter, r *http.Request) {
	orgID := r.Header.Get("X-Organization-ID")
	userID := r.Header.Get("X-User-ID")

	if orgID == "" || userID == "" {
		respond.BadRequest(w, "X-Organization-ID and X-User-ID headers are required")
		return
	}

	count := h.inAppSvc.MarkAllAsRead(orgID, userID)
	respond.JSON(w, http.StatusOK, map[string]int{"marked_read": count})
}

// DeleteInApp handles DELETE /notifications/in-app/{id}
// Deletes an in-app notification.
func (h *NotificationHandler) DeleteInApp(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	orgID := r.Header.Get("X-Organization-ID")
	userID := r.Header.Get("X-User-ID")

	if orgID == "" || userID == "" {
		respond.BadRequest(w, "X-Organization-ID and X-User-ID headers are required")
		return
	}

	if err := h.inAppSvc.Delete(id, orgID, userID); err != nil {
		respond.NotFound(w, "notification")
		return
	}
	respond.NoContent(w)
}

// UnreadCount handles GET /notifications/in-app/unread-count
func (h *NotificationHandler) UnreadCount(w http.ResponseWriter, r *http.Request) {
	orgID := r.Header.Get("X-Organization-ID")
	userID := r.Header.Get("X-User-ID")

	if orgID == "" || userID == "" {
		respond.BadRequest(w, "X-Organization-ID and X-User-ID headers are required")
		return
	}

	count := h.inAppSvc.UnreadCount(orgID, userID)
	respond.JSON(w, http.StatusOK, map[string]int{"unread_count": count})
}
