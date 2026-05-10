from flask import Blueprint, render_template, request, redirect, url_for, flash, g, abort
import db
import ai
import pdf_utils
import nlp_utils
import config

bp = Blueprint("screen", __name__)


@bp.route("/", methods=["GET"])
def new():
    return render_template("screen_new.html")


@bp.route("/", methods=["POST"])
def create():
    job_text = (request.form.get("job_text") or "").strip()
    title    = (request.form.get("title")    or "").strip() or None
    file     = request.files.get("resume")

    if not job_text:
        flash("Please paste a job description.", "error")
        return redirect(url_for("screen.new"))
    if not file or not file.filename:
        flash("Please upload a resume PDF.", "error")
        return redirect(url_for("screen.new"))
    if not file.filename.lower().endswith(".pdf"):
        flash("Resume must be a PDF.", "error")
        return redirect(url_for("screen.new"))

    try:
        resume_text = pdf_utils.extract_text(file)
    except pdf_utils.PDFExtractError as e:
        flash(str(e), "error")
        return redirect(url_for("screen.new"))

    if not resume_text:
        flash("Couldn't extract any text from that PDF. Make sure it isn't a scanned image.", "error")
        return redirect(url_for("screen.new"))

    # Stage 1 — keyword extraction
    resume_skills = nlp_utils.extract_skills(resume_text)
    job_skills    = nlp_utils.extract_skills(job_text)
    cmp_result    = nlp_utils.compare_skills(resume_skills, job_skills)

    # Stage 2 — LLM four-dimension enrichment (graceful fallback if AI unavailable)
    enriched = {
        "ai_score":          cmp_result["score"],
        "required_score":    0,
        "preferred_score":   0,
        "required_matched":  0,
        "required_total":    0,
        "preferred_matched": 0,
        "preferred_total":   0,
        "required_present":  [],
        "required_missing":  [],
        "preferred_present": [],
        "preferred_missing": [],
        "implied_skills":    [],
        "formatting_flags":  [],
        "language_flags":    [],
        "title_alignment":   "",
        "experience_note":   "",
        "verdict":           "unknown",
        "verdict_reason":    "AI analysis unavailable — keyword score shown only.",
        "ai_assessment":     "",
        "suggestions":       [],
    }

    if ai.is_configured():
        try:
            enriched = ai.enrich_screen(
                resume_text,
                job_text,
                cmp_result["score"],
                cmp_result["matched"],
                cmp_result["missing"],
            )
        except Exception as e:
            flash(f"AI analysis unavailable: {e}", "warning")

    session_id = db.create_session(g.user_token, {
        "title":             title or _derive_title(job_text),
        "resume_filename":   file.filename,
        "resume_text":       resume_text,
        "job_text":          job_text,
        # Stage 1
        "keyword_score":     cmp_result["score"],
        "matched_skills":    cmp_result["matched"],
        "missing_skills":    cmp_result["missing"],
        # Stage 2 scores
        "ai_score":          enriched["ai_score"],
        "required_score":    enriched["required_score"],
        "preferred_score":   enriched["preferred_score"],
        "required_matched":  enriched["required_matched"],
        "required_total":    enriched["required_total"],
        "preferred_matched": enriched["preferred_matched"],
        "preferred_total":   enriched["preferred_total"],
        # Stage 2 skill lists
        "required_present":  enriched["required_present"],
        "required_missing":  enriched["required_missing"],
        "preferred_present": enriched["preferred_present"],
        "preferred_missing": enriched["preferred_missing"],
        "implied_skills":    enriched["implied_skills"],
        # Stage 2 ATS signals
        "formatting_flags":  enriched["formatting_flags"],
        "language_flags":    enriched["language_flags"],
        "title_alignment":   enriched["title_alignment"],
        "experience_note":   enriched["experience_note"],
        # Stage 2 verdict + narrative
        "verdict":           enriched["verdict"],
        "verdict_reason":    enriched["verdict_reason"],
        "ai_assessment":     enriched["ai_assessment"],
        "suggestions":       enriched["suggestions"],
    })

    return redirect(url_for("screen.result", session_id=session_id))


@bp.route("/<int:session_id>")
def result(session_id):
    session = db.get_session(session_id, g.user_token)
    if not session:
        abort(404)
    summary   = db.get_summary(session_id)
    msg_count = db.message_count(session_id)
    return render_template(
        "screen_result.html",
        session=session,
        summary=summary,
        interview_started=msg_count > 0,
    )


def _derive_title(job_text):
    first_line = next((l.strip() for l in job_text.splitlines() if l.strip()), "")
    return (first_line[:60] + "...") if len(first_line) > 60 else (first_line or "Untitled session")