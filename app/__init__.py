import os

import markdown
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"


def create_app():
    app = Flask(__name__)

    UPLOAD_FOLDER = os.path.join(app.root_path, "uploads")

    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

    app.config.from_object("config.Config")

    @app.template_filter("markdown")
    def markdown_filter(text):
        if not text:
            return ""
        return markdown.markdown(
            text,
            extensions=["nl2br", "fenced_code", "tables"]
        )

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from .routes import main
    from .auth import auth

    app.register_blueprint(main)
    app.register_blueprint(auth)

    return app