from flask import Blueprint, render_template, request, jsonify, redirect, url_for, g, abort
import db
import ai
import config

bp = Blueprint("interview", __name__)


@bp.route("/<int:session_id>")
def chat(session_id):
    session = db.get_session(session_id, g.user_token)
    if not session:
        abort(404)
    messages = db.get_messages(session_id)
    summary = db.get_summary(session_id)
    return render_template(
        "interview.html",
        session=session,
        messages=messages,
        summary=summary,
        question_target=config.INTERVIEW_QUESTION_COUNT,
    )


@bp.route("/<int:session_id>/start", methods=["POST"])
def start(session_id):
    session = db.get_session(session_id, g.user_token)
    if not session:
        abort(404)
    if not ai.is_configured():
        return jsonify({"error": "AI is not configured. Add ANTHROPIC_API_KEY to .env."}), 500

    if db.message_count(session_id) > 0:
        return jsonify({"messages": db.get_messages(session_id)})

    try:
        opener = ai.interview_reply(session, history=[])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    db.add_message(session_id, "assistant", opener)
    return jsonify({"messages": db.get_messages(session_id)})


@bp.route("/<int:session_id>/message", methods=["POST"])
def send(session_id):
    session = db.get_session(session_id, g.user_token)
    if not session:
        abort(404)
    if not ai.is_configured():
        return jsonify({"error": "AI is not configured."}), 500

    data = request.get_json(silent=True) or {}
    user_msg = (data.get("message") or "").strip()
    if not user_msg:
        return jsonify({"error": "Empty message."}), 400

    db.add_message(session_id, "user", user_msg)
    history = db.get_messages(session_id)

    assistant_question_count = sum(1 for m in history if m["role"] == "assistant")

    try:
        if assistant_question_count >= config.INTERVIEW_QUESTION_COUNT:
            wrap = ai.interview_reply(session, history=history, conclude=True)
            db.save_summary(session_id, wrap["summary"], wrap["score"])
            db.add_message(
                session_id, "assistant",
                f"Thanks — that wraps up the interview.\n\n**Summary:** {wrap['summary']}\n\n**Score:** {wrap['score']}/10",
            )
            return jsonify({
                "messages": db.get_messages(session_id),
                "concluded": True,
                "summary": wrap["summary"],
                "score": wrap["score"],
            })

        reply = ai.interview_reply(session, history=history, user_message=None)
        db.add_message(session_id, "assistant", reply)
        return jsonify({"messages": db.get_messages(session_id), "concluded": False})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/<int:session_id>/reset", methods=["POST"])
def reset(session_id):
    session = db.get_session(session_id, g.user_token)
    if not session:
        abort(404)
    conn = db.get_conn()
    with db.transaction() as c:
        c.execute("DELETE FROM interview_messages WHERE session_id = ?", (session_id,))
        c.execute("DELETE FROM interview_summary WHERE session_id = ?", (session_id,))
    return redirect(url_for("interview.chat", session_id=session_id))
