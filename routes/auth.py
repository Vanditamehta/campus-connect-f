from flask import Blueprint, request, jsonify

auth_bp = Blueprint("auth", __name__)

users = []


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    if not data.get("name") or not data.get("email"):
        return jsonify({"error": "name and email are required"}), 400

    user = {
        "id": len(users) + 1,
        "name": data["name"],
        "email": data["email"]
    }

    users.append(user)
    return jsonify(user), 201