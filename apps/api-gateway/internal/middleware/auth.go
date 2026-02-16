package middleware

import (
	"context"
	"log/slog"
	"net/http"
	"os"
	"strings"

	"github.com/projectforge/api-gateway/internal/firebase"
	"github.com/projectforge/api-gateway/pkg/response"
)

// ContextKey is a type for context keys
type ContextKey string

const (
	// UserUIDKey is the context key for user UID
	UserUIDKey ContextKey = "user_uid"
	// UserEmailKey is the context key for user email
	UserEmailKey ContextKey = "user_email"
	// UserClaimsKey is the context key for all user claims
	UserClaimsKey ContextKey = "user_claims"
)

// Auth creates an authentication middleware
func Auth(firebaseClient *firebase.Client) func(http.Handler) http.Handler {
	// Check if running in development mode
	isDevelopment := os.Getenv("ENVIRONMENT") == "development"

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// DEVELOPMENT MODE: Bypass authentication
			if isDevelopment {
				slog.Debug("Auth bypass in development mode")
				// Set dummy user context for development
				ctx := r.Context()
				ctx = context.WithValue(ctx, UserUIDKey, "dev-user-uid")
				ctx = context.WithValue(ctx, UserEmailKey, "dev@projectforge.local")
				ctx = context.WithValue(ctx, UserClaimsKey, map[string]interface{}{
					"email": "dev@projectforge.local",
					"org_id": "dev-org-id",
				})
				next.ServeHTTP(w, r.WithContext(ctx))
				return
			}

			// PRODUCTION MODE: Full authentication
			// Extract Bearer token from Authorization header
			authHeader := r.Header.Get("Authorization")
			if authHeader == "" {
				response.Unauthorized(w, "Missing authorization header")
				return
			}

			// Check for Bearer prefix
			parts := strings.Split(authHeader, " ")
			if len(parts) != 2 || parts[0] != "Bearer" {
				response.Unauthorized(w, "Invalid authorization header format")
				return
			}

			idToken := parts[1]

			// Verify the Firebase ID token
			token, err := firebaseClient.VerifyIDToken(r.Context(), idToken)
			if err != nil {
				response.Unauthorized(w, "Invalid or expired token")
				return
			}

			// Extract claims
			uid := token.UID
			email := ""
			if emailClaim, ok := token.Claims["email"].(string); ok {
				email = emailClaim
			}

			// Add user information to context
			ctx := r.Context()
			ctx = context.WithValue(ctx, UserUIDKey, uid)
			ctx = context.WithValue(ctx, UserEmailKey, email)
			ctx = context.WithValue(ctx, UserClaimsKey, token.Claims)

			// Continue with the request
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

// GetUserUID retrieves the user UID from context
func GetUserUID(ctx context.Context) string {
	if uid, ok := ctx.Value(UserUIDKey).(string); ok {
		return uid
	}
	return ""
}

// GetUserEmail retrieves the user email from context
func GetUserEmail(ctx context.Context) string {
	if email, ok := ctx.Value(UserEmailKey).(string); ok {
		return email
	}
	return ""
}

// GetUserClaims retrieves all user claims from context
func GetUserClaims(ctx context.Context) map[string]interface{} {
	if claims, ok := ctx.Value(UserClaimsKey).(map[string]interface{}); ok {
		return claims
	}
	return nil
}
