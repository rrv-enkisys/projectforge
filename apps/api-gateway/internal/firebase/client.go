package firebase

import (
	"context"
	"log"

	firebase "firebase.google.com/go/v4"
	"firebase.google.com/go/v4/auth"
	"google.golang.org/api/option"
)

// Client wraps the Firebase Auth client
type Client struct {
	authClient *auth.Client
}

// NewClient initializes a new Firebase client
func NewClient(ctx context.Context, projectID, credentialsPath string) (*Client, error) {
	var app *firebase.App
	var err error

	if credentialsPath != "" {
		// Use credentials file if provided
		opt := option.WithCredentialsFile(credentialsPath)
		config := &firebase.Config{ProjectID: projectID}
		app, err = firebase.NewApp(ctx, config, opt)
	} else {
		// Use default credentials (for GCP environments)
		config := &firebase.Config{ProjectID: projectID}
		app, err = firebase.NewApp(ctx, config)
	}

	if err != nil {
		return nil, err
	}

	authClient, err := app.Auth(ctx)
	if err != nil {
		return nil, err
	}

	log.Println("Firebase client initialized successfully")
	return &Client{authClient: authClient}, nil
}

// VerifyIDToken verifies a Firebase ID token and returns the token claims
func (c *Client) VerifyIDToken(ctx context.Context, idToken string) (*auth.Token, error) {
	token, err := c.authClient.VerifyIDToken(ctx, idToken)
	if err != nil {
		return nil, err
	}
	return token, nil
}

// GetUser retrieves user information by UID
func (c *Client) GetUser(ctx context.Context, uid string) (*auth.UserRecord, error) {
	user, err := c.authClient.GetUser(ctx, uid)
	if err != nil {
		return nil, err
	}
	return user, nil
}
