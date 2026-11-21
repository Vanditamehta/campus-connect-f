
from flask import (
    Blueprint,
    request,
    jsonify,
    render_template,
    redirect,
    url_for,
    session,
    flash
)

from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models import Profile, User


profile_bp = Blueprint("profile", __name__)


# Get the currently logged-in user
def get_logged_in_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    user = db.session.get(User, user_id)

    if user is None:
        session.clear()

    return user


# Validate profile information
def validate_profile_data(data, user, profile=None):

    # Name is mandatory when creating a profile.
    # During an update, existing values can be retained.
    name = data.get(
        "name",
        profile.name if profile else ""
    )

    headline = data.get(
        "headline",
        user.headline or ""
    )

    specialization = data.get(
        "specialization",
        profile.specialization if profile else ""
    )

    bio = data.get(
        "bio",
        profile.bio if profile else ""
    )

    skills = data.get(
        "skills",
        profile.skills if profile else []
    )

    # Validate name
    if not isinstance(name, str):
        return None, "Name must be text."

    name = name.strip()

    if not name:
        return None, "Name is required."

    if len(name) > 100:
        return None, "Name cannot exceed 100 characters."

    # Validate headline
    if not isinstance(headline, str):
        return None, "Headline must be text."

    headline = headline.strip()

    if len(headline) > 150:
        return None, "Headline cannot exceed 150 characters."

    # Validate specialization
    if not isinstance(specialization, str):
        return None, "Specialization must be text."

    specialization = specialization.strip()

    if len(specialization) > 150:
        return None, "Specialization cannot exceed 150 characters."

    # Validate bio
    if not isinstance(bio, str):
        return None, "Bio must be text."

    bio = bio.strip()

    if len(bio) > 2000:
        return None, "Bio cannot exceed 2000 characters."

    # Accept skills as a list or comma-separated string
    if isinstance(skills, str):
        skills = skills.split(",")

    if not isinstance(skills, list):
        return None, "Skills must be a list or comma-separated text."

    cleaned_skills = []

    for skill in skills:

        if not isinstance(skill, str):
            return None, "Each skill must be text."

        skill = skill.strip()

        if not skill:
            continue

        if len(skill) > 50:
            return None, "Each skill cannot exceed 50 characters."

        if skill not in cleaned_skills:
            cleaned_skills.append(skill)

    if not cleaned_skills:
        return None, "At least one skill is required."

    if len(cleaned_skills) > 20:
        return None, "You can add a maximum of 20 skills."

    return {
        "name": name,
        "headline": headline,
        "specialization": specialization,
        "bio": bio,
        "skills": cleaned_skills
    }, None


# Create or update profile information
def save_profile_data(user, profile, validated_data):

    if profile is None:
        profile = Profile(user_id=user.id)

    profile.name = validated_data["name"]
    profile.skills = validated_data["skills"]
    profile.specialization = validated_data["specialization"]
    profile.bio = validated_data["bio"]

    # Update the user's account information
    user.name = validated_data["name"]
    user.headline = validated_data["headline"]

    db.session.add(profile)
    db.session.commit()

    return profile


# Format profile data for JSON responses
def profile_response(profile):

    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "name": profile.name,
        "headline": profile.user.headline or "",
        "skills": profile.skills,
        "specialization": profile.specialization,
        "bio": profile.bio
    }


