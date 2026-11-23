
from flask import Flask, render_template
from config import Config
from extensions import db, migrate, csrf
from image_storage import get_image_url

from routes.auth import auth_bp
from routes.profile import profile_bp
from routes.posts import posts_bp
from routes.connections import connections_bp
from routes.main import main_bp

import models


def create_app(test_config=None):
    app = Flask(__name__)

    # Load application configuration
    app.config.from_object(Config)

    # Apply optional test configuration
    if test_config:
        app.config.update(test_config)

    # Make image URL helper available in all Jinja templates
    app.jinja_env.globals["get_image_url"] = get_image_url

    # Initialize database, migrations and CSRF protection
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Register application routes
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(connections_bp)
    app.register_blueprint(main_bp)

    # Home page
    @app.route("/")
    def home():
        return render_template("index.html")

    # Create database tables automatically only when enabled
    if app.config.get("AUTO_CREATE_DB", True):
        with app.app_context():
            db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", False))
