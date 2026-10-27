# CareerPilot

An end-to-end career preparation tool: AI-powered resume screening and tailored mock interview practice in a single Flask app.

**Live application:** [careerpilot-9wif.onrender.com](https://careerpilot-9wif.onrender.com/)

---

## What it does

1. **Screen** — Upload a resume PDF and paste a job description. CareerPilot runs a two-stage analysis: keyword extraction followed by Claude AI four-dimension scoring. You get a plain-language ATS verdict, a breakdown of required versus preferred skills, formatting warnings, language-quality feedback with before-and-after rewrites, and prioritized improvement suggestions.
2. **Interview** — After screening, continue directly to a mock interview. The AI interviewer already has your resume, the job description, and the skill gaps the screener identified—no re-uploading. After a set number of questions, you receive a written summary and a score out of 10.
3. **History** — Sessions are saved to your account. Revisit past screenings or continue a previous interview from the History page.

---

## How the screening works

Screening uses a two-stage pipeline:

**Stage 1 — Keyword extraction** uses a curated skill list with weighted scoring to produce a fast, deterministic baseline match. Skills are normalized across common variants (for example, `postgresql → sql` and `powerbi → power bi`).

**Stage 2 — Claude AI analysis** receives the resume, job description, and Stage 1 results and performs four analytical tasks:

- **Skill classification** — Every skill in the job description is classified as required or preferred based on the surrounding language. Required skills are weighted at 70% of the final score and preferred skills at 30%. Implied skills—demonstrated in context without the exact keyword—are also flagged.
- **Formatting check** — Detects potential ATS issues such as multi-column layouts, tables, or missing standard sections.
- **Title and experience alignment** — Compares the candidate's most recent role and total experience against the job description's stated requirements.
- **Language quality** — Identifies weak verbs, unquantified bullets, and vague descriptions, with specific before-and-after rewrites for impactful issues.

The model runs at `temperature=0` for consistency and is instructed not to classify eligibility requirements such as citizenship, security clearance, or degree requirements as skills.

---

## Stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.11, Flask, Gunicorn |
| AI | Anthropic Claude API — Sonnet 4.6 for screening, Haiku 4.5 for interviews |
| NLP | Regex-based keyword matching; spaCy optional for local development |
| PDF | pdfplumber |
| Database | SQLite via Python `sqlite3` |
| Authentication | Flask-Login with bcrypt password hashing |
| Frontend | Jinja2 templates, vanilla JavaScript, custom CSS with dark/light mode |
| Hosting | Render — [careerpilot-9wif.onrender.com](https://careerpilot-9wif.onrender.com/) |

---

## Project layout

```text
CareerPilot/
├── app.py                  # Flask app factory — registers all blueprints
├── config.py               # Configuration — reads environment variables
├── db.py                   # SQLite database operations
├── ai.py                   # Claude API calls for screening and interviews
├── pdf_utils.py            # PDF text extraction via pdfplumber
├── nlp_utils.py            # Keyword matching and weighted scoring
├── schema.sql              # Database schema — four tables
├── blueprints/
│   ├── auth.py             # Registration, login, logout, account deletion
│   ├── dashboard.py        # / — dashboard and recent sessions
│   ├── screen.py           # /screen — resume upload, analysis, results
│   ├── interview.py        # /interview — mock interview chat
│   └── history.py          # /history — session history
├── templates/
│   ├── base.html           # Shared layout, navigation, theme toggle
│   ├── auth/               # Login, registration, account-deletion pages
│   ├── dashboard.html
│   ├── screen_new.html
│   ├── screen_result.html
│   ├── interview.html
│   └── history.html
├── static/
│   ├── css/style.css       # Design system and dark/light themes
│   └── js/
│       ├── interview.js    # Interview chat behavior
│       └── screen.js       # Screening form and loading-state behavior
├── Procfile                # Render start command
├── requirements.txt        # Python dependencies
└── .python-version         # Pins Python 3.11 for Render
```

---

## Engineering decisions

Several technical decisions were shaped by integration, hosting, and project-timeline constraints:

**Integration architecture** — Tanzul's interview project was already structured as a Flask app factory with blueprints, making it the natural base for the merge. Emma's resume screener was restructured to fit that pattern rather than the reverse. This kept the combined codebase coherent but required retrofitting authentication, database schema changes, and session ownership after integration was underway.

**spaCy to regex fallback on Render** — The original screener used spaCy's `PhraseMatcher` for skill extraction. Although the language model worked locally, it exceeded the memory available on Render's free tier during screening requests. The `DISABLE_SPACY` environment variable now selects a regex-based fallback at runtime, allowing production to remain within its memory limit while keeping spaCy available as an optional local-development path.

**Claude prompt engineering** — Producing consistent structured JSON required several prompt iterations. Important decisions included setting `temperature=0`, placing the job description before the resume to reduce classification drift, and explicitly excluding eligibility gates—such as citizenship, security clearance, degree requirements, and minimum years of experience—from skill scoring.

**SQLite on ephemeral storage** — Render's free tier does not guarantee filesystem persistence across restarts or deployments. Rather than migrate databases during the Capstone timeline, the team accepted SQLite as a documented prototype constraint. The tradeoff is that account and session data can be lost; migration to Supabase or Render PostgreSQL is the identified next step.

**Authentication added mid-project** — Flask-Login was added after the core screening and interview features were working. The retrofit introduced a users table, password hashing, protected routes, account deletion, and user linkage for saved sessions. The retrofit also exposed an inconsistency between the original anonymous browser-token ownership model and authenticated user IDs. Session authorization now consistently uses authenticated user IDs, while the legacy token column remains temporarily for schema compatibility. The central lesson was that authentication and data ownership are easier to design from the beginning than to retrofit later.

---

## Local setup

**Prerequisites:** Python 3.11+

```bash
git clone https://github.com/EmmaBlueJeans/CareerPilot.git
cd CareerPilot
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate         # Windows

pip install -r requirements.txt

cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY and FLASK_SECRET_KEY

python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). You will be prompted to create an account.

spaCy is not installed by the project requirements. To use it for local development, install spaCy and its language model separately and leave `DISABLE_SPACY` unset. Otherwise, CareerPilot uses its regex-based fallback.

---

## Environment variables

| Variable | Required | Description |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | Yes for AI features | Anthropic Console API key |
| `FLASK_SECRET_KEY` | Yes | Long random string used for session security |
| `DISABLE_SPACY` | Optional | Set to `1` to use regex matching instead of spaCy; used on Render to stay within memory limits |

---

## Deployment

CareerPilot is deployed on Render's free tier.

- **Start command:** `gunicorn --timeout 120 --workers 1 "app:create_app()"`
- **Python version:** 3.11, pinned through `.python-version`
- Environment variables are configured in the Render dashboard and are never committed to the repository.

**Known limitation:** Render's free tier uses an ephemeral filesystem, so the SQLite database may reset when the service is restarted or redeployed. Migrating to a hosted database such as Render PostgreSQL or Supabase is a planned improvement.

---

## Authentication and privacy

Core application features require an authenticated user account. Passwords are hashed with bcrypt and are not stored in plain text. The Anthropic API key remains on the server and is never sent to the browser.

CareerPilot extracts text from uploaded resume PDFs; the original PDF file is not retained. Extracted resume text and job descriptions are stored in the application's SQLite database and sent to the Anthropic API when AI analysis or interview coaching is requested.

Because the Render deployment currently uses an ephemeral SQLite database, account and session data may be erased when the service is restarted or redeployed.

---

## Built for Capstone II

CareerPilot was developed for Capstone II in the Edmonds College Bachelor of Applied Science in Information Technology — Application Development program.

The project combines two earlier Capstone I tools. The resume-screening MVP was originally developed by Emma Dennis with a Capstone I teammate, while the AI interview coach was created by Tanzul Rajput. During Capstone II, Emma and Tanzul integrated the tools into one Flask application that carries resume and job-description context from screening into tailored interview practice.
