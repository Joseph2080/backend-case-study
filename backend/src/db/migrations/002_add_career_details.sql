BEGIN;

CREATE TABLE career_details (
    cv_item_id UUID PRIMARY KEY REFERENCES cv_items(id) ON DELETE CASCADE,
    annual_salary BIGINT NOT NULL,
    salary_currency VARCHAR(3) NOT NULL,
    weekly_hours INTEGER NOT NULL,
    direct_reports INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

COMMIT;
