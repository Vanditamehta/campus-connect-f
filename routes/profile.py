
import os
import uuid
from urllib.parse import urlsplit

from PIL import Image, UnidentifiedImageError

from flask import (
    Blueprint,
    request,
    jsonify,
    render_template,
    redirect,
    url_for,
    session,
    flash,
    current_app
)

from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models import Profile, User, Post, Comment, Like, SocialLink


profile_bp = Blueprint("profile", __name__)

ALLOWED_IMAGE_FORMATS = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp"
}

MAX_SOCIAL_LINKS = 10


# =====================================================
# AUTHENTICATION
# =====================================================

def get_logged_in_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    user = db.session.get(User, user_id)

    if user is None:
        session.clear()

    return user


# =====================================================
# PROFILE IMAGE HELPERS
# =====================================================

def save_profile_image(image_file):

    if image_file is None or not image_file.filename:
        return None

    try:
        image_file.stream.seek(0)

        with Image.open(image_file.stream) as image:
            image_format = image.format

            if image_format not in ALLOWED_IMAGE_FORMATS:
                raise ValueError(
                    "Only JPEG, PNG and WEBP images are allowed."
                )

            image.verify()

        image_file.stream.seek(0)

        extension = ALLOWED_IMAGE_FORMATS[image_format]
        filename = f"{uuid.uuid4().hex}{extension}"

        upload_folder = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_folder, exist_ok=True)

        image_path = os.path.join(upload_folder, filename)
        image_file.save(image_path)

        return filename

    except ValueError:
        raise

    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError
    ):
        raise ValueError(
            "The uploaded file is not a valid image."
        )


def remove_profile_image(filename):

    if not filename:
        return

    safe_filename = os.path.basename(filename)

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    image_path = os.path.join(upload_folder, safe_filename)

    try:
        if os.path.isfile(image_path):
            os.remove(image_path)

    except OSError:
        current_app.logger.warning(
            "Could not remove old profile image: %s",
            safe_filename
        )


# =====================================================
# PROFILE VALIDATION
# =====================================================

def validate_profile_data(data, user, profile=None):

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

    if not isinstance(name, str):
        return None, "Name must be text."

    name = name.strip()

    if not name:
        return None, "Name is required."

    if len(name) > 100:
        return None, "Name cannot exceed 100 characters."

    if not isinstance(headline, str):
        return None, "Headline must be text."

    headline = headline.strip()

    if len(headline) > 150:
        return None, "Headline cannot exceed 150 characters."

    if not isinstance(specialization, str):
        return None, "Specialization must be text."

    specialization = specialization.strip()

    if len(specialization) > 150:
        return None, "Specialization cannot exceed 150 characters."

    if not isinstance(bio, str):
        return None, "Bio must be text."

    bio = bio.strip()

    if len(bio) > 2000:
        return None, "Bio cannot exceed 2000 characters."

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


# =====================================================
# SOCIAL LINK VALIDATION
# =====================================================

def validate_social_link(title, url):

    if not isinstance(title, str) or not isinstance(url, str):
        return None, "Title and URL must be text."

    title = title.strip()
    url = url.strip()

    if not title:
        return None, "Please enter a link title."

    if len(title) > 50:
        return None, "Link title cannot exceed 50 characters."

    if not url:
        return None, "Please enter a URL."

    if len(url) > 500:
        return None, "URL cannot exceed 500 characters."

    try:
        parsed_url = urlsplit(url)

        if (
            parsed_url.scheme not in ("http", "https")
            or not parsed_url.hostname
            or parsed_url.username
            or parsed_url.password
        ):
            return None, "Enter a valid HTTP or HTTPS URL."

    except ValueError:
        return None, "Enter a valid URL."

    return {
        "title": title,
        "url": url
    }, None


# =====================================================
# SAVE PROFILE INFORMATION
# =====================================================

