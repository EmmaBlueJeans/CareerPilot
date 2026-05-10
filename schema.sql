CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_token TEXT NOT NULL,
    title TEXT,
    resume_filename TEXT,
    resume_text TEXT,
    job_text TEXT,

    -- Stage 1: keyword scoring
    keyword_score INTEGER,

    -- Stage 2: AI four-dimension scoring
    ai_score INTEGER,
    required_score INTEGER,
    preferred_score INTEGER,
    required_matched INTEGER,
    required_total INTEGER,
    preferred_matched INTEGER,
    preferred_total INTEGER,

    -- Stage 2: skill lists (JSON arrays)
    matched_skills TEXT,
    missing_skills TEXT,
    implied_skills TEXT,
    required_present TEXT,
    required_missing TEXT,
    preferred_present TEXT,
    preferred_missing TEXT,

    -- Stage 2: ATS signals
    verdict TEXT,
    verdict_reason TEXT,
    formatting_flags TEXT,
    language_flags TEXT,
    title_alignment TEXT,
    experience_note TEXT,

    -- Stage 2: narrative fields
    ai_assessment TEXT,
    suggestions TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_token, created_at DESC);

CREATE TABLE IF NOT EXISTS interview_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON interview_messages(session_id, id);

CREATE TABLE IF NOT EXISTS interview_summary (
    session_id INTEGER PRIMARY KEY,
    summary TEXT,
    score INTEGER,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);