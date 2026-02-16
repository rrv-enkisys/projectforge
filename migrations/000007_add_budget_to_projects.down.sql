-- Migration: Rollback budget field from projects table
-- Description: Removes the budget column from projects table

-- Remove budget column
ALTER TABLE projects
DROP COLUMN IF EXISTS budget;
