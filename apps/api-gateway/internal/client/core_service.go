package client

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"time"
)

// CoreServiceClient is a client for the Core Service
type CoreServiceClient struct {
	baseURL    string
	httpClient *http.Client
	logger     *slog.Logger
}

// UserOrganizationResponse represents the response from the user organization endpoint
type UserOrganizationResponse struct {
	OrganizationID string `json:"organization_id"`
	Role           string `json:"role"`
}

// NewCoreServiceClient creates a new Core Service client
func NewCoreServiceClient(baseURL string, logger *slog.Logger) *CoreServiceClient {
	return &CoreServiceClient{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 5 * time.Second, // 5 second timeout for tenant lookup
		},
		logger: logger,
	}
}

// GetUserOrganization fetches the user's primary organization by Firebase UID
func (c *CoreServiceClient) GetUserOrganization(ctx context.Context, firebaseUID string) (*UserOrganizationResponse, error) {
	url := fmt.Sprintf("%s/api/v1/users/firebase/%s/organization", c.baseURL, firebaseUID)

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// Add headers
	req.Header.Set("Content-Type", "application/json")

	c.logger.Debug("Fetching user organization", "firebase_uid", firebaseUID, "url", url)

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, fmt.Errorf("user or organization not found for firebase_uid: %s", firebaseUID)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	var result UserOrganizationResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	c.logger.Debug("User organization fetched successfully",
		"firebase_uid", firebaseUID,
		"organization_id", result.OrganizationID,
		"role", result.Role)

	return &result, nil
}
