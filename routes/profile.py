
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
from image_storage import (
    store_image,
    get_image_url,
    delete_image
)
from models import (
    Profile,
    User,
    Post,
    Comment,
    Like,
    SocialLink,
    ProfileSection
)


profile_bp = Blueprint("profile", __name__)

ALLOWED_IMAGE_FORMATS = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp"
}

MAX_SOCIAL_LINKS = 10

PROFILE_SECTION_FIELDS = {
    "education": {
        "institution": 150,
        "degree": 150,
        "field_of_study": 150,
        "graduation_year": 20,
        "description": 2000
    },
    "experience": {
        "title": 150,
        "company": 150,
        "employment_type": 100,
        "location": 150,
        "start_date": 30,
        "end_date": 30,
        "currently_working": 10,
        "description": 2000
    },
    "projects": {
        "name": 150,
        "description": 2000,
        "technologies": 500,
        "project_url": 500
    },
    "certifications": {
        "name": 150,
        "issuing_organization": 150,
        "issue_date": 30,
        "expiration_date": 30,
        "credential_id": 150,
        "credential_url": 500
    },
    "courses": {
        "name": 150,
        "provider": 150,
        "completion_date": 30,
        "description": 2000
    },
    "achievements": {
        "title": 150,
        "issuer": 150,
        "date": 30,
        "description": 2000
    },
    "volunteer_experience": {
        "role": 150,
        "organization": 150,
        "cause": 150,
        "start_date": 30,
        "end_date": 30,
        "description": 2000
    }
}

PROFILE_SECTION_REQUIRED_FIELDS = {
    "education": "institution",
    "experience": "title",
    "projects": "name",
    "certifications": "name",
    "courses": "name",
    "achievements": "title",
    "volunteer_experience": "role"
}


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

        return store_image(
            image_file,
            folder="profile_images",
            extension=extension
        )

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

    delete_image(filename)


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
# PROFILE SECTION VALIDATION
# =====================================================

