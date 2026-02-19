package config

import (
	"os"
	"strconv"
	"time"
)

// Config holds all configuration for the notification service.
type Config struct {
	// Server
	Port            string
	ReadTimeout     time.Duration
	WriteTimeout    time.Duration
	ShutdownTimeout time.Duration

	// Email (Resend)
	ResendAPIKey   string
	ResendFromName string
	ResendFromAddr string

	// Slack
	SlackBotToken      string
	SlackDefaultChannel string

	// Webhook
	WebhookSigningSecret string
	WebhookMaxRetries    int
	WebhookRetryDelay    time.Duration

	// App
	Environment string
	LogLevel    string
	ServiceName string
}

// Load reads configuration from environment variables.
func Load() *Config {
	return &Config{
		Port:            getEnv("PORT", "8083"),
		ReadTimeout:     getDuration("READ_TIMEOUT", 15*time.Second),
		WriteTimeout:    getDuration("WRITE_TIMEOUT", 15*time.Second),
		ShutdownTimeout: getDuration("SHUTDOWN_TIMEOUT", 30*time.Second),

		ResendAPIKey:   getEnv("RESEND_API_KEY", ""),
		ResendFromName: getEnv("RESEND_FROM_NAME", "ProjectForge"),
		ResendFromAddr: getEnv("RESEND_FROM_ADDR", "noreply@projectforge.app"),

		SlackBotToken:       getEnv("SLACK_BOT_TOKEN", ""),
		SlackDefaultChannel: getEnv("SLACK_DEFAULT_CHANNEL", "#general"),

		WebhookSigningSecret: getEnv("WEBHOOK_SIGNING_SECRET", "webhook-secret-change-in-prod"),
		WebhookMaxRetries:    getInt("WEBHOOK_MAX_RETRIES", 3),
		WebhookRetryDelay:    getDuration("WEBHOOK_RETRY_DELAY", 5*time.Second),

		Environment: getEnv("ENVIRONMENT", "development"),
		LogLevel:    getEnv("LOG_LEVEL", "info"),
		ServiceName: "notification-service",
	}
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func getInt(key string, fallback int) int {
	if v := os.Getenv(key); v != "" {
		if i, err := strconv.Atoi(v); err == nil {
			return i
		}
	}
	return fallback
}

func getDuration(key string, fallback time.Duration) time.Duration {
	if v := os.Getenv(key); v != "" {
		if d, err := time.ParseDuration(v); err == nil {
			return d
		}
	}
	return fallback
}
