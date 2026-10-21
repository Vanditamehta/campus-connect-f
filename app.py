from flask import Flask, jsonify
from routes.auth import auth_bp
from routes.profile import profile_bp


def create_app():
    app = Flask(__name__)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)

    @app.route("/")
    def home():
        return jsonify({"message": "CampusConnect API running"})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)