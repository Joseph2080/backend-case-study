BEGIN;

-- Idempotent migration for sharing career details across matching employment items.
-- Safe if work_experiences was already created by SQLModel create_all.

CREATE TABLE IF NOT EXISTS work_experiences (
    id UUID PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_work_experiences_user_id ON work_experiences (user_id);

ALTER TABLE cv_items
    ADD COLUMN IF NOT EXISTS work_experience_id UUID REFERENCES work_experiences (id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_cv_items_work_experience_id ON cv_items (work_experience_id);

-- Only rebuild career_details when it is still on the old cv_item_id schema.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'career_details' AND column_name = 'cv_item_id'
    ) THEN
        CREATE TEMP TABLE career_details_migration AS
        SELECT
            career_details.cv_item_id,
            gen_random_uuid() AS work_experience_id,
            career_details.annual_salary,
            career_details.salary_currency,
            career_details.weekly_hours,
            career_details.direct_reports,
            career_details.created_at,
            career_details.updated_at,
            cvs.user_id
        FROM career_details
        JOIN cv_items ON cv_items.id = career_details.cv_item_id
        JOIN cv_sections ON cv_sections.id = cv_items.section_id
        JOIN cvs ON cvs.id = cv_sections.cv_id;

        INSERT INTO work_experiences (id, user_id, created_at, updated_at)
        SELECT m.work_experience_id, m.user_id, m.created_at, m.updated_at
        FROM career_details_migration m;

        CREATE TABLE career_details_shared (
            work_experience_id UUID PRIMARY KEY REFERENCES work_experiences (id) ON DELETE CASCADE,
            annual_salary BIGINT NOT NULL,
            salary_currency VARCHAR(3) NOT NULL,
            weekly_hours INTEGER NOT NULL,
            direct_reports INTEGER NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
        );

        INSERT INTO career_details_shared (
            work_experience_id,
            annual_salary,
            salary_currency,
            weekly_hours,
            direct_reports,
            created_at,
            updated_at
        )
        SELECT
            work_experience_id,
            annual_salary,
            salary_currency,
            weekly_hours,
            direct_reports,
            created_at,
            updated_at
        FROM career_details_migration;

        UPDATE cv_items
        SET work_experience_id = career_details_migration.work_experience_id
        FROM career_details_migration
        WHERE cv_items.id = career_details_migration.cv_item_id;

        DROP TABLE career_details;
        ALTER TABLE career_details_shared RENAME TO career_details;
    END IF;
END $$;

COMMIT;
