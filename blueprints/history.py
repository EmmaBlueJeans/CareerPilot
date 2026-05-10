from flask import Blueprint, render_template, redirect, url_for, g, request
import db

bp = Blueprint("history", __name__)


@bp.route("/")
def index():
    sessions = db.list_sessions(g.user_token, limit=200)
    return render_template("history.html", sessions=sessions)


@bp.route("/<int:session_id>/delete", methods=["POST"])
def delete(session_id):
    db.delete_session(session_id, g.user_token)
    return redirect(url_for("history.index"))
