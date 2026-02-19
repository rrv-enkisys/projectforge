package respond

import (
	"encoding/json"
	"log/slog"
	"net/http"
)

// JSON writes a JSON response with the given status code and data.
func JSON(w http.ResponseWriter, status int, data any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(data); err != nil {
		slog.Error("failed to encode JSON response", "error", err)
	}
}

// Error writes a standardized JSON error response.
func Error(w http.ResponseWriter, status int, code, message string) {
	JSON(w, status, map[string]any{
		"error": map[string]string{
			"code":    code,
			"message": message,
		},
	})
}

// NotFound writes a 404 JSON error response.
func NotFound(w http.ResponseWriter, resource string) {
	Error(w, http.StatusNotFound, "NOT_FOUND", resource+" not found")
}

// BadRequest writes a 400 JSON error response.
func BadRequest(w http.ResponseWriter, message string) {
	Error(w, http.StatusBadRequest, "BAD_REQUEST", message)
}

// InternalError writes a 500 JSON error response.
func InternalError(w http.ResponseWriter, err error) {
	slog.Error("internal server error", "error", err)
	Error(w, http.StatusInternalServerError, "INTERNAL_ERROR", "An unexpected error occurred")
}

// NoContent writes a 204 No Content response.
func NoContent(w http.ResponseWriter) {
	w.WriteHeader(http.StatusNoContent)
}
