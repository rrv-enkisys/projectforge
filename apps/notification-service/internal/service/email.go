package service

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"strings"
	"time"

	"github.com/projectforge/notification-service/internal/config"
	"github.com/projectforge/notification-service/internal/model"
)

const resendAPIURL = "https://api.resend.com/emails"

// EmailService sends transactional emails via the Resend API.
type EmailService struct {
	cfg        *config.Config
	httpClient *http.Client
}

// NewEmailService creates a new EmailService.
func NewEmailService(cfg *config.Config) *EmailService {
	return &EmailService{
		cfg: cfg,
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

// resendPayload is the request body for the Resend API.
type resendPayload struct {
	From    string   `json:"from"`
	To      []string `json:"to"`
	Subject string   `json:"subject"`
	Html    string   `json:"html"`
	Text    string   `json:"text,omitempty"`
}

// Send sends an email using the Resend API.
func (s *EmailService) Send(ctx context.Context, to, subject, htmlBody string) error {
	if s.cfg.ResendAPIKey == "" {
		slog.Warn("RESEND_API_KEY not configured, skipping email", "to", to, "subject", subject)
		return nil
	}

	payload := resendPayload{
		From:    fmt.Sprintf("%s <%s>", s.cfg.ResendFromName, s.cfg.ResendFromAddr),
		To:      []string{to},
		Subject: subject,
		Html:    htmlBody,
		Text:    stripHTML(htmlBody),
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("marshaling email payload: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, resendAPIURL, bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("creating Resend request: %w", err)
	}

	req.Header.Set("Authorization", "Bearer "+s.cfg.ResendAPIKey)
	req.Header.Set("Content-Type", "application/json")

	resp, err := s.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("calling Resend API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		return fmt.Errorf("Resend API error: status %d", resp.StatusCode)
	}

	slog.Info("email sent", "to", to, "subject", subject, "status", resp.StatusCode)
	return nil
}

// SendNotificationEmail sends a formatted notification email based on event type.
func (s *EmailService) SendNotificationEmail(ctx context.Context, event *model.NotificationEvent) error {
	if event.RecipientEmail == "" {
		slog.Debug("no recipient email, skipping", "event_type", event.EventType)
		return nil
	}

	subject, htmlBody := s.buildEmailContent(event)
	return s.Send(ctx, event.RecipientEmail, subject, htmlBody)
}

// buildEmailContent generates subject and HTML body based on event type.
func (s *EmailService) buildEmailContent(event *model.NotificationEvent) (string, string) {
	subject := event.Subject
	if subject == "" {
		subject = string(event.EventType)
	}

	var bodyContent string
	switch event.EventType {
	case model.EventTaskAssigned:
		bodyContent = fmt.Sprintf(
			`<p>You have been assigned a new task by <strong>%s</strong>.</p>
			<p><strong>Task:</strong> %s</p>`,
			event.ActorName, event.Body,
		)
	case model.EventTaskCompleted:
		bodyContent = fmt.Sprintf(
			`<p><strong>%s</strong> completed a task.</p>
			<p><strong>Task:</strong> %s</p>`,
			event.ActorName, event.Body,
		)
	case model.EventMilestoneReached:
		bodyContent = fmt.Sprintf(
			`<p>🎉 A milestone has been reached!</p>
			<p><strong>Milestone:</strong> %s</p>
			<p>Completed by <strong>%s</strong></p>`,
			event.Body, event.ActorName,
		)
	case model.EventMentionReceived:
		bodyContent = fmt.Sprintf(
			`<p><strong>%s</strong> mentioned you:</p>
			<blockquote>%s</blockquote>`,
			event.ActorName, event.Body,
		)
	default:
		bodyContent = fmt.Sprintf("<p>%s</p>", event.Body)
	}

	html := fmt.Sprintf(`<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #1a1a1a; margin: 0; padding: 0; }
    .container { max-width: 600px; margin: 0 auto; padding: 40px 20px; }
    .header { background: #4F46E5; color: white; padding: 20px 24px; border-radius: 8px 8px 0 0; }
    .header h1 { margin: 0; font-size: 18px; }
    .content { background: #ffffff; border: 1px solid #e5e7eb; border-top: none; padding: 24px; border-radius: 0 0 8px 8px; }
    blockquote { border-left: 3px solid #4F46E5; margin: 16px 0; padding: 8px 16px; background: #f9fafb; }
    .footer { margin-top: 24px; font-size: 12px; color: #6b7280; text-align: center; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header"><h1>ProjectForge Notification</h1></div>
    <div class="content">
      %s
    </div>
    <div class="footer">
      <p>You received this notification from ProjectForge.<br>
      To manage your notification preferences, visit your account settings.</p>
    </div>
  </div>
</body>
</html>`, bodyContent)

	return subject, html
}

// stripHTML removes HTML tags for plain-text fallback (minimal implementation).
func stripHTML(html string) string {
	result := strings.NewReplacer(
		"<p>", "", "</p>", "\n",
		"<br>", "\n", "<br/>", "\n",
		"<strong>", "", "</strong>", "",
		"<blockquote>", "", "</blockquote>", "",
		"<h1>", "", "</h1>", "\n",
	).Replace(html)
	// Remove remaining HTML tags
	for strings.Contains(result, "<") {
		start := strings.Index(result, "<")
		end := strings.Index(result[start:], ">")
		if end == -1 {
			break
		}
		result = result[:start] + result[start+end+1:]
	}
	return strings.TrimSpace(result)
}
