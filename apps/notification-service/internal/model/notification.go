package model

import (
	"time"

	"github.com/google/uuid"
)

// EventType represents the type of notification event.
type EventType string

const (
	EventTaskCreated       EventType = "task.created"
	EventTaskUpdated       EventType = "task.updated"
	EventTaskAssigned      EventType = "task.assigned"
	EventTaskCompleted     EventType = "task.completed"
	EventMilestoneCreated  EventType = "milestone.created"
	EventMilestoneReached  EventType = "milestone.reached"
	EventProjectCreated    EventType = "project.created"
	EventProjectCompleted  EventType = "project.completed"
	EventDocumentUploaded  EventType = "document.uploaded"
	EventMentionReceived   EventType = "mention.received"
)

// Channel represents a notification delivery channel.
type Channel string

const (
	ChannelEmail  Channel = "email"
	ChannelSlack  Channel = "slack"
	ChannelWebhook Channel = "webhook"
	ChannelInApp  Channel = "in_app"
)

// NotificationStatus represents the delivery status.
type NotificationStatus string

const (
	StatusPending   NotificationStatus = "pending"
	StatusSent      NotificationStatus = "sent"
	StatusFailed    NotificationStatus = "failed"
	StatusRead      NotificationStatus = "read"
)

// NotificationEvent is the payload sent when an event occurs.
type NotificationEvent struct {
	ID             string         `json:"id"`
	EventType      EventType      `json:"event_type"`
	OrganizationID string         `json:"organization_id"`
	ProjectID      string         `json:"project_id,omitempty"`
	ActorID        string         `json:"actor_id"`        // User who triggered the event
	ActorName      string         `json:"actor_name"`
	RecipientIDs   []string       `json:"recipient_ids"`   // Users to notify
	RecipientEmail string         `json:"recipient_email,omitempty"`
	Subject        string         `json:"subject"`
	Body           string         `json:"body"`
	Metadata       map[string]any `json:"metadata,omitempty"`
	Channels       []Channel      `json:"channels"`
	CreatedAt      time.Time      `json:"created_at"`
}

// Notification represents a stored in-app notification.
type Notification struct {
	ID             string             `json:"id"`
	OrganizationID string             `json:"organization_id"`
	UserID         string             `json:"user_id"`
	EventType      EventType          `json:"event_type"`
	Title          string             `json:"title"`
	Body           string             `json:"body"`
	ProjectID      string             `json:"project_id,omitempty"`
	ActorID        string             `json:"actor_id,omitempty"`
	ActorName      string             `json:"actor_name,omitempty"`
	Metadata       map[string]any     `json:"metadata,omitempty"`
	Status         NotificationStatus `json:"status"`
	CreatedAt      time.Time          `json:"created_at"`
	ReadAt         *time.Time         `json:"read_at,omitempty"`
}

// NewNotification creates a new in-app notification.
func NewNotification(orgID, userID string, event *NotificationEvent) *Notification {
	return &Notification{
		ID:             uuid.New().String(),
		OrganizationID: orgID,
		UserID:         userID,
		EventType:      event.EventType,
		Title:          event.Subject,
		Body:           event.Body,
		ProjectID:      event.ProjectID,
		ActorID:        event.ActorID,
		ActorName:      event.ActorName,
		Metadata:       event.Metadata,
		Status:         StatusPending,
		CreatedAt:      time.Now().UTC(),
	}
}

// SendEventRequest is the API request body for sending a notification event.
type SendEventRequest struct {
	EventType      EventType      `json:"event_type"`
	OrganizationID string         `json:"organization_id"`
	ProjectID      string         `json:"project_id,omitempty"`
	ActorID        string         `json:"actor_id"`
	ActorName      string         `json:"actor_name"`
	RecipientIDs   []string       `json:"recipient_ids"`
	RecipientEmail string         `json:"recipient_email,omitempty"`
	Subject        string         `json:"subject"`
	Body           string         `json:"body"`
	Metadata       map[string]any `json:"metadata,omitempty"`
	Channels       []Channel      `json:"channels"`
}

// DeliveryResult tracks delivery for a single channel.
type DeliveryResult struct {
	Channel Channel `json:"channel"`
	Success bool    `json:"success"`
	Error   string  `json:"error,omitempty"`
}

// SendEventResponse is the API response after sending a notification.
type SendEventResponse struct {
	EventID  string           `json:"event_id"`
	Results  []DeliveryResult `json:"results"`
	AllSent  bool             `json:"all_sent"`
}
