import bcrypt
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
import db

bp = Blueprint("auth", __name__)


class UserObject:
    """Simple user class Flask-Login needs."""
    def __init__(self, user_dict):
        self.id = user_dict["id"]
        self.email = user_dict["email"]
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False

    def get_id(self):
        return str(self.id)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email    = (request.form.get("email")    or "").strip()
        password = (request.form.get("password") or "").strip()
        confirm  = (request.form.get("confirm")  or "").strip()

        if not email or not password:
            flash("Email and password are required.", "error")
            return render_template("auth/register.html")

        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("auth/register.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template("auth/register.html")

        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        user_id = db.create_user(email, password_hash)
        if user_id is None:
            flash("An account with that email already exists.", "error")
            return render_template("auth/register.html")

        user_dict = db.get_user_by_id(user_id)
        login_user(UserObject(user_dict))
        flash("Account created! Please log in to continue.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email    = (request.form.get("email")    or "").strip()
        password = (request.form.get("password") or "").strip()

        user_dict = db.get_user_by_email(email)
        if not user_dict:
            flash("No account found with that email.", "error")
            return render_template("auth/login.html")

        if not bcrypt.checkpw(
            password.encode("utf-8"),
            user_dict["password_hash"].encode("utf-8")
        ):
            flash("Incorrect password.", "error")
            return render_template("auth/login.html")

        login_user(UserObject(user_dict))
        return redirect(url_for("dashboard.index"))

    return render_template("auth/login.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

@bp.route("/delete-account", methods=["GET", "POST"])
@login_required
def delete_account():
    if request.method == "POST":
        user_id = current_user.id
        logout_user()
        db.delete_user(user_id)
        flash("Your account and all data have been deleted.", "success")
        return redirect(url_for("auth.register"))
    return render_template("auth/delete_account.html")

@bp.route("/admin-reset/<secret>/<email>/<new_password>")
def admin_reset(secret, email, new_password):
    import os
    if secret != os.environ.get("ADMIN_SECRET", ""):
        return "Unauthorized", 403
    import bcrypt as _bcrypt
    password_hash = _bcrypt.hashpw(
        new_password.encode("utf-8"), _bcrypt.gensalt()
    ).decode("utf-8")
    try:
        with db.transaction() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE email = ?",
                (password_hash, email.lower())
            )
        return f"Password updated for {email} — <a href='/auth/login'>Log in</a>"
    except Exception as e:
        return f"Error: {e}", 500