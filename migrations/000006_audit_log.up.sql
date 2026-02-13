-- Audit log table for tracking all changes
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,  -- CREATE, UPDATE, DELETE, etc.
    entity_type VARCHAR(100) NOT NULL,  -- projects, tasks, users, etc.
    entity_id UUID NOT NULL,
    changes JSONB DEFAULT '{}',  -- Before/after values
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_log_organization_id ON audit_log(organization_id);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at DESC);
CREATE INDEX idx_audit_log_org_created ON audit_log(organization_id, created_at DESC);

-- GIN index for JSONB queries on changes field
CREATE INDEX idx_audit_log_changes ON audit_log USING GIN (changes);

-- Enable RLS on audit log
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_audit_log ON audit_log
    USING (organization_id = current_setting('app.current_organization_id')::uuid);

-- Function to automatically log changes (optional, can be used with triggers)
CREATE OR REPLACE FUNCTION log_audit_change()
RETURNS TRIGGER AS $$
DECLARE
    org_id UUID;
    changes_json JSONB;
BEGIN
    -- Get organization_id from the record
    IF TG_OP = 'DELETE' THEN
        org_id := OLD.organization_id;
        changes_json := jsonb_build_object('old', row_to_json(OLD));
    ELSIF TG_OP = 'INSERT' THEN
        org_id := NEW.organization_id;
        changes_json := jsonb_build_object('new', row_to_json(NEW));
    ELSE -- UPDATE
        org_id := NEW.organization_id;
        changes_json := jsonb_build_object(
            'old', row_to_json(OLD),
            'new', row_to_json(NEW)
        );
    END IF;

    -- Insert audit log entry
    INSERT INTO audit_log (
        organization_id,
        action,
        entity_type,
        entity_id,
        changes
    ) VALUES (
        org_id,
        TG_OP,
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        changes_json
    );

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Example: Enable audit logging on projects table
-- Uncomment to enable audit logging
-- CREATE TRIGGER audit_projects
--     AFTER INSERT OR UPDATE OR DELETE ON projects
--     FOR EACH ROW
--     EXECUTE FUNCTION log_audit_change();
