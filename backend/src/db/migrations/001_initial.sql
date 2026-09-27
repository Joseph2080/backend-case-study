-- Initial schema for the standalone CV workspace. Apply once to an empty database.
BEGIN;

CREATE TYPE cvlanguage AS ENUM ('en', 'de', 'fr', 'nl', 'es', 'sv', 'pl', 'it', 'ro', 'cs', 'pt', 'tr', 'uk', 'no', 'fi', 'da', 'sk', 'el', 'hu', 'bg', 'hr');


CREATE TYPE dateposition AS ENUM ('leading', 'trailing');

CREATE TYPE textalignment AS ENUM ('leading', 'justify');

CREATE TYPE cvattributeskilllevel AS ENUM ('novice', 'beginner', 'skillful', 'experienced', 'expert');

CREATE TYPE cvattributelanguagelevel AS ENUM ('A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'basic', 'elementary', 'intermediate', 'advanced', 'fluent', 'native', 'conversational', 'professional');

CREATE TYPE cvsectiontype AS ENUM ('employment', 'education', 'skills', 'languages', 'awards', 'hobbies', 'references', 'social_links', 'courses', 'extracurricular', 'custom');


CREATE TABLE cvs (
	id UUID NOT NULL,
	user_id VARCHAR NOT NULL,
	cv_name VARCHAR,
	cv_language cvlanguage NOT NULL,
	target_country_code VARCHAR,
	first_name VARCHAR NOT NULL,
	last_name VARCHAR NOT NULL,
	email VARCHAR,
	phone VARCHAR,
	street_address VARCHAR,
	city VARCHAR,
	state VARCHAR,
	postal_code VARCHAR,
	country VARCHAR,
	date_of_birth DATE,
	driving_license VARCHAR,
	place_of_birth VARCHAR,
	nationality VARCHAR,
	personal_website VARCHAR,
	marital_status VARCHAR,
	professional_title VARCHAR,
	professional_summary VARCHAR,
	privacy_clause_enabled BOOLEAN NOT NULL,
	signature_enabled BOOLEAN NOT NULL,
	signature_location VARCHAR,
	signature_include_date BOOLEAN NOT NULL,
	signature_show_name BOOLEAN NOT NULL,
	template_id VARCHAR,
	accent_color VARCHAR(7),
	section_spacing FLOAT,
	line_spacing FLOAT,
	margin_spacing FLOAT,
	date_position dateposition,
	text_alignment textalignment,
	font_size FLOAT,
	font_family VARCHAR(64),
	content_font_scale FLOAT,
	heading_font_scale FLOAT,
	parent_cv_id UUID,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT check_cvs_target_country_code_uppercase CHECK (target_country_code ~ '^[A-Z]{2}$'),
	FOREIGN KEY(parent_cv_id) REFERENCES cvs (id) ON DELETE SET NULL
);

CREATE INDEX ix_cvs_user_id ON cvs (user_id);


CREATE TABLE cv_sections (
	id UUID NOT NULL,
	cv_id UUID NOT NULL,
	type cvsectiontype NOT NULL,
	title VARCHAR,
	position INTEGER NOT NULL,
	text_content VARCHAR,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT unique_position_per_cv UNIQUE (cv_id, position) DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY(cv_id) REFERENCES cvs (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX ix_unique_standard_section_per_cv ON cv_sections (cv_id, type) WHERE type != 'custom';


CREATE TABLE cv_attributes (
	id UUID NOT NULL,
	section_id UUID NOT NULL,
	position INTEGER NOT NULL,
	name VARCHAR NOT NULL,
	value VARCHAR,
	skill_level cvattributeskilllevel,
	language_level cvattributelanguagelevel,
	skill_group_name VARCHAR,
	company_name VARCHAR,
	email VARCHAR,
	phone VARCHAR,
	url VARCHAR,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT unique_attribute_position_per_section UNIQUE (section_id, position) DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY(section_id) REFERENCES cv_sections (id) ON DELETE CASCADE
);

CREATE INDEX ix_cv_attributes_section_id ON cv_attributes (section_id);


CREATE TABLE cv_items (
	id UUID NOT NULL,
	section_id UUID NOT NULL,
	position INTEGER NOT NULL,
	title VARCHAR,
	organization VARCHAR,
	city VARCHAR,
	description VARCHAR,
	start_year INTEGER,
	start_month INTEGER,
	end_year INTEGER,
	end_month INTEGER,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT unique_item_position_per_section UNIQUE (section_id, position) DEFERRABLE INITIALLY DEFERRED,
	FOREIGN KEY(section_id) REFERENCES cv_sections (id) ON DELETE CASCADE
);

CREATE INDEX ix_cv_items_section_id ON cv_items (section_id);

COMMIT;
