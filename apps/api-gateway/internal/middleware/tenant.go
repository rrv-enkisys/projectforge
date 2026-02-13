package middleware

import (
	"context"
	"net/http"

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
func Tenant() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			ctx := r.Context()

			// Get user claims from context (set by Auth middleware)
			claims := GetUserClaims(ctx)
			if claims == nil {
				response.Unauthorized(w, "User claims not found")
				return
			}

			// Try to get organization_id from header first (for explicit org selection)
			organizationID := r.Header.Get(HeaderOrganizationID)

			// If not in header, try to get from custom claims
			if organizationID == "" {
				if orgID, ok := claims["organization_id"].(string); ok {
					organizationID = orgID
				}
			}

			// If still not found, try to get from organizations array (first one)
			if organizationID == "" {
				if orgs, ok := claims["organizations"].([]interface{}); ok && len(orgs) > 0 {
					if orgMap, ok := orgs[0].(map[string]interface{}); ok {
						if orgID, ok := orgMap["id"].(string); ok {
							organizationID = orgID
						}
					}
				}
			}

			// Organization ID is optional for some endpoints (e.g., /users/me)
			// So we don't enforce it here, but we set it if available

			// Get user role for this organization (if available)
			userRole := ""
			if organizationID != "" {
				// Try to extract role from claims
				if orgs, ok := claims["organizations"].([]interface{}); ok {
					for _, org := range orgs {
						if orgMap, ok := org.(map[string]interface{}); ok {
							if orgID, ok := orgMap["id"].(string); ok && orgID == organizationID {
								if role, ok := orgMap["role"].(string); ok {
									userRole = role
								}
								break
							}
						}
					}
				}
			}

			// Add organization context to context
			if organizationID != "" {
				ctx = context.WithValue(ctx, OrganizationIDKey, organizationID)
			}
			if userRole != "" {
				ctx = context.WithValue(ctx, UserRoleKey, userRole)
			}

			// Set headers for downstream services
			userUID := GetUserUID(ctx)
			userEmail := GetUserEmail(ctx)

			if organizationID != "" {
				r.Header.Set(HeaderOrganizationID, organizationID)
			}
			if userUID != "" {
				r.Header.Set(HeaderUserID, userUID)
			}
			if userEmail != "" {
				r.Header.Set(HeaderUserEmail, userEmail)
			}
			if userRole != "" {
				r.Header.Set(HeaderUserRole, userRole)
			}

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