def save_profile_data(
    user,
    profile,
    validated_data,
    profile_image_filename=None
):

    if profile is None:
        profile = Profile(user_id=user.id)

    profile.name = validated_data["name"]
    profile.skills = validated_data["skills"]
    profile.specialization = validated_data["specialization"]
    profile.bio = validated_data["bio"]

    if profile_image_filename:
        profile.profile_image_filename = profile_image_filename

    user.name = validated_data["name"]
    user.headline = validated_data["headline"]

    db.session.add(profile)
    db.session.commit()

    return profile


# =====================================================
# PROFILE JSON RESPONSE
# =====================================================

def profile_response(profile):

    image_url = None

    if profile.profile_image_filename:
        image_url = url_for(
            "static",
            filename=f"uploads/{profile.profile_image_filename}"
        )

    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "name": profile.name,
        "headline": profile.user.headline or "",
        "skills": profile.skills,
        "specialization": profile.specialization,
        "bio": profile.bio,
        "profile_image_url": image_url,
        "social_links": [
            {
                "id": link.id,
                "title": link.title,
                "url": link.url
            }
            for link in profile.user.social_links
        ]
    }


# =====================================================
# CREATE OR VIEW OWN PROFILE
# =====================================================

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

    if request.method == "GET":

        profile = Profile.query.filter_by(
            user_id=user.id
        ).first()

        if profile is None:
            flash("Please complete your profile.", "info")
            return redirect(url_for("profile.edit_profile"))

        recent_posts = (
            Post.query
            .filter_by(user_id=user.id)
            .order_by(Post.created_at.desc(), Post.id.desc())
            .limit(10)
            .all()
        )

        recent_comments = (
            Comment.query
            .filter_by(user_id=user.id)
            .order_by(Comment.created_at.desc(), Comment.id.desc())
            .limit(10)
            .all()
        )

        recent_reactions = (
            Like.query
            .filter_by(user_id=user.id)
            .order_by(Like.created_at.desc(), Like.id.desc())
            .limit(10)
            .all()
        )

        return render_template(
            "profile.html",
            profile=profile,
            user=user,
            recent_posts=recent_posts,
            recent_comments=recent_comments,
            recent_reactions=recent_reactions
        )

    data = request.get_json(silent=True)

    if data is None:
        data = request.form

    if not hasattr(data, "get"):
        return jsonify({
            "error": "Invalid profile data."
        }), 400

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

    uploaded_filename = None

    try:
        if not request.is_json:
            uploaded_filename = save_profile_image(
                request.files.get("profile_image")
            )

        profile = save_profile_data(
            user,
            None,
            validated_data,
            uploaded_filename
        )

    except ValueError as error:

        if uploaded_filename:
            remove_profile_image(uploaded_filename)

        if request.is_json:
            return jsonify({"error": str(error)}), 400

        flash(str(error), "danger")
        return redirect(url_for("profile.edit_profile"))

    except SQLAlchemyError:
        db.session.rollback()

        if uploaded_filename:
            remove_profile_image(uploaded_filename)

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


# =====================================================
# EDIT PROFILE
# =====================================================

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

    if request.method == "GET":

        return render_template(
            "edit_profile.html",
            profile=profile,
            user=user
        )

    data = request.get_json(silent=True)

    if data is None:
        data = request.form

    if not hasattr(data, "get"):
        return jsonify({
            "error": "Invalid profile data."
        }), 400

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

    old_image_filename = (
        profile.profile_image_filename
        if profile else None
    )

    uploaded_filename = None

    try:
        if not request.is_json:
            uploaded_filename = save_profile_image(
                request.files.get("profile_image")
            )

        profile = save_profile_data(
            user,
            profile,
            validated_data,
            uploaded_filename
        )

    except ValueError as error:

        if uploaded_filename:
            remove_profile_image(uploaded_filename)

        if request.is_json:
            return jsonify({"error": str(error)}), 400

        flash(str(error), "danger")
        return redirect(url_for("profile.edit_profile"))

    except SQLAlchemyError:
        db.session.rollback()

        if uploaded_filename:
            remove_profile_image(uploaded_filename)

        if request.is_json:
            return jsonify({
                "error": "Could not save profile changes."
            }), 500

        flash("Could not save changes. Please try again.", "danger")
        return redirect(url_for("profile.edit_profile"))

    if uploaded_filename and old_image_filename:
        remove_profile_image(old_image_filename)

    if request.is_json:
        return jsonify({
            "message": "Profile updated successfully.",
            "profile": profile_response(profile)
        }), 200

    flash("Profile updated successfully!", "success")
    return redirect(url_for("profile.profile_page"))


