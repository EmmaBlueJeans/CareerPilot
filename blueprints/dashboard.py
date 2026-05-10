from flask import Blueprint, render_template, g
import db

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    sessions = db.list_sessions(g.user_token, limit=6)
    return render_template("dashboard.html", sessions=sessions)
