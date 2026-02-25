-- TOEFL 2026 Platform - Initial Database Schema
-- Target: PostgreSQL 15+

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- 1. USERS & AUTHENTICATION
-- ==========================================
CREATE TYPE user_role AS ENUM ('ADMIN', 'STUDENT', 'RATER', 'PROCTOR', 'ITEM_DESIGNER');

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role user_role NOT NULL DEFAULT 'STUDENT',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- ==========================================
-- 2. ITEM BANK & ASSESSMENT CONTENT
-- ==========================================
CREATE TYPE section_type AS ENUM ('READING', 'LISTENING', 'SPEAKING', 'WRITING');
CREATE TYPE cefr_level AS ENUM ('A1', 'A2', 'B1', 'B2', 'C1', 'C2');
CREATE TYPE task_type AS ENUM (
    'READ_ACADEMIC_PASSAGE', 'READ_IN_DAILY_LIFE', 'COMPLETE_THE_WORDS',
    'BUILD_A_SENTENCE', 'WRITE_ACADEMIC_DISCUSSION', 'WRITE_AN_EMAIL',
    'TAKE_AN_INTERVIEW'
);

CREATE TABLE test_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    author_id UUID REFERENCES users(id),
    section section_type NOT NULL,
    task_type task_type,                       -- item subtype within section
    target_level cefr_level NOT NULL,
    irt_difficulty DECIMAL(5,2) DEFAULT 0.0, -- Item Response Theory difficulty parameter
    irt_discrimination DECIMAL(5,2) DEFAULT 1.0, -- IRT discrimination parameter
    prompt_content TEXT, -- Markdown or JSON blocks
    media_url VARCHAR(500), -- Audio/Video S3 URL for listening/speaking
    rubric_id UUID,
    is_active BOOLEAN DEFAULT FALSE,
    -- Version / Audit Trail
    version INT NOT NULL DEFAULT 1,
    generated_by_model VARCHAR(100), -- e.g. 'MiniMax-M2.5', 'Human', 'GPT-4o'
    generation_notes TEXT, -- Free-text QA notes or change description
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Exposure / Burn-Rate Tracking
    exposure_count INT NOT NULL DEFAULT 0,
    last_exposed_at TIMESTAMP WITH TIME ZONE,
    -- Import Traceability
    source_file VARCHAR(255),
    source_id VARCHAR(100)
);

CREATE TABLE choices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID REFERENCES test_items(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE,
    sequence_order INT NOT NULL
);

-- ==========================================
-- 3. TEST SESSIONS & PROCTORING
-- ==========================================
CREATE TYPE session_status AS ENUM ('SCHEDULED', 'ACTIVE', 'COMPLETED', 'FLAGGED', 'VOIDED');

CREATE TABLE test_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID REFERENCES users(id),
    proctor_id UUID REFERENCES users(id),
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    status session_status DEFAULT 'SCHEDULED',
    browser_fingerprint VARCHAR(255),
    ip_address INET,
    total_score INT
);

CREATE TABLE session_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES test_sessions(id) ON DELETE CASCADE,
    item_id UUID REFERENCES test_items(id),
    selected_choice_id UUID REFERENCES choices(id), -- For multiple choice
    text_response TEXT, -- For writing
    audio_s3_key VARCHAR(500), -- For speaking
    time_spent_ms INT NOT NULL,
    ai_score DECIMAL(5,2),
    human_score DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 4. SCORING & RUBRICS
-- ==========================================
CREATE TABLE rubrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    section section_type NOT NULL,
    max_score INT NOT NULL
);

-- Indexes for performance
CREATE INDEX idx_test_items_section ON test_items(section, target_level);
CREATE INDEX idx_session_responses_session ON session_responses(session_id);
