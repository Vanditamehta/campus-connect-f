from flask import Flask, jsonify
from config import Config
from extensions import db
from routes.auth import auth_bp
from routes.profile import profile_bp
from routes.posts import posts_bp

import models


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(posts_bp)

    @app.route("/")
    def home():
        return jsonify({"message": "CampusConnect API running"})

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)