# =====================================================
# VIEW OR UPDATE PUBLIC PROFILE API
# =====================================================

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

    if request.method == "GET":
        return jsonify(profile_response(profile)), 200

    user = get_logged_in_user()

    if user is None:
        return jsonify({
            "error": "Please log in first."
        }), 401

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


# =====================================================
# ADD SOCIAL LINK
# =====================================================

@profile_bp.route("/profile/social-links", methods=["POST"])
def add_social_link():

    user = get_logged_in_user()

    if user is None:
        flash("Please log in first.", "warning")
        return redirect(url_for("auth.login"))

    title = request.form.get("title", "")
    url = request.form.get("url", "")

    if request.is_json:
        data = request.get_json(silent=True) or {}
        title = data.get("title", "")
        url = data.get("url", "")

    validated, error = validate_social_link(title, url)

    if error:
        flash(error, "danger")
        return redirect(url_for("profile.profile_page"))

    if len(user.social_links) >= MAX_SOCIAL_LINKS:
        flash("You can add a maximum of 10 links.", "warning")
        return redirect(url_for("profile.profile_page"))

    link = SocialLink(
        user_id=user.id,
        title=validated["title"],
        url=validated["url"]
    )

    try:
        db.session.add(link)
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()
        flash("Could not add your link. Please try again.", "danger")
        return redirect(url_for("profile.profile_page"))

    flash("Social link added successfully!", "success")
    return redirect(url_for("profile.profile_page"))


# =====================================================
# EDIT SOCIAL LINK
# =====================================================

@profile_bp.route(
    "/profile/social-links/<int:link_id>/edit",
    methods=["POST"]
)
def edit_social_link(link_id):

    user = get_logged_in_user()

    if user is None:
        flash("Please log in first.", "warning")
        return redirect(url_for("auth.login"))

    link = db.session.get(SocialLink, link_id)

    if link is None:
        flash("Social link not found.", "danger")
        return redirect(url_for("profile.profile_page"))

    if link.user_id != user.id:
        flash("You cannot edit someone else's link.", "danger")
        return redirect(url_for("profile.profile_page"))

    validated, error = validate_social_link(
        request.form.get("title", ""),
        request.form.get("url", "")
    )

    if error:
        flash(error, "danger")
        return redirect(url_for("profile.profile_page"))

    link.title = validated["title"]
    link.url = validated["url"]

    try:
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()
        flash("Could not update your link.", "danger")
        return redirect(url_for("profile.profile_page"))

    flash("Social link updated successfully!", "success")
    return redirect(url_for("profile.profile_page"))


# =====================================================
# DELETE SOCIAL LINK
# =====================================================

@profile_bp.route(
    "/profile/social-links/<int:link_id>/delete",
    methods=["POST"]
)
def delete_social_link(link_id):

    user = get_logged_in_user()

    if user is None:
        flash("Please log in first.", "warning")
        return redirect(url_for("auth.login"))

    link = db.session.get(SocialLink, link_id)

    if link is None:
        flash("Social link not found.", "danger")
        return redirect(url_for("profile.profile_page"))

    if link.user_id != user.id:
        flash("You cannot delete someone else's link.", "danger")
        return redirect(url_for("profile.profile_page"))

    try:
        db.session.delete(link)
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()
        flash("Could not delete your link.", "danger")
        return redirect(url_for("profile.profile_page"))

    flash("Social link deleted successfully!", "success")
    return redirect(url_for("profile.profile_page"))