# View or create the logged-in user's profile
@profile_bp.route("/profile", methods=["GET", "POST"])
def profile_page():

    user = get_logged_in_user()

    if user is None:

        if request.is_json:
            return jsonify({
                "error": "Please log in first."
            }), 401

        flash("Please log in to view your profile.", "warning")
        return redirect(url_for("auth.login"))

    # Display profile
    if request.method == "GET":

        profile = Profile.query.filter_by(
            user_id=user.id
        ).first()

        if profile is None:
            flash("Please complete your profile.", "info")
            return redirect(url_for("profile.edit_profile"))

        return render_template(
            "profile.html",
            profile=profile,
            user=user
        )

    # Create profile
    data = request.get_json(silent=True)

    if data is None:
        data = request.form

    if not hasattr(data, "get"):
        return jsonify({"error": "Invalid profile data."}), 400

    # Require name and skills during creation
    if not data.get("name") or not data.get("skills"):
        if request.is_json:
            return jsonify({
                "error": "Name and skills are required."
            }), 400

        flash("Name and skills are required.", "danger")
        return redirect(url_for("profile.edit_profile"))

    existing_profile = Profile.query.filter_by(
        user_id=user.id
    ).first()

    if existing_profile:

        if request.is_json:
            return jsonify({
                "error": "Profile already exists. Use the update route."
            }), 409

        flash("Your profile already exists. Edit it instead.", "info")
        return redirect(url_for("profile.edit_profile"))

    validated_data, error = validate_profile_data(data, user)

    if error:

        if request.is_json:
            return jsonify({"error": error}), 400

        flash(error, "danger")
        return redirect(url_for("profile.edit_profile"))

    try:
        profile = save_profile_data(
            user,
            None,
            validated_data
        )

    except SQLAlchemyError:
        db.session.rollback()

        if request.is_json:
            return jsonify({
                "error": "Could not save profile."
            }), 500

        flash("Could not save your profile. Please try again.", "danger")
        return redirect(url_for("profile.edit_profile"))

    if request.is_json:
        return jsonify(profile_response(profile)), 201

    flash("Profile created successfully!", "success")
    return redirect(url_for("profile.profile_page"))


# Open and save the edit profile form
@profile_bp.route("/profile/edit", methods=["GET", "POST"])
def edit_profile():

    user = get_logged_in_user()

    if user is None:

        if request.is_json:
            return jsonify({
                "error": "Please log in first."
            }), 401

        flash("Please log in to edit your profile.", "warning")
        return redirect(url_for("auth.login"))

    profile = Profile.query.filter_by(
        user_id=user.id
    ).first()

    # Display edit form
    if request.method == "GET":

        return render_template(
            "edit_profile.html",
            profile=profile,
            user=user
        )

    # Receive updated information
    data = request.get_json(silent=True)

    if data is None:
        data = request.form

    if not hasattr(data, "get"):
        return jsonify({"error": "Invalid profile data."}), 400

    validated_data, error = validate_profile_data(
        data,
        user,
        profile
    )

    if error:

        if request.is_json:
            return jsonify({"error": error}), 400

        flash(error, "danger")
        return redirect(url_for("profile.edit_profile"))

    try:
        profile = save_profile_data(
            user,
            profile,
            validated_data
        )

    except SQLAlchemyError:
        db.session.rollback()

        if request.is_json:
            return jsonify({
                "error": "Could not save profile changes."
            }), 500

        flash("Could not save changes. Please try again.", "danger")
        return redirect(url_for("profile.edit_profile"))

    if request.is_json:
        return jsonify({
            "message": "Profile updated successfully.",
            "profile": profile_response(profile)
        }), 200

    flash("Profile updated successfully!", "success")
    return redirect(url_for("profile.profile_page"))


# View a public profile or update it if the logged-in user owns it
@profile_bp.route(
    "/profile/<int:profile_id>",
    methods=["GET", "PUT", "PATCH"]
)
def get_profile(profile_id):

    profile = db.session.get(Profile, profile_id)

    if profile is None:
        return jsonify({
            "error": "Profile not found."
        }), 404

    # Public profile viewing
    if request.method == "GET":
        return jsonify(profile_response(profile)), 200

    # Login required for updates
    user = get_logged_in_user()

    if user is None:
        return jsonify({
            "error": "Please log in first."
        }), 401

    # Ownership verification
    if profile.user_id != user.id:
        return jsonify({
            "error": "You are not allowed to edit this profile."
        }), 403

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Invalid profile data."
        }), 400

    validated_data, error = validate_profile_data(
        data,
        user,
        profile
    )

    if error:
        return jsonify({"error": error}), 400

    try:
        save_profile_data(
            user,
            profile,
            validated_data
        )

    except SQLAlchemyError:
        db.session.rollback()

        return jsonify({
            "error": "Could not save profile changes."
        }), 500

    return jsonify({
        "message": "Profile updated successfully.",
        "profile": profile_response(profile)
    }), 200
