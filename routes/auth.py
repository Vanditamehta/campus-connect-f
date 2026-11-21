from flask import Blueprint, request, jsonify
from extensions import db
from models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}

    if not data.get("name") or not data.get("email"):
        return jsonify({"error": "name and email are required"}), 400

    existing_user = User.query.filter_by(email=data["email"]).first()

    if existing_user:
        return jsonify({"error": "email already registered"}), 409

    user = User(
        name=data["name"],
        email=data["email"]
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email
    }), 201