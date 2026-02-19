package service

import (
	"fmt"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/projectforge/notification-service/internal/model"
)

// InAppStore is an in-memory store for in-app notifications.
// In production, this would be backed by PostgreSQL or Firestore.
type InAppStore struct {
	mu            sync.RWMutex
	notifications map[string]*model.Notification // id -> notification
}

func newInAppStore() *InAppStore {
	return &InAppStore{
		notifications: make(map[string]*model.Notification),
	}
}

// InAppService manages in-app notifications.
type InAppService struct {
	store *InAppStore
}

// NewInAppService creates a new InAppService.
func NewInAppService() *InAppService {
	return &InAppService{
		store: newInAppStore(),
	}
}

// Create stores a new in-app notification for each recipient.
func (s *InAppService) Create(event *model.NotificationEvent) []*model.Notification {
	created := make([]*model.Notification, 0, len(event.RecipientIDs))

	for _, userID := range event.RecipientIDs {
		n := &model.Notification{
			ID:             uuid.New().String(),
			OrganizationID: event.OrganizationID,
			UserID:         userID,
			EventType:      event.EventType,
			Title:          event.Subject,
			Body:           event.Body,
			ProjectID:      event.ProjectID,
			ActorID:        event.ActorID,
			ActorName:      event.ActorName,
			Metadata:       event.Metadata,
			Status:         model.StatusPending,
			CreatedAt:      time.Now().UTC(),
		}

		s.store.mu.Lock()
		s.store.notifications[n.ID] = n
		s.store.mu.Unlock()

		created = append(created, n)
	}

	return created
}

// List returns notifications for a user within an organization.
func (s *InAppService) List(orgID, userID string, unreadOnly bool, limit int) []*model.Notification {
	s.store.mu.RLock()
	defer s.store.mu.RUnlock()

	result := make([]*model.Notification, 0)
	for _, n := range s.store.notifications {
		if n.OrganizationID != orgID || n.UserID != userID {
			continue
		}
		if unreadOnly && n.Status == model.StatusRead {
			continue
		}
		result = append(result, n)
	}

	// Sort by created_at descending (newest first)
	sortNotificationsByDate(result)

	if limit > 0 && len(result) > limit {
		result = result[:limit]
	}
	return result
}

// MarkAsRead marks a notification as read.
func (s *InAppService) MarkAsRead(id, orgID, userID string) error {
	s.store.mu.Lock()
	defer s.store.mu.Unlock()

	n, ok := s.store.notifications[id]
	if !ok || n.OrganizationID != orgID || n.UserID != userID {
		return fmt.Errorf("notification not found")
	}

	now := time.Now().UTC()
	n.Status = model.StatusRead
	n.ReadAt = &now
	return nil
}

// MarkAllAsRead marks all notifications as read for a user.
func (s *InAppService) MarkAllAsRead(orgID, userID string) int {
	s.store.mu.Lock()
	defer s.store.mu.Unlock()

	count := 0
	now := time.Now().UTC()
	for _, n := range s.store.notifications {
		if n.OrganizationID == orgID && n.UserID == userID && n.Status != model.StatusRead {
			n.Status = model.StatusRead
			n.ReadAt = &now
			count++
		}
	}
	return count
}

// Delete deletes a notification.
func (s *InAppService) Delete(id, orgID, userID string) error {
	s.store.mu.Lock()
	defer s.store.mu.Unlock()

	n, ok := s.store.notifications[id]
	if !ok || n.OrganizationID != orgID || n.UserID != userID {
		return fmt.Errorf("notification not found")
	}
	delete(s.store.notifications, id)
	return nil
}

// UnreadCount returns the number of unread notifications for a user.
func (s *InAppService) UnreadCount(orgID, userID string) int {
	s.store.mu.RLock()
	defer s.store.mu.RUnlock()

	count := 0
	for _, n := range s.store.notifications {
		if n.OrganizationID == orgID && n.UserID == userID && n.Status != model.StatusRead {
			count++
		}
	}
	return count
}

// sortNotificationsByDate sorts notifications by created_at descending.
func sortNotificationsByDate(ns []*model.Notification) {
	// Simple insertion sort (adequate for small lists in dev mode)
	for i := 1; i < len(ns); i++ {
		for j := i; j > 0 && ns[j].CreatedAt.After(ns[j-1].CreatedAt); j-- {
			ns[j], ns[j-1] = ns[j-1], ns[j]
		}
	}
}
