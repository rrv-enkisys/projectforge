-- Email templates table
CREATE TABLE email_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    trigger_type trigger_type NOT NULL,
    subject_template TEXT NOT NULL,
    body_template TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_email_templates_organization_id ON email_templates(organization_id);
CREATE INDEX idx_email_templates_trigger_type ON email_templates(organization_id, trigger_type);
CREATE INDEX idx_email_templates_is_active ON email_templates(is_active);

CREATE TRIGGER update_email_templates_updated_at
    BEFORE UPDATE ON email_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Notification log table
CREATE TABLE notification_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    type trigger_type NOT NULL,
    recipient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    template_id UUID REFERENCES email_templates(id) ON DELETE SET NULL,
    status notification_status NOT NULL DEFAULT 'pending',
    sent_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notification_log_organization_id ON notification_log(organization_id);
CREATE INDEX idx_notification_log_recipient_id ON notification_log(recipient_id);
CREATE INDEX idx_notification_log_status ON notification_log(status);
CREATE INDEX idx_notification_log_type ON notification_log(type);
CREATE INDEX idx_notification_log_created_at ON notification_log(created_at DESC);
CREATE INDEX idx_notification_log_task_id ON notification_log(task_id) WHERE task_id IS NOT NULL;
CREATE INDEX idx_notification_log_project_id ON notification_log(project_id) WHERE project_id IS NOT NULL;

CREATE TRIGGER update_notification_log_updated_at
    BEFORE UPDATE ON notification_log
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Notification preferences table
CREATE TABLE notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email_enabled BOOLEAN NOT NULL DEFAULT true,
    slack_enabled BOOLEAN NOT NULL DEFAULT false,
    teams_enabled BOOLEAN NOT NULL DEFAULT false,
    triggers JSONB NOT NULL DEFAULT '{}',  -- JSON object with trigger_type as keys and boolean as values
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, organization_id)
);

CREATE INDEX idx_notification_preferences_user_id ON notification_preferences(user_id);
CREATE INDEX idx_notification_preferences_organization_id ON notification_preferences(organization_id);

CREATE TRIGGER update_notification_preferences_updated_at
    BEFORE UPDATE ON notification_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable RLS on notification tables
ALTER TABLE email_templates ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_email_templates ON email_templates
    USING (organization_id = current_setting('app.current_organization_id')::uuid);

ALTER TABLE notification_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_notification_log ON notification_log
    USING (organization_id = current_setting('app.current_organization_id')::uuid);

ALTER TABLE notification_preferences ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_notification_preferences ON notification_preferences
    USING (organization_id = current_setting('app.current_organization_id')::uuid);
