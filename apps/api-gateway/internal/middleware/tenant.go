package middleware

import (
	"context"
	"log/slog"
	"net/http"
	"os"

	"github.com/projectforge/api-gateway/internal/client"
	"github.com/projectforge/api-gateway/pkg/response"
)

const (
	// OrganizationIDKey is the context key for organization ID
	OrganizationIDKey ContextKey = "organization_id"
	// UserRoleKey is the context key for user role in organization
	UserRoleKey ContextKey = "user_role"
)

// Headers that will be forwarded to downstream services
const (
	HeaderOrganizationID = "X-Organization-ID"
	HeaderUserID         = "X-User-ID"
	HeaderUserEmail      = "X-User-Email"
	HeaderUserRole       = "X-User-Role"
)

// Tenant creates a tenant middleware that extracts and validates organization context
func Tenant(coreServiceClient *client.CoreServiceClient) func(http.Handler) http.Handler {
	// Check if running in development mode
	isDevelopment := os.Getenv("ENVIRONMENT") == "development"
	logger := slog.Default()

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			ctx := r.Context()

			// Get user UID from context (set by Auth middleware)
			userUID := GetUserUID(ctx)
			if userUID == "" {
				response.Unauthorized(w, "User UID not found in context")
				return
			}

			userEmail := GetUserEmail(ctx)

			var organizationID string
			var userRole string

			// DEVELOPMENT MODE: Use hardcoded organization for development
			if isDevelopment {
				logger.Debug("Tenant context bypass in development mode", "user_uid", userUID)
				organizationID = "11111111-1111-1111-1111-111111111111"
				userRole = "admin"
			} else {
				// PRODUCTION MODE: Fetch organization from Core Service
				logger.Debug("Fetching user organization from Core Service", "user_uid", userUID)

				userOrg, err := coreServiceClient.GetUserOrganization(ctx, userUID)
				if err != nil {
					logger.Error("Failed to fetch user organization",
						"user_uid", userUID,
						"error", err)

					// Check if it's a not found error
					if err.Error() == "user or organization not found for firebase_uid: "+userUID {
						response.NotFound(w, "User is not associated with any organization. Please contact support.")
					} else {
						response.ServiceUnavailable(w, "Unable to determine user organization. Please try again.")
					}
					return
				}

				organizationID = userOrg.OrganizationID
				userRole = userOrg.Role

				logger.Info("Tenant context established",
					"user_uid", userUID,
					"organization_id", organizationID,
					"role", userRole)
			}

			// Add organization context to context
			ctx = context.WithValue(ctx, OrganizationIDKey, organizationID)
			ctx = context.WithValue(ctx, UserRoleKey, userRole)

			// Set headers for downstream services
			// These headers are CRITICAL for multi-tenant isolation
			r.Header.Set(HeaderOrganizationID, organizationID)
			r.Header.Set(HeaderUserID, userUID)
			if userEmail != "" {
				r.Header.Set(HeaderUserEmail, userEmail)
			}
			r.Header.Set(HeaderUserRole, userRole)

			logger.Debug("Forwarding request with tenant context",
				"path", r.URL.Path,
				"organization_id", organizationID,
				"user_uid", userUID)

			// Continue with the request
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

// GetOrganizationID retrieves the organization ID from context
func GetOrganizationID(ctx context.Context) string {
	if orgID, ok := ctx.Value(OrganizationIDKey).(string); ok {
		return orgID
	}
	return ""
}

// GetUserRole retrieves the user role from context
func GetUserRole(ctx context.Context) string {
	if role, ok := ctx.Value(UserRoleKey).(string); ok {
		return role
	}
	return ""
}
