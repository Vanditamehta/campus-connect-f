from flask import Blueprint, request, jsonify
from extensions import db
from models import Profile

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile", methods=["POST"])
def create_profile():
    data = request.get_json() or {}

    if not data.get("name") or not data.get("skills"):
        return jsonify({"error": "name and skills are required"}), 400

    profile = Profile(
        name=data["name"],
        skills=data["skills"],
        specialization=data.get("specialization", ""),
        bio=data.get("bio", "")
    )

    db.session.add(profile)
    db.session.commit()

    return jsonify({
        "id": profile.id,
        "name": profile.name,
        "skills": profile.skills,
        "specialization": profile.specialization,
        "bio": profile.bio
    }), 201


@profile_bp.route("/profile/<int:profile_id>", methods=["GET"])
def get_profile(profile_id):
    profile = db.session.get(Profile, profile_id)

    if profile is None:
        return jsonify({"error": "profile not found"}), 404

    return jsonify({
        "id": profile.id,
        "name": profile.name,
        "skills": profile.skills,
        "specialization": profile.specialization,
        "bio": profile.bio
    }), 200
