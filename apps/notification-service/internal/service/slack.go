package service

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"time"

	"github.com/projectforge/notification-service/internal/config"
	"github.com/projectforge/notification-service/internal/model"
)

// SlackService sends notifications to Slack channels.
type SlackService struct {
	cfg        *config.Config
	httpClient *http.Client
}

// NewSlackService creates a new SlackService.
func NewSlackService(cfg *config.Config) *SlackService {
	return &SlackService{
		cfg: cfg,
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

// slackMessage is the payload for Slack incoming webhooks.
type slackMessage struct {
	Channel     string       `json:"channel,omitempty"`
	Text        string       `json:"text"`
	Attachments []slackAttachment `json:"attachments,omitempty"`
}

type slackAttachment struct {
	Color  string `json:"color"`
	Title  string `json:"title"`
	Text   string `json:"text"`
	Footer string `json:"footer"`
	Ts     int64  `json:"ts"`
}

// SendToWebhook posts a Slack message to an incoming webhook URL.
func (s *SlackService) SendToWebhook(ctx context.Context, webhookURL string, event *model.NotificationEvent) error {
	if webhookURL == "" {
		slog.Warn("no Slack webhook URL configured, skipping", "event_type", event.EventType)
		return nil
	}

	msg := s.buildMessage(event)
	payload, err := json.Marshal(msg)
	if err != nil {
		return fmt.Errorf("marshaling Slack message: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, webhookURL, bytes.NewReader(payload))
	if err != nil {
		return fmt.Errorf("creating Slack request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := s.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("sending Slack message: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		return fmt.Errorf("Slack webhook returned status %d", resp.StatusCode)
	}

	slog.Info("Slack notification sent", "event_type", event.EventType)
	return nil
}

// SendNotification sends a formatted Slack notification based on event type.
// Uses the Slack Bot Token to post to a channel.
func (s *SlackService) SendNotification(ctx context.Context, channel string, event *model.NotificationEvent) error {
	if s.cfg.SlackBotToken == "" {
		slog.Warn("SLACK_BOT_TOKEN not configured, skipping", "event_type", event.EventType)
		return nil
	}

	if channel == "" {
		channel = s.cfg.SlackDefaultChannel
	}

	msg := s.buildMessage(event)
	msg.Channel = channel

	payload, err := json.Marshal(msg)
	if err != nil {
		return fmt.Errorf("marshaling Slack message: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, "https://slack.com/api/chat.postMessage", bytes.NewReader(payload))
	if err != nil {
		return fmt.Errorf("creating Slack API request: %w", err)
	}
	req.Header.Set("Authorization", "Bearer "+s.cfg.SlackBotToken)
	req.Header.Set("Content-Type", "application/json")

	resp, err := s.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("calling Slack API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		return fmt.Errorf("Slack API returned status %d", resp.StatusCode)
	}

	slog.Info("Slack API notification sent", "channel", channel, "event_type", event.EventType)
	return nil
}

// buildMessage creates a Slack message from a notification event.
func (s *SlackService) buildMessage(event *model.NotificationEvent) slackMessage {
	color := colorForEvent(event.EventType)
	icon := iconForEvent(event.EventType)

	return slackMessage{
		Text: fmt.Sprintf("%s *%s*", icon, event.Subject),
		Attachments: []slackAttachment{
			{
				Color:  color,
				Text:   event.Body,
				Footer: fmt.Sprintf("ProjectForge • by %s", event.ActorName),
				Ts:     time.Now().Unix(),
			},
		},
	}
}

func colorForEvent(eventType model.EventType) string {
	switch eventType {
	case model.EventTaskCompleted, model.EventMilestoneReached, model.EventProjectCompleted:
		return "#22c55e" // green
	case model.EventTaskAssigned, model.EventMentionReceived:
		return "#4F46E5" // indigo
	case model.EventDocumentUploaded:
		return "#f59e0b" // amber
	default:
		return "#6b7280" // gray
	}
}

func iconForEvent(eventType model.EventType) string {
	switch eventType {
	case model.EventTaskCreated:
		return "📋"
	case model.EventTaskCompleted:
		return "✅"
	case model.EventTaskAssigned:
		return "👤"
	case model.EventMilestoneReached:
		return "🎯"
	case model.EventProjectCompleted:
		return "🎉"
	case model.EventDocumentUploaded:
		return "📄"
	case model.EventMentionReceived:
		return "💬"
	default:
		return "🔔"
	}
}
