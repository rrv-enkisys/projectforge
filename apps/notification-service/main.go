package main

import (
	"context"
	"fmt"
	"log"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/joho/godotenv"
	"github.com/projectforge/notification-service/internal/config"
	"github.com/projectforge/notification-service/internal/handler"
	"github.com/projectforge/notification-service/internal/service"
	"github.com/projectforge/notification-service/pkg/respond"
)

func main() {
	// Load environment variables
	_ = godotenv.Load()

	// Load configuration
	cfg := config.Load()

	// Initialize structured logger
	logLevel := slog.LevelInfo
	if cfg.LogLevel == "debug" {
		logLevel = slog.LevelDebug
	}
	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: logLevel}))
	slog.SetDefault(logger)

	// Initialize services
	emailSvc := service.NewEmailService(cfg)
	slackSvc := service.NewSlackService(cfg)
	webhookSvc := service.NewWebhookService(cfg)
	inAppSvc := service.NewInAppService()
	notifSvc := service.NewNotificationService(emailSvc, slackSvc, webhookSvc, inAppSvc)

	// Initialize handlers
	notifHandler := handler.NewNotificationHandler(notifSvc, inAppSvc)
	webhookHandler := handler.NewWebhookHandler(webhookSvc)

	// Initialize router
	r := chi.NewRouter()

	// Global middleware
	r.Use(middleware.RequestID)
	r.Use(middleware.RealIP)
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(middleware.Timeout(cfg.WriteTimeout))
	r.Use(middleware.Compress(5))

	// Health check
	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		respond.JSON(w, http.StatusOK, map[string]string{
			"status":  "healthy",
			"service": cfg.ServiceName,
		})
	})

	r.Get("/", func(w http.ResponseWriter, r *http.Request) {
		respond.JSON(w, http.StatusOK, map[string]string{
			"message": "ProjectForge Notification Service",
			"version": "1.0.0",
		})
	})

	// API v1 routes
	r.Route("/api/v1", func(r chi.Router) {
		// Notification event dispatch
		r.Post("/notifications/events", notifHandler.SendEvent)

		// In-app notifications
		r.Route("/notifications/in-app", func(r chi.Router) {
			r.Get("/", notifHandler.ListInApp)
			r.Get("/unread-count", notifHandler.UnreadCount)
			r.Patch("/read-all", notifHandler.MarkAllAsRead)
			r.Patch("/{id}/read", notifHandler.MarkAsRead)
			r.Delete("/{id}", notifHandler.DeleteInApp)
		})

		// Webhook subscription management
		r.Route("/webhooks", func(r chi.Router) {
			r.Post("/", webhookHandler.Create)
			r.Get("/", webhookHandler.List)
			r.Get("/{id}", webhookHandler.Get)
			r.Patch("/{id}", webhookHandler.Update)
			r.Delete("/{id}", webhookHandler.Delete)
			r.Get("/{id}/deliveries", webhookHandler.ListDeliveries)
		})
	})

	// Start server
	srv := &http.Server{
		Addr:         ":" + cfg.Port,
		Handler:      r,
		ReadTimeout:  cfg.ReadTimeout,
		WriteTimeout: cfg.WriteTimeout,
		IdleTimeout:  cfg.WriteTimeout * 4,
	}

	go func() {
		slog.Info("starting notification service", "port", cfg.Port, "environment", cfg.Environment)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("server failed to start: %v", err)
		}
	}()

	// Graceful shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	slog.Info("shutting down server...")
	ctx, cancel := context.WithTimeout(context.Background(), cfg.ShutdownTimeout)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		log.Fatal("server forced to shutdown:", err)
	}

	fmt.Println("server stopped")
}
