
from flask import Flask, render_template
from config import Config
from extensions import db

from routes.auth import auth_bp
from routes.profile import profile_bp
from routes.posts import posts_bp
from routes.connections import connections_bp
from routes.main import main_bp

import models


def create_app(test_config=None):
    app = Flask(__name__)

    # Load the normal application configuration
    app.config.from_object(Config)

    # Apply optional overrides before initializing the database
    if test_config:
        app.config.update(test_config)

    # Initialize database
    db.init_app(app)

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

    # Create database tables if they do not exist
    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