def validate_profile_section(section_type, data):

    if section_type not in PROFILE_SECTION_FIELDS:
        return None, "Invalid profile section type."

    if not isinstance(data, dict):
        return None, "Section information must be valid data."

    allowed_fields = PROFILE_SECTION_FIELDS[section_type]
    cleaned_data = {}

    for field, value in data.items():

        if field not in allowed_fields:
            return None, f"Invalid field: {field}."

        if field == "currently_working":

            if isinstance(value, bool):
                cleaned_data[field] = value
                continue

            if isinstance(value, str):
                value = value.strip().lower()

                if value in ("true", "1", "yes", "on"):
                    cleaned_data[field] = True
                    continue

                if value in ("false", "0", "no", "off", ""):
                    cleaned_data[field] = False
                    continue

            return None, "Currently working must be true or false."

        if not isinstance(value, str):
            return None, (
                f"{field.replace('_', ' ').title()} must be text."
            )

        value = value.strip()

        if len(value) > allowed_fields[field]:
            return None, (
                f"{field.replace('_', ' ').title()} cannot exceed "
                f"{allowed_fields[field]} characters."
            )

        if value:
            cleaned_data[field] = value

    required_field = PROFILE_SECTION_REQUIRED_FIELDS[section_type]

    if not cleaned_data.get(required_field):
        return None, (
            f"{required_field.replace('_', ' ').title()} is required."
        )

    for url_field in ("project_url", "credential_url"):

        if url_field not in cleaned_data:
            continue

        try:
            parsed_url = urlsplit(cleaned_data[url_field])

            if (
                parsed_url.scheme not in ("http", "https")
                or not parsed_url.hostname
                or parsed_url.username
                or parsed_url.password
            ):
                return None, (
                    f"Enter a valid URL for "
                    f"{url_field.replace('_', ' ')}."
                )

        except ValueError:
            return None, "Enter a valid URL."

    return cleaned_data, None


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

    image_url = get_image_url(
        profile.profile_image_filename
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
        ],
        "profile_sections": [
            {
                "id": section.id,
                "section_type": section.section_type,
                "data": section.data
            }
            for section in profile.user.profile_sections
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

        profile_sections = (
            ProfileSection.query
            .filter_by(user_id=user.id)
            .order_by(ProfileSection.id.asc())
            .all()
        )

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
            profile_sections=profile_sections,
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


# =====================================================
# ADD PROFILE SECTION
# =====================================================

@profile_bp.route("/profile/sections", methods=["POST"])
def add_profile_section():

    user = get_logged_in_user()

    if user is None:

        if request.is_json:
            return jsonify({"error": "Please log in first."}), 401

        flash("Please log in first.", "warning")
        return redirect(url_for("auth.login"))

    if request.is_json:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({"error": "Invalid section data."}), 400

        section_type = data.get("section_type", "")
        section_data = data.get("data", {})

    else:
        data = request.form
        section_type = data.get("section_type", "")
        section_data = {
            key: value
            for key, value in data.items()
            if key != "section_type"
        }

    validated_data, error = validate_profile_section(
        section_type,
        section_data
    )

    if error:

        if request.is_json:
            return jsonify({"error": error}), 400

        flash(error, "danger")
        return redirect(url_for("profile.profile_page"))

    section = ProfileSection(
        user_id=user.id,
        section_type=section_type,
        data=validated_data
    )

    try:

        db.session.add(section)
        db.session.commit()

    except SQLAlchemyError:

        db.session.rollback()

        if request.is_json:
            return jsonify({
                "error": "Could not add profile section."
            }), 500

        flash("Could not add profile section.", "danger")
        return redirect(url_for("profile.profile_page"))

    if request.is_json:
        return jsonify({
            "message": "Profile section added successfully.",
            "section": {
                "id": section.id,
                "section_type": section.section_type,
                "data": section.data
            }
        }), 201

    flash("Profile section added successfully!", "success")
    return redirect(url_for("profile.profile_page"))


# =====================================================
# EDIT PROFILE SECTION
# =====================================================

@profile_bp.route(
    "/profile/sections/<int:section_id>/edit",
    methods=["POST"]
)
def edit_profile_section(section_id):

    user = get_logged_in_user()

    if user is None:

        if request.is_json:
            return jsonify({"error": "Please log in first."}), 401

        flash("Please log in first.", "warning")
        return redirect(url_for("auth.login"))

    section = db.session.get(ProfileSection, section_id)

    if section is None:

        if request.is_json:
            return jsonify({
                "error": "Profile section not found."
            }), 404

        flash("Profile section not found.", "danger")
        return redirect(url_for("profile.profile_page"))

    if section.user_id != user.id:

        if request.is_json:
            return jsonify({
                "error": "You cannot edit someone else's profile section."
            }), 403

        flash("You cannot edit someone else's profile section.", "danger")
        return redirect(url_for("profile.profile_page"))

    if request.is_json:

        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({"error": "Invalid section data."}), 400

        section_type = data.get("section_type", section.section_type)
        incoming_data = data.get("data", {})

    else:

        data = request.form
        section_type = section.section_type

        # Do not include the CSRF token in profile section data.
        incoming_data = {
            key: value
            for key, value in data.items()
            if key != "csrf_token"
        }

    if section_type != section.section_type:

        if request.is_json:
            return jsonify({
                "error": "Section type cannot be changed."
            }), 400

        flash("Section type cannot be changed.", "danger")
        return redirect(url_for("profile.profile_page"))

    if not isinstance(incoming_data, dict):
        return jsonify({"error": "Invalid section data."}), 400

    merged_data = dict(section.data or {})
    merged_data.update(incoming_data)

    # HTML does not submit unchecked checkboxes.
    # Save False explicitly when the experience checkbox is unchecked.
    if section_type == "experience" and not request.is_json:
        merged_data["currently_working"] = (
            request.form.get("currently_working") == "true"
        )

    validated_data, error = validate_profile_section(
        section_type,
        merged_data
    )

    if error:

        if request.is_json:
            return jsonify({"error": error}), 400

        flash(error, "danger")
        return redirect(url_for("profile.profile_page"))

    section.data = validated_data

    try:

        db.session.commit()

    except SQLAlchemyError:

        db.session.rollback()

        if request.is_json:
            return jsonify({
                "error": "Could not update profile section."
            }), 500

        flash("Could not update profile section.", "danger")
        return redirect(url_for("profile.profile_page"))

    if request.is_json:
        return jsonify({
            "message": "Profile section updated successfully.",
            "section": {
                "id": section.id,
                "section_type": section.section_type,
                "data": section.data
            }
        }), 200

    flash("Profile section updated successfully!", "success")
    return redirect(url_for("profile.profile_page"))


# =====================================================
# DELETE PROFILE SECTION
# =====================================================

@profile_bp.route(
    "/profile/sections/<int:section_id>/delete",
    methods=["POST"]
)
def delete_profile_section(section_id):

    user = get_logged_in_user()

    if user is None:

        if request.is_json:
            return jsonify({"error": "Please log in first."}), 401

        flash("Please log in first.", "warning")
        return redirect(url_for("auth.login"))

    section = db.session.get(ProfileSection, section_id)

    if section is None:

        if request.is_json:
            return jsonify({
                "error": "Profile section not found."
            }), 404

        flash("Profile section not found.", "danger")
        return redirect(url_for("profile.profile_page"))

    if section.user_id != user.id:

        if request.is_json:
            return jsonify({
                "error": "You cannot delete someone else's profile section."
            }), 403

        flash("You cannot delete someone else's profile section.", "danger")
        return redirect(url_for("profile.profile_page"))

    try:

        db.session.delete(section)
        db.session.commit()

    except SQLAlchemyError:

        db.session.rollback()

        if request.is_json:
            return jsonify({
                "error": "Could not delete profile section."
            }), 500

        flash("Could not delete profile section.", "danger")
        return redirect(url_for("profile.profile_page"))

    if request.is_json:
        return jsonify({
            "message": "Profile section deleted successfully."
        }), 200

    flash("Profile section deleted successfully!", "success")
    return redirect(url_for("profile.profile_page"))
