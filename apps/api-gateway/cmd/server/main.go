package main

import (
	"context"
	"log"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/go-chi/chi/v5"
	chimiddleware "github.com/go-chi/chi/v5/middleware"
	"github.com/joho/godotenv"

	"github.com/projectforge/api-gateway/internal/config"
	"github.com/projectforge/api-gateway/internal/firebase"
	"github.com/projectforge/api-gateway/internal/handler"
	"github.com/projectforge/api-gateway/internal/middleware"
)

func main() {
	// Load environment variables from .env file (if exists)
	_ = godotenv.Load()

	// Load configuration
	cfg := config.Load()
	if err := cfg.Validate(); err != nil {
		log.Fatalf("Invalid configuration: %v", err)
	}

	// Initialize logger
	logLevel := slog.LevelInfo
	if cfg.Environment == "development" {
		logLevel = slog.LevelDebug
	}

	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
		Level: logLevel,
	}))
	slog.SetDefault(logger)

	// Initialize Firebase client
	ctx := context.Background()
	firebaseClient, err := firebase.NewClient(ctx, cfg.FirebaseProjectID, cfg.FirebaseCredentials)
	if err != nil {
		log.Fatalf("Failed to initialize Firebase client: %v", err)
	}

	// Initialize handlers
	healthHandler := handler.NewHealthHandler()
	proxyHandler := handler.NewProxyHandler(cfg.CoreServiceURL, cfg.AIServiceURL, logger)

	// Initialize rate limiter
	rateLimiter := middleware.NewRateLimiter(cfg.RateLimitRPS)

	// Initialize router
	r := chi.NewRouter()

	// Global middleware (applied to all routes)
	r.Use(chimiddleware.RequestID)
	r.Use(chimiddleware.RealIP)
	r.Use(middleware.StructuredLogger(logger))
	r.Use(chimiddleware.Recoverer)
	r.Use(middleware.CORS(cfg.CORSOrigins))
	r.Use(chimiddleware.Timeout(60 * time.Second))

	// Public routes (no authentication required)
	r.Get("/health", healthHandler.Check)

	// API routes (authenticated)
	r.Route("/api/v1", func(r chi.Router) {
		// Authentication middleware
		r.Use(middleware.Auth(firebaseClient))

		// Tenant middleware (extracts organization context)
		r.Use(middleware.Tenant())

		// Rate limiting middleware
		r.Use(middleware.RateLimit(rateLimiter))

		// Core Service routes - match any method and path
		r.HandleFunc("/organizations", proxyHandler.ProxyToCore())
		r.HandleFunc("/organizations/*", proxyHandler.ProxyToCore())

		r.HandleFunc("/clients", proxyHandler.ProxyToCore())
		r.HandleFunc("/clients/*", proxyHandler.ProxyToCore())

		r.HandleFunc("/projects", proxyHandler.ProxyToCore())
		r.HandleFunc("/projects/*", proxyHandler.ProxyToCore())

		r.HandleFunc("/tasks", proxyHandler.ProxyToCore())
		r.HandleFunc("/tasks/*", proxyHandler.ProxyToCore())

		r.HandleFunc("/milestones", proxyHandler.ProxyToCore())
		r.HandleFunc("/milestones/*", proxyHandler.ProxyToCore())

		r.HandleFunc("/users", proxyHandler.ProxyToCore())
		r.HandleFunc("/users/*", proxyHandler.ProxyToCore())

		// AI Service routes
		r.HandleFunc("/documents", proxyHandler.ProxyToAI())
		r.HandleFunc("/documents/*", proxyHandler.ProxyToAI())

		r.HandleFunc("/chat", proxyHandler.ProxyToAI())
		r.HandleFunc("/chat/*", proxyHandler.ProxyToAI())
	})

	// Create HTTP server
	srv := &http.Server{
		Addr:         ":" + cfg.Port,
		Handler:      r,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Start server in a goroutine
	go func() {
		logger.Info("Starting API Gateway",
			"port", cfg.Port,
			"environment", cfg.Environment,
			"core_service", cfg.CoreServiceURL,
			"ai_service", cfg.AIServiceURL,
		)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Server failed to start: %v", err)
		}
	}()

	// Wait for interrupt signal for graceful shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	logger.Info("Shutting down server...")

	// Create shutdown context with timeout
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Attempt graceful shutdown
	if err := srv.Shutdown(shutdownCtx); err != nil {
		log.Fatal("Server forced to shutdown:", err)
	}

	logger.Info("Server stopped gracefully")
}
