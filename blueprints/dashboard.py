from flask import Blueprint, render_template, g
from flask_login import login_required, current_user
import db

bp = Blueprint("dashboard", __name__)


@bp.route("/")
@login_required
def index():
    sessions = db.list_sessions(g.user_token, user_id=current_user.id)
    return render_template("dashboard.html", sessions=sessions)
