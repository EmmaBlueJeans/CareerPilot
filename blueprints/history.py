from flask import Blueprint, render_template, redirect, url_for, g, request
import db
from flask_login import login_required, current_user

bp = Blueprint("history", __name__)


@bp.route("/")
@login_required
def index():
    sessions = db.list_sessions(g.user_token, limit=200)
    return render_template("history.html", sessions=sessions)


@bp.route("/<int:session_id>/delete", methods=["POST"])
@login_required
def delete(session_id):
    db.delete_session(session_id, g.user_token)
    return redirect(url_for("history.index"))
