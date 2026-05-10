# CareerPilot

An end-to-end career assistant: resume screening + tailored mock interview practice in a single Flask app.

## What it does

1. **Screen** — upload a resume PDF, paste a job description, get an AI-augmented match score, matched/missing skills, and concrete improvement suggestions.
2. **Interview** — practice a mock interview tuned to *your* resume, the JD, and the gaps the screener found. Get a final summary and 0-10 score.
3. **History** — every session is saved locally (SQLite). Revisit any past screening or interview.

Built for Capstone II by combining two Capstone I projects (Resume Screener + Resume Bot) into one cohesive product.

## Stack

- Flask + blueprints (single app, three feature areas)
- SQLite (local, file-based — `instance/careerpilot.db`)
- Anthropic Claude (Sonnet 4.6 for screening, Haiku 4.5 for interview chat)
- pdfplumber + spaCy (skill extraction)
- Vanilla HTML/CSS/JS frontend (no build step)

## Setup

```bash
cd CareerPilot
python -m venv .venv
source .venv/bin/activate         # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Create `.env` from the example and add your key:

```bash
cp .env.example .env
# then edit .env to set ANTHROPIC_API_KEY=sk-ant-...
```

## Run

```bash
python app.py
```

Open http://127.0.0.1:5000

## Project layout

```
CareerPilot/
├── app.py                  # Flask app factory + cookie-based user identity
├── config.py               # env loading + model selection
├── db.py                   # SQLite helpers (sessions, messages, summaries)
├── ai.py                   # Anthropic SDK wrapper (screening + interview)
├── pdf_utils.py            # PDF text extraction
├── nlp_utils.py            # spaCy skill matching + weighted score
├── schema.sql              # DB schema
├── blueprints/
│   ├── dashboard.py        # /
│   ├── screen.py           # /screen
│   ├── interview.py        # /interview/<id>
│   └── history.py          # /history
├── templates/              # Jinja2 templates with shared base.html
├── static/
│   ├── css/style.css       # design system (dark, indigo→purple gradient)
│   └── js/                 # screen.js, interview.js
└── instance/               # SQLite DB lives here (gitignored)
```

## User flow

1. Land on **Dashboard** → see recent sessions.
2. Click **Start a new screen** → upload resume, paste JD.
3. Submit → see **screening result** (AI score, keyword score, matched/missing/implied skills, AI assessment, suggestions).
4. Click **Practice interview** → chat with an interviewer that already knows your resume and the JD.
5. After ~5 questions, the interview wraps with a written summary and a 0-10 score.
6. Everything persists in **History**.

## Identity / privacy

- No login. Each browser gets an anonymous cookie (`cp_user`) that scopes all DB rows.
- Resumes and chat live only on this device's SQLite file.
- API key is server-side only — never sent to the browser.

## Notes

- If `ANTHROPIC_API_KEY` is missing, screening still runs the keyword-based score; the AI assessment / interview features are disabled until configured.
- Models can be swapped in `config.py` (`SCREEN_MODEL`, `INTERVIEW_MODEL`).
