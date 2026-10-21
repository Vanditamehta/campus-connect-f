from flask import Blueprint, request, jsonify

profile_bp = Blueprint("profile", __name__)

profiles = []


@profile_bp.route("/profile", methods=["POST"])
def create_profile():
    data = request.get_json() or {}
    if not data.get("name") or not data.get("skills"):
        return jsonify({"error": "name and skills are required"}), 400

    profile = {
        "id": len(profiles) + 1,
        "name": data["name"],
        "skills": data["skills"],
        "specialization": data.get("specialization", ""),
        "bio": data.get("bio", ""),
    }

    profiles.append(profile)
    return jsonify(profile), 201


@profile_bp.route("/profile/<int:profile_id>", methods=["GET"])
def get_profile(profile_id):
    for p in profiles:
        if p["id"] == profile_id:
            return jsonify(p), 200

    return jsonify({"error": "profile not found"}), 404