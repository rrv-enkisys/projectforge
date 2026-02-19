package service

import (
	"context"
	"log/slog"
	"time"

	"github.com/google/uuid"
	"github.com/projectforge/notification-service/internal/model"
)

// NotificationService is the main orchestrator for sending notifications
// across all configured channels.
type NotificationService struct {
	email   *EmailService
	slack   *SlackService
	webhook *WebhookService
	inApp   *InAppService
}

// NewNotificationService creates the main notification orchestrator.
func NewNotificationService(
	email *EmailService,
	slack *SlackService,
	webhook *WebhookService,
	inApp *InAppService,
) *NotificationService {
	return &NotificationService{
		email:   email,
		slack:   slack,
		webhook: webhook,
		inApp:   inApp,
	}
}

// Send dispatches a notification event to all requested channels.
func (s *NotificationService) Send(ctx context.Context, req *model.SendEventRequest) *model.SendEventResponse {
	event := &model.NotificationEvent{
		ID:             uuid.New().String(),
		EventType:      req.EventType,
		OrganizationID: req.OrganizationID,
		ProjectID:      req.ProjectID,
		ActorID:        req.ActorID,
		ActorName:      req.ActorName,
		RecipientIDs:   req.RecipientIDs,
		RecipientEmail: req.RecipientEmail,
		Subject:        req.Subject,
		Body:           req.Body,
		Metadata:       req.Metadata,
		Channels:       req.Channels,
		CreatedAt:      time.Now().UTC(),
	}

	results := make([]model.DeliveryResult, 0, len(req.Channels))
	allSent := true

	for _, channel := range req.Channels {
		switch channel {
		case model.ChannelEmail:
			result := s.sendEmail(ctx, event)
			if !result.Success {
				allSent = false
			}
			results = append(results, result)

		case model.ChannelSlack:
			result := s.sendSlack(ctx, event)
			if !result.Success {
				allSent = false
			}
			results = append(results, result)

		case model.ChannelWebhook:
			webhookResults := s.webhook.Deliver(ctx, event)
			for _, r := range webhookResults {
				if !r.Success {
					allSent = false
				}
				results = append(results, r)
			}

		case model.ChannelInApp:
			result := s.sendInApp(event)
			if !result.Success {
				allSent = false
			}
			results = append(results, result)
		}
	}

	slog.Info("notification dispatched",
		"event_id", event.ID,
		"event_type", event.EventType,
		"channels", len(req.Channels),
		"all_sent", allSent,
	)

	return &model.SendEventResponse{
		EventID: event.ID,
		Results: results,
		AllSent: allSent,
	}
}

func (s *NotificationService) sendEmail(ctx context.Context, event *model.NotificationEvent) model.DeliveryResult {
	if err := s.email.SendNotificationEmail(ctx, event); err != nil {
		slog.Error("email delivery failed", "error", err, "event_type", event.EventType)
		return model.DeliveryResult{Channel: model.ChannelEmail, Success: false, Error: err.Error()}
	}
	return model.DeliveryResult{Channel: model.ChannelEmail, Success: true}
}

func (s *NotificationService) sendSlack(ctx context.Context, event *model.NotificationEvent) model.DeliveryResult {
	slackWebhookURL := ""
	if event.Metadata != nil {
		if url, ok := event.Metadata["slack_webhook_url"].(string); ok {
			slackWebhookURL = url
		}
	}

	var err error
	if slackWebhookURL != "" {
		err = s.slack.SendToWebhook(ctx, slackWebhookURL, event)
	} else {
		channel := ""
		if event.Metadata != nil {
			if ch, ok := event.Metadata["slack_channel"].(string); ok {
				channel = ch
			}
		}
		err = s.slack.SendNotification(ctx, channel, event)
	}

	if err != nil {
		slog.Error("Slack delivery failed", "error", err, "event_type", event.EventType)
		return model.DeliveryResult{Channel: model.ChannelSlack, Success: false, Error: err.Error()}
	}
	return model.DeliveryResult{Channel: model.ChannelSlack, Success: true}
}

func (s *NotificationService) sendInApp(event *model.NotificationEvent) model.DeliveryResult {
	notifications := s.inApp.Create(event)
	if len(notifications) == 0 && len(event.RecipientIDs) > 0 {
		return model.DeliveryResult{Channel: model.ChannelInApp, Success: false, Error: "failed to create in-app notifications"}
	}
	return model.DeliveryResult{Channel: model.ChannelInApp, Success: true}
}
