import sqlite3
import json
from contextlib import contextmanager
from flask import g
import config


def get_conn():
    if "db" not in g:
        conn = sqlite3.connect(config.DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def close_conn(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(config.DB_PATH) as conn:
        with open(config.BASE_DIR / "schema.sql") as f:
            conn.executescript(f.read())


@contextmanager
def transaction():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def create_session(user_token, payload):
    with transaction() as conn:
        cur = conn.execute(
            """INSERT INTO sessions (
                user_token, title, resume_filename, resume_text, job_text,
                keyword_score,
                ai_score, required_score, preferred_score,
                required_matched, required_total,
                preferred_matched, preferred_total,
                matched_skills, missing_skills,
                required_present, required_missing,
                preferred_present, preferred_missing,
                implied_skills,
                formatting_flags, language_flags,
                title_alignment, experience_note,
                verdict, verdict_reason,
                ai_assessment, suggestions
            ) VALUES (
                ?, ?, ?, ?, ?,
                ?,
                ?, ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?
            )""",
            (
                user_token,
                payload.get("title"),
                payload.get("resume_filename"),
                payload.get("resume_text"),
                payload.get("job_text"),
                # Stage 1
                payload.get("keyword_score"),
                # Stage 2 scores
                payload.get("ai_score"),
                payload.get("required_score"),
                payload.get("preferred_score"),
                payload.get("required_matched"),
                payload.get("required_total"),
                payload.get("preferred_matched"),
                payload.get("preferred_total"),
                # Skill lists (JSON)
                json.dumps(payload.get("matched_skills")    or []),
                json.dumps(payload.get("missing_skills")    or []),
                json.dumps(payload.get("required_present")  or []),
                json.dumps(payload.get("required_missing")  or []),
                json.dumps(payload.get("preferred_present") or []),
                json.dumps(payload.get("preferred_missing") or []),
                json.dumps(payload.get("implied_skills")    or []),
                # ATS signals (JSON for lists, text for strings)
                json.dumps(payload.get("formatting_flags")  or []),
                json.dumps(payload.get("language_flags")    or []),
                payload.get("title_alignment"),
                payload.get("experience_note"),
                # Verdict
                payload.get("verdict"),
                payload.get("verdict_reason"),
                # Narrative
                payload.get("ai_assessment"),
                json.dumps(payload.get("suggestions")       or []),
            ),
        )
        return cur.lastrowid


def get_session(session_id, user_token):
    row = get_conn().execute(
        "SELECT * FROM sessions WHERE id = ? AND user_token = ?",
        (session_id, user_token),
    ).fetchone()
    return _hydrate_session(row) if row else None


def list_sessions(user_token, limit=50):
    rows = get_conn().execute(
        """SELECT s.*, sm.score AS interview_score, sm.completed_at AS interview_completed_at
           FROM sessions s
           LEFT JOIN interview_summary sm ON sm.session_id = s.id
           WHERE s.user_token = ?
           ORDER BY s.created_at DESC
           LIMIT ?""",
        (user_token, limit),
    ).fetchall()
    return [_hydrate_session(r) for r in rows]


def delete_session(session_id, user_token):
    with transaction() as conn:
        conn.execute(
            "DELETE FROM sessions WHERE id = ? AND user_token = ?",
            (session_id, user_token),
        )


def add_message(session_id, role, content):
    with transaction() as conn:
        conn.execute(
            "INSERT INTO interview_messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )


def get_messages(session_id):
    rows = get_conn().execute(
        "SELECT role, content, created_at FROM interview_messages WHERE session_id = ? ORDER BY id ASC",
        (session_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def message_count(session_id):
    return get_conn().execute(
        "SELECT COUNT(*) FROM interview_messages WHERE session_id = ?",
        (session_id,),
    ).fetchone()[0]


def save_summary(session_id, summary, score):
    with transaction() as conn:
        conn.execute(
            """INSERT INTO interview_summary (session_id, summary, score)
               VALUES (?, ?, ?)
               ON CONFLICT(session_id) DO UPDATE SET
                   summary = excluded.summary,
                   score = excluded.score,
                   completed_at = CURRENT_TIMESTAMP""",
            (session_id, summary, score),
        )


def get_summary(session_id):
    row = get_conn().execute(
        "SELECT summary, score, completed_at FROM interview_summary WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    return dict(row) if row else None


# JSON fields that need deserializing when reading from DB
_JSON_FIELDS = (
    "matched_skills", "missing_skills",
    "required_present", "required_missing",
    "preferred_present", "preferred_missing",
    "implied_skills",
    "formatting_flags", "language_flags",
    "suggestions",
)


def _hydrate_session(row):
    if not row:
        return None
    d = dict(row)
    for key in _JSON_FIELDS:
        try:
            d[key] = json.loads(d.get(key) or "[]")
        except (TypeError, json.JSONDecodeError):
            d[key] = []
    return d