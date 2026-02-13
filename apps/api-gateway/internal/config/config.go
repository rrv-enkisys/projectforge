package config

import (
	"log"
	"os"
	"strconv"
)

// Config holds all application configuration
type Config struct {
	// Server configuration
	Port        string
	Environment string

	// Service URLs
	CoreServiceURL string
	AIServiceURL   string

	// Firebase configuration
	FirebaseProjectID     string
	FirebaseCredentials   string // Path to credentials JSON file

	// Rate limiting
	RateLimitRPS int // Requests per second per organization

	// CORS
	CORSOrigins []string
}

// Load loads configuration from environment variables
func Load() *Config {
	return &Config{
		Port:                  getEnv("PORT", "8080"),
		Environment:           getEnv("ENVIRONMENT", "development"),
		CoreServiceURL:        getEnv("CORE_SERVICE_URL", "http://localhost:8000"),
		AIServiceURL:          getEnv("AI_SERVICE_URL", "http://localhost:8001"),
		FirebaseProjectID:     getEnv("FIREBASE_PROJECT_ID", ""),
		FirebaseCredentials:   getEnv("FIREBASE_CREDENTIALS", ""),
		RateLimitRPS:          getEnvAsInt("RATE_LIMIT_RPS", 100),
		CORSOrigins:           getEnvAsSlice("CORS_ORIGINS", []string{"http://localhost:3000"}),
	}
}

// Validate checks if required configuration is present
func (c *Config) Validate() error {
	if c.FirebaseProjectID == "" {
		log.Println("Warning: FIREBASE_PROJECT_ID not set, authentication will use default credentials")
	}
	return nil
}

// getEnv gets an environment variable or returns a default value
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// getEnvAsInt gets an environment variable as int or returns a default value
func getEnvAsInt(key string, defaultValue int) int {
	valueStr := os.Getenv(key)
	if valueStr == "" {
		return defaultValue
	}
	value, err := strconv.Atoi(valueStr)
	if err != nil {
		log.Printf("Invalid integer for %s: %v, using default %d", key, err, defaultValue)
		return defaultValue
	}
	return value
}

// getEnvAsSlice gets an environment variable as slice or returns a default value
func getEnvAsSlice(key string, defaultValue []string) []string {
	valueStr := os.Getenv(key)
	if valueStr == "" {
		return defaultValue
	}
	// Simple comma-separated parsing
	// For production, consider using a more robust parser
	return []string{valueStr}
}
