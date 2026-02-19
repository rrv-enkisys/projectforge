package service_test

import (
	"testing"
	"time"

	"github.com/projectforge/notification-service/internal/model"
	"github.com/projectforge/notification-service/internal/service"
)

const (
	inAppOrgID  = "org-inapp-test"
	inAppUser1  = "user-111"
	inAppUser2  = "user-222"
)

func makeEvent(orgID string, recipients []string) *model.NotificationEvent {
	return &model.NotificationEvent{
		ID:             "evt-" + time.Now().String(),
		EventType:      model.EventTaskAssigned,
		OrganizationID: orgID,
		ActorID:        "actor-1",
		ActorName:      "Alice",
		RecipientIDs:   recipients,
		Subject:        "New task assigned",
		Body:           "You have a new task",
	}
}

func TestInAppService_Create(t *testing.T) {
	svc := service.NewInAppService()

	event := makeEvent(inAppOrgID, []string{inAppUser1, inAppUser2})
	created := svc.Create(event)

	if len(created) != 2 {
		t.Errorf("expected 2 notifications, got %d", len(created))
	}

	for _, n := range created {
		if n.ID == "" {
			t.Error("expected non-empty notification ID")
		}
		if n.Status != model.StatusPending {
			t.Errorf("expected status pending, got %s", n.Status)
		}
		if n.Title != event.Subject {
			t.Errorf("expected title %q, got %q", event.Subject, n.Title)
		}
		if n.OrganizationID != inAppOrgID {
			t.Errorf("expected org ID %q, got %q", inAppOrgID, n.OrganizationID)
		}
	}
}

func TestInAppService_Create_EmptyRecipients(t *testing.T) {
	svc := service.NewInAppService()
	event := makeEvent(inAppOrgID, []string{}) // No recipients
	created := svc.Create(event)
	if len(created) != 0 {
		t.Errorf("expected 0 notifications, got %d", len(created))
	}
}

func TestInAppService_List_All(t *testing.T) {
	svc := service.NewInAppService()

	// Create 3 notifications for user1
	svc.Create(makeEvent(inAppOrgID, []string{inAppUser1}))
	svc.Create(makeEvent(inAppOrgID, []string{inAppUser1}))
	svc.Create(makeEvent(inAppOrgID, []string{inAppUser1}))
	// 1 for user2
	svc.Create(makeEvent(inAppOrgID, []string{inAppUser2}))

	list := svc.List(inAppOrgID, inAppUser1, false, 0)
	if len(list) != 3 {
		t.Errorf("expected 3 notifications for user1, got %d", len(list))
	}

	list2 := svc.List(inAppOrgID, inAppUser2, false, 0)
	if len(list2) != 1 {
		t.Errorf("expected 1 notification for user2, got %d", len(list2))
	}
}

func TestInAppService_List_UnreadOnly(t *testing.T) {
	svc := service.NewInAppService()

	created := svc.Create(makeEvent(inAppOrgID, []string{inAppUser1}))
	svc.Create(makeEvent(inAppOrgID, []string{inAppUser1}))
	svc.Create(makeEvent(inAppOrgID, []string{inAppUser1}))

	// Mark one as read
	svc.MarkAsRead(created[0].ID, inAppOrgID, inAppUser1)

	// Unread should be 2
	unread := svc.List(inAppOrgID, inAppUser1, true, 0)
	if len(unread) != 2 {
		t.Errorf("expected 2 unread notifications, got %d", len(unread))
	}
}

func TestInAppService_List_WithLimit(t *testing.T) {
	svc := service.NewInAppService()

	for i := 0; i < 5; i++ {
		svc.Create(makeEvent(inAppOrgID, []string{inAppUser1}))
	}

	list := svc.List(inAppOrgID, inAppUser1, false, 3)
	if len(list) != 3 {
		t.Errorf("expected 3 notifications (limit), got %d", len(list))
	}
}

func TestInAppService_List_IsolatedByOrg(t *testing.T) {
	svc := service.NewInAppService()
	otherOrg := "org-other"

	svc.Create(makeEvent(inAppOrgID, []string{inAppUser1}))
	svc.Create(&model.NotificationEvent{
		EventType:      model.EventTaskAssigned,
		OrganizationID: otherOrg,
		RecipientIDs:   []string{inAppUser1},
		Subject:        "Other org notification",
		Body:           "Different org",
	})

	// User1 in inAppOrgID should only see their org's notifications
	list := svc.List(inAppOrgID, inAppUser1, false, 0)
	if len(list) != 1 {
		t.Errorf("expected 1 notification for org isolation, got %d", len(list))
	}
}

func TestInAppService_MarkAsRead(t *testing.T) {
	svc := service.NewInAppService()

	created := svc.Create(makeEvent(inAppOrgID, []string{inAppUser1}))
	id := created[0].ID

	err := svc.MarkAsRead(id, inAppOrgID, inAppUser1)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	// Verify it's read
	list := svc.List(inAppOrgID, inAppUser1, true, 0) // unread only
	for _, n := range list {
		if n.ID == id {
			t.Error("expected notification to be read, but found in unread list")
		}
	}
}

func TestInAppService_MarkAsRead_WrongUser(t *testing.T) {
	svc := service.NewInAppService()
	created := svc.Create(makeEvent(inAppOrgID, []string{inAppUser1}))

	err := svc.MarkAsRead(created[0].ID, inAppOrgID, inAppUser2)
	if err == nil {
		t.Error("expected error marking another user's notification as read")
	}
}

func TestInAppService_MarkAllAsRead(t *testing.T) {
	svc := service.NewInAppService()

	svc.Create(makeEvent(inAppOrgID, []string{inAppUser1}))
	svc.Create(makeEvent(inAppOrgID, []string{inAppUser1}))
	svc.Create(makeEvent(inAppOrgID, []string{inAppUser1}))

	count := svc.MarkAllAsRead(inAppOrgID, inAppUser1)
	if count != 3 {
		t.Errorf("expected 3 marked as read, got %d", count)
	}

	unreadCount := svc.UnreadCount(inAppOrgID, inAppUser1)
	if unreadCount != 0 {
		t.Errorf("expected 0 unread after mark all, got %d", unreadCount)
	}
}

func TestInAppService_Delete(t *testing.T) {
	svc := service.NewInAppService()

	created := svc.Create(makeEvent(inAppOrgID, []string{inAppUser1}))
	id := created[0].ID

	err := svc.Delete(id, inAppOrgID, inAppUser1)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	// Should not be in list anymore
	list := svc.List(inAppOrgID, inAppUser1, false, 0)
	for _, n := range list {
		if n.ID == id {
			t.Error("expected notification to be deleted")
		}
	}

	// Deleting again should error
	err = svc.Delete(id, inAppOrgID, inAppUser1)
	if err == nil {
		t.Error("expected error deleting non-existent notification")
	}
}

func TestInAppService_UnreadCount(t *testing.T) {
	svc := service.NewInAppService()

	svc.Create(makeEvent(inAppOrgID, []string{inAppUser1}))
	svc.Create(makeEvent(inAppOrgID, []string{inAppUser1}))

	count := svc.UnreadCount(inAppOrgID, inAppUser1)
	if count != 2 {
		t.Errorf("expected 2 unread, got %d", count)
	}

	// After marking all as read
	svc.MarkAllAsRead(inAppOrgID, inAppUser1)
	count = svc.UnreadCount(inAppOrgID, inAppUser1)
	if count != 0 {
		t.Errorf("expected 0 unread after mark all, got %d", count)
	}
}
