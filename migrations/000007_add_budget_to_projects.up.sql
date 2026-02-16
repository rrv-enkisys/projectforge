-- Migration: Add budget field to projects table
-- Description: Adds a budget column to track project budgets

-- Add budget column to projects table
ALTER TABLE projects
ADD COLUMN budget NUMERIC(15, 2) DEFAULT NULL;

-- Add comment for documentation
COMMENT ON COLUMN projects.budget IS 'Project budget in currency units (precision: 15 digits, scale: 2 decimals)';
