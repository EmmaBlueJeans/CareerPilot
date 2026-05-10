import uuid
from flask import Flask, g, request
import config
import db
from blueprints.dashboard import bp as dashboard_bp
from blueprints.screen import bp as screen_bp
from blueprints.interview import bp as interview_bp
from blueprints.history import bp as history_bp


def create_app():
    app = Flask(__name__, instance_path=str(config.INSTANCE_DIR))
    app.config["SECRET_KEY"] = config.FLASK_SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_PDF_BYTES + 1024 * 1024

    db.init_db()
    app.teardown_appcontext(db.close_conn)

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(screen_bp, url_prefix="/screen")
    app.register_blueprint(interview_bp, url_prefix="/interview")
    app.register_blueprint(history_bp, url_prefix="/history")

    @app.before_request
    def ensure_user_token():
        token = request.cookies.get("cp_user")
        if not token:
            token = uuid.uuid4().hex
        g.user_token = token
        g.is_new_user = not request.cookies.get("cp_user")

    @app.after_request
    def set_user_cookie(response):
        if getattr(g, "is_new_user", False):
            response.set_cookie(
                "cp_user", g.user_token,
                max_age=60 * 60 * 24 * 365,
                httponly=True, samesite="Lax",
            )
        return response

    @app.context_processor
    def inject_globals():
        import ai
        return {
            "ai_configured": ai.is_configured(),
            "app_name": "CareerPilot",
        }

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
