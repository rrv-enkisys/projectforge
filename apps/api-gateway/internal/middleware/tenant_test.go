package middleware

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/projectforge/api-gateway/internal/client"
)

func TestTenantMiddleware_Development(t *testing.T) {
	// Set development mode
	t.Setenv("ENVIRONMENT", "development")

	// Create a nil client (won't be used in dev mode)
	var coreServiceClient *client.CoreServiceClient

	// Create middleware
	tenantMiddleware := Tenant(coreServiceClient)

	// Create a test handler that checks for organization context
	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		orgID := GetOrganizationID(r.Context())
		role := GetUserRole(r.Context())

		// In dev mode, should have hardcoded org ID
		if orgID == "" {
			t.Error("Expected organization ID in context, got empty string")
		}

		if role == "" {
			t.Error("Expected user role in context, got empty string")
		}

		// Check headers
		if r.Header.Get(HeaderOrganizationID) == "" {
			t.Error("Expected X-Organization-ID header, got empty")
		}

		w.WriteHeader(http.StatusOK)
	})

	// Wrap handler with middleware
	handler := tenantMiddleware(testHandler)

	// Create test request with user context
	req := httptest.NewRequest(http.MethodGet, "/test", nil)
	ctx := context.WithValue(req.Context(), UserUIDKey, "test-uid")
	ctx = context.WithValue(ctx, UserEmailKey, "test@example.com")
	req = req.WithContext(ctx)

	rr := httptest.NewRecorder()

	// Execute request
	handler.ServeHTTP(rr, req)

	// Check response
	if rr.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", rr.Code)
	}
}

func TestTenantMiddleware_MissingUserUID(t *testing.T) {
	// Set production mode
	t.Setenv("ENVIRONMENT", "production")

	// Create a nil client
	var coreServiceClient *client.CoreServiceClient

	// Create middleware
	tenantMiddleware := Tenant(coreServiceClient)

	// Create a test handler
	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	// Wrap handler with middleware
	handler := tenantMiddleware(testHandler)

	// Create test request WITHOUT user UID in context
	req := httptest.NewRequest(http.MethodGet, "/test", nil)
	rr := httptest.NewRecorder()

	// Execute request
	handler.ServeHTTP(rr, req)

	// Check response - should be 401 Unauthorized
	if rr.Code != http.StatusUnauthorized {
		t.Errorf("Expected status 401, got %d", rr.Code)
	}
}

func TestGetOrganizationID(t *testing.T) {
	// Create context with organization ID
	ctx := context.WithValue(context.Background(), OrganizationIDKey, "org-123")

	orgID := GetOrganizationID(ctx)
	if orgID != "org-123" {
		t.Errorf("Expected 'org-123', got '%s'", orgID)
	}

	// Test with empty context
	emptyOrgID := GetOrganizationID(context.Background())
	if emptyOrgID != "" {
		t.Errorf("Expected empty string, got '%s'", emptyOrgID)
	}
}

func TestGetUserRole(t *testing.T) {
	// Create context with user role
	ctx := context.WithValue(context.Background(), UserRoleKey, "admin")

	role := GetUserRole(ctx)
	if role != "admin" {
		t.Errorf("Expected 'admin', got '%s'", role)
	}

	// Test with empty context
	emptyRole := GetUserRole(context.Background())
	if emptyRole != "" {
		t.Errorf("Expected empty string, got '%s'", emptyRole)
	}
}
