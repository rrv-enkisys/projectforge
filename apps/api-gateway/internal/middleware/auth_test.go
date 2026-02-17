package middleware

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/projectforge/api-gateway/internal/firebase"
)

func TestAuthMiddleware_Development(t *testing.T) {
	// Set development mode
	t.Setenv("ENVIRONMENT", "development")

	// Create a mock Firebase client (won't be used in dev mode)
	firebaseClient := &firebase.Client{}

	// Create middleware
	authMiddleware := Auth(firebaseClient)

	// Create a test handler that checks for user context
	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		userUID := GetUserUID(r.Context())
		userEmail := GetUserEmail(r.Context())

		if userUID == "" {
			t.Error("Expected user UID in context, got empty string")
		}

		if userEmail == "" {
			t.Error("Expected user email in context, got empty string")
		}

		w.WriteHeader(http.StatusOK)
	})

	// Wrap handler with middleware
	handler := authMiddleware(testHandler)

	// Create test request
	req := httptest.NewRequest(http.MethodGet, "/test", nil)
	rr := httptest.NewRecorder()

	// Execute request
	handler.ServeHTTP(rr, req)

	// Check response
	if rr.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", rr.Code)
	}
}

func TestAuthMiddleware_MissingAuthHeader(t *testing.T) {
	// Set production mode
	t.Setenv("ENVIRONMENT", "production")

	// Create a mock Firebase client
	firebaseClient := &firebase.Client{}

	// Create middleware
	authMiddleware := Auth(firebaseClient)

	// Create a test handler
	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	// Wrap handler with middleware
	handler := authMiddleware(testHandler)

	// Create test request without Authorization header
	req := httptest.NewRequest(http.MethodGet, "/test", nil)
	rr := httptest.NewRecorder()

	// Execute request
	handler.ServeHTTP(rr, req)

	// Check response - should be 401 Unauthorized
	if rr.Code != http.StatusUnauthorized {
		t.Errorf("Expected status 401, got %d", rr.Code)
	}
}

func TestAuthMiddleware_InvalidAuthHeaderFormat(t *testing.T) {
	// Set production mode
	t.Setenv("ENVIRONMENT", "production")

	// Create a mock Firebase client
	firebaseClient := &firebase.Client{}

	// Create middleware
	authMiddleware := Auth(firebaseClient)

	// Create a test handler
	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	// Wrap handler with middleware
	handler := authMiddleware(testHandler)

	// Test cases for invalid auth headers
	testCases := []struct {
		name       string
		authHeader string
	}{
		{"No Bearer prefix", "some-token"},
		{"Wrong prefix", "Basic some-token"},
		{"Missing token", "Bearer "},
		{"Empty header", ""},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			req := httptest.NewRequest(http.MethodGet, "/test", nil)
			if tc.authHeader != "" {
				req.Header.Set("Authorization", tc.authHeader)
			}
			rr := httptest.NewRecorder()

			handler.ServeHTTP(rr, req)

			if rr.Code != http.StatusUnauthorized {
				t.Errorf("Expected status 401 for %s, got %d", tc.name, rr.Code)
			}
		})
	}
}

func TestGetUserUID(t *testing.T) {
	// Create context with user UID
	ctx := context.WithValue(context.Background(), UserUIDKey, "test-uid-123")

	uid := GetUserUID(ctx)
	if uid != "test-uid-123" {
		t.Errorf("Expected 'test-uid-123', got '%s'", uid)
	}

	// Test with empty context
	emptyUID := GetUserUID(context.Background())
	if emptyUID != "" {
		t.Errorf("Expected empty string, got '%s'", emptyUID)
	}
}

func TestGetUserEmail(t *testing.T) {
	// Create context with user email
	ctx := context.WithValue(context.Background(), UserEmailKey, "test@example.com")

	email := GetUserEmail(ctx)
	if email != "test@example.com" {
		t.Errorf("Expected 'test@example.com', got '%s'", email)
	}

	// Test with empty context
	emptyEmail := GetUserEmail(context.Background())
	if emptyEmail != "" {
		t.Errorf("Expected empty string, got '%s'", emptyEmail)
	}
}

func TestGetUserClaims(t *testing.T) {
	// Create context with user claims
	claims := map[string]interface{}{
		"email": "test@example.com",
		"name":  "Test User",
	}
	ctx := context.WithValue(context.Background(), UserClaimsKey, claims)

	retrievedClaims := GetUserClaims(ctx)
	if retrievedClaims == nil {
		t.Fatal("Expected claims, got nil")
	}

	if retrievedClaims["email"] != "test@example.com" {
		t.Errorf("Expected email 'test@example.com', got '%v'", retrievedClaims["email"])
	}

	// Test with empty context
	emptyClaims := GetUserClaims(context.Background())
	if emptyClaims != nil {
		t.Errorf("Expected nil, got %v", emptyClaims)
	}
}
