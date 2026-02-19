package model

import "time"

// WebhookStatus represents the status of a webhook delivery attempt.
type WebhookStatus string

const (
	WebhookStatusPending   WebhookStatus = "pending"
	WebhookStatusDelivered WebhookStatus = "delivered"
	WebhookStatusFailed    WebhookStatus = "failed"
)

// WebhookSubscription represents a registered webhook endpoint.
type WebhookSubscription struct {
	ID             string      `json:"id"`
	OrganizationID string      `json:"organization_id"`
	URL            string      `json:"url"`
	Secret         string      `json:"secret,omitempty"` // HMAC signing secret (not returned in API)
	Events         []EventType `json:"events"`           // Which events to subscribe to
	Active         bool        `json:"active"`
	Description    string      `json:"description,omitempty"`
	CreatedAt      time.Time   `json:"created_at"`
	UpdatedAt      time.Time   `json:"updated_at"`
}

// WebhookDelivery represents a single delivery attempt for a webhook.
type WebhookDelivery struct {
	ID             string        `json:"id"`
	WebhookID      string        `json:"webhook_id"`
	EventType      EventType     `json:"event_type"`
	Payload        any           `json:"payload"`
	Status         WebhookStatus `json:"status"`
	StatusCode     int           `json:"status_code,omitempty"`
	AttemptCount   int           `json:"attempt_count"`
	NextRetryAt    *time.Time    `json:"next_retry_at,omitempty"`
	ResponseBody   string        `json:"response_body,omitempty"`
	Error          string        `json:"error,omitempty"`
	DeliveredAt    *time.Time    `json:"delivered_at,omitempty"`
	CreatedAt      time.Time     `json:"created_at"`
}

// CreateWebhookRequest is the API request for creating a webhook subscription.
type CreateWebhookRequest struct {
	URL         string      `json:"url"`
	Events      []EventType `json:"events"`
	Secret      string      `json:"secret,omitempty"`
	Description string      `json:"description,omitempty"`
}

// UpdateWebhookRequest is the API request for updating a webhook subscription.
type UpdateWebhookRequest struct {
	URL         *string      `json:"url,omitempty"`
	Events      []EventType  `json:"events,omitempty"`
	Active      *bool        `json:"active,omitempty"`
	Description *string      `json:"description,omitempty"`
}
