package service

import (
	"bytes"
	"context"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/projectforge/notification-service/internal/config"
	"github.com/projectforge/notification-service/internal/model"
)

// WebhookStore is an in-memory store for webhook subscriptions.
// In production, this would be backed by PostgreSQL.
type WebhookStore struct {
	mu            sync.RWMutex
	subscriptions map[string]*model.WebhookSubscription // id -> subscription
	deliveries    map[string]*model.WebhookDelivery      // id -> delivery
}

func newWebhookStore() *WebhookStore {
	return &WebhookStore{
		subscriptions: make(map[string]*model.WebhookSubscription),
		deliveries:    make(map[string]*model.WebhookDelivery),
	}
}

// WebhookService manages webhook subscriptions and deliveries.
type WebhookService struct {
	cfg        *config.Config
	store      *WebhookStore
	httpClient *http.Client
}

// NewWebhookService creates a new WebhookService.
func NewWebhookService(cfg *config.Config) *WebhookService {
	return &WebhookService{
		cfg:   cfg,
		store: newWebhookStore(),
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

// CreateSubscription creates a new webhook subscription.
func (s *WebhookService) CreateSubscription(orgID string, req *model.CreateWebhookRequest) (*model.WebhookSubscription, error) {
	if req.URL == "" {
		return nil, fmt.Errorf("webhook URL is required")
	}
	if len(req.Events) == 0 {
		return nil, fmt.Errorf("at least one event type is required")
	}

	secret := req.Secret
	if secret == "" {
		secret = uuid.New().String() // Auto-generate secret if not provided
	}

	sub := &model.WebhookSubscription{
		ID:             uuid.New().String(),
		OrganizationID: orgID,
		URL:            req.URL,
		Secret:         secret,
		Events:         req.Events,
		Active:         true,
		Description:    req.Description,
		CreatedAt:      time.Now().UTC(),
		UpdatedAt:      time.Now().UTC(),
	}

	s.store.mu.Lock()
	s.store.subscriptions[sub.ID] = sub
	s.store.mu.Unlock()

	slog.Info("webhook subscription created", "id", sub.ID, "url", sub.URL, "org", orgID)
	return sub, nil
}

// GetSubscription returns a subscription by ID.
func (s *WebhookService) GetSubscription(id, orgID string) (*model.WebhookSubscription, error) {
	s.store.mu.RLock()
	sub, ok := s.store.subscriptions[id]
	s.store.mu.RUnlock()

	if !ok || sub.OrganizationID != orgID {
		return nil, fmt.Errorf("webhook subscription not found")
	}
	return sub, nil
}

// ListSubscriptions returns all subscriptions for an organization.
func (s *WebhookService) ListSubscriptions(orgID string) []*model.WebhookSubscription {
	s.store.mu.RLock()
	defer s.store.mu.RUnlock()

	result := make([]*model.WebhookSubscription, 0)
	for _, sub := range s.store.subscriptions {
		if sub.OrganizationID == orgID {
			// Return copy without secret
			copy := *sub
			copy.Secret = ""
			result = append(result, &copy)
		}
	}
	return result
}

// UpdateSubscription updates a webhook subscription.
func (s *WebhookService) UpdateSubscription(id, orgID string, req *model.UpdateWebhookRequest) (*model.WebhookSubscription, error) {
	s.store.mu.Lock()
	defer s.store.mu.Unlock()

	sub, ok := s.store.subscriptions[id]
	if !ok || sub.OrganizationID != orgID {
		return nil, fmt.Errorf("webhook subscription not found")
	}

	if req.URL != nil {
		sub.URL = *req.URL
	}
	if len(req.Events) > 0 {
		sub.Events = req.Events
	}
	if req.Active != nil {
		sub.Active = *req.Active
	}
	if req.Description != nil {
		sub.Description = *req.Description
	}
	sub.UpdatedAt = time.Now().UTC()

	result := *sub
	result.Secret = "" // Don't expose secret
	return &result, nil
}

// DeleteSubscription deletes a webhook subscription.
func (s *WebhookService) DeleteSubscription(id, orgID string) error {
	s.store.mu.Lock()
	defer s.store.mu.Unlock()

	sub, ok := s.store.subscriptions[id]
	if !ok || sub.OrganizationID != orgID {
		return fmt.Errorf("webhook subscription not found")
	}
	delete(s.store.subscriptions, id)
	return nil
}

// Deliver sends an event to all matching webhook subscriptions for an org.
func (s *WebhookService) Deliver(ctx context.Context, event *model.NotificationEvent) []model.DeliveryResult {
	s.store.mu.RLock()
	var matching []*model.WebhookSubscription
	for _, sub := range s.store.subscriptions {
		if sub.OrganizationID == event.OrganizationID && sub.Active && s.matchesEvent(sub, event.EventType) {
			sub := sub // capture
			matching = append(matching, sub)
		}
	}
	s.store.mu.RUnlock()

	results := make([]model.DeliveryResult, 0, len(matching))
	for _, sub := range matching {
		result := s.deliverToSubscription(ctx, sub, event)
		results = append(results, result)
	}
	return results
}

// deliverToSubscription delivers an event to a single webhook with retry.
func (s *WebhookService) deliverToSubscription(ctx context.Context, sub *model.WebhookSubscription, event *model.NotificationEvent) model.DeliveryResult {
	payload, err := json.Marshal(event)
	if err != nil {
		return model.DeliveryResult{Channel: model.ChannelWebhook, Success: false, Error: err.Error()}
	}

	var lastErr error
	for attempt := 0; attempt <= s.cfg.WebhookMaxRetries; attempt++ {
		if attempt > 0 {
			select {
			case <-ctx.Done():
				return model.DeliveryResult{Channel: model.ChannelWebhook, Success: false, Error: "context cancelled"}
			case <-time.After(s.cfg.WebhookRetryDelay * time.Duration(attempt)):
			}
		}

		if err := s.postWebhook(ctx, sub, payload, event.EventType); err != nil {
			lastErr = err
			slog.Warn("webhook delivery failed, will retry",
				"attempt", attempt+1,
				"max", s.cfg.WebhookMaxRetries,
				"url", sub.URL,
				"error", err,
			)
			continue
		}

		slog.Info("webhook delivered", "url", sub.URL, "event", event.EventType)
		return model.DeliveryResult{Channel: model.ChannelWebhook, Success: true}
	}

	return model.DeliveryResult{Channel: model.ChannelWebhook, Success: false, Error: lastErr.Error()}
}

// postWebhook sends the HTTP POST to the webhook URL.
func (s *WebhookService) postWebhook(ctx context.Context, sub *model.WebhookSubscription, payload []byte, eventType model.EventType) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, sub.URL, bytes.NewReader(payload))
	if err != nil {
		return fmt.Errorf("creating webhook request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-ProjectForge-Event", string(eventType))
	req.Header.Set("X-ProjectForge-Signature", s.sign(payload, sub.Secret))
	req.Header.Set("X-ProjectForge-Delivery", uuid.New().String())
	req.Header.Set("User-Agent", "ProjectForge-Webhook/1.0")

	resp, err := s.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("sending webhook: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		return fmt.Errorf("webhook endpoint returned status %d", resp.StatusCode)
	}
	return nil
}

// sign generates an HMAC-SHA256 signature for the payload.
func (s *WebhookService) sign(payload []byte, secret string) string {
	mac := hmac.New(sha256.New, []byte(secret))
	mac.Write(payload)
	return "sha256=" + hex.EncodeToString(mac.Sum(nil))
}

// VerifySignature verifies a webhook signature from an incoming request.
func (s *WebhookService) VerifySignature(payload []byte, signature, secret string) bool {
	expected := s.sign(payload, secret)
	return hmac.Equal([]byte(signature), []byte(expected))
}

// matchesEvent checks if a subscription subscribes to a given event type.
func (s *WebhookService) matchesEvent(sub *model.WebhookSubscription, eventType model.EventType) bool {
	for _, e := range sub.Events {
		if e == eventType || e == "*" {
			return true
		}
	}
	return false
}

// ListDeliveries returns recent deliveries for a subscription.
func (s *WebhookService) ListDeliveries(webhookID, orgID string) []*model.WebhookDelivery {
	// Verify subscription belongs to org
	if _, err := s.GetSubscription(webhookID, orgID); err != nil {
		return nil
	}

	s.store.mu.RLock()
	defer s.store.mu.RUnlock()

	result := make([]*model.WebhookDelivery, 0)
	for _, d := range s.store.deliveries {
		if d.WebhookID == webhookID {
			result = append(result, d)
		}
	}
	return result
}
