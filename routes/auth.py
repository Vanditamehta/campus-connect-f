
import re

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
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from extensions import db
from models import User


auth_bp = Blueprint("auth", __name__)


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    if request.is_json:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({"error": "Invalid request data."}), 400
    else:
        data = request.form

    name = data.get("name", "")
    email = data.get("email", "")
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")

    # Validate input types
    if not all(isinstance(value, str) for value in (
        name, email, password, confirm_password
    )):
        message = "Please enter valid registration details."

        if request.is_json:
            return jsonify({"error": message}), 400

        flash(message, "danger")
        return redirect(url_for("auth.register"))

    name = name.strip()
    email = email.strip().lower()

    # Required fields
    if not name or not email or not password:
        message = "All fields are required."

        if request.is_json:
            return jsonify({"error": message}), 400

        flash(message, "danger")
        return redirect(url_for("auth.register"))

    # Name validation
    if len(name) > 100:
        message = "Name cannot exceed 100 characters."

        if request.is_json:
            return jsonify({"error": message}), 400

        flash(message, "danger")
        return redirect(url_for("auth.register"))

    # Email validation
    email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    if len(email) > 120 or not re.fullmatch(email_pattern, email):
        message = "Please enter a valid email address."

        if request.is_json:
            return jsonify({"error": message}), 400

        flash(message, "danger")
        return redirect(url_for("auth.register"))

    # Password validation
    if len(password) < 8:
        message = "Password must contain at least 8 characters."

        if request.is_json:
            return jsonify({"error": message}), 400

        flash(message, "danger")
        return redirect(url_for("auth.register"))

    # Confirm password validation for browser registration
    if not request.is_json:

        if not confirm_password:
            flash("Please confirm your password.", "danger")
            return redirect(url_for("auth.register"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.register"))

    # Check existing email and create account
    try:
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            message = "This email is already registered."

            if request.is_json:
                return jsonify({
                    "error": "email already registered"
                }), 409

            flash(message, "danger")
            return redirect(url_for("auth.register"))

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password)
        )

        db.session.add(user)
        db.session.commit()

    except IntegrityError:
        db.session.rollback()

        message = "This email is already registered."

        if request.is_json:
            return jsonify({
                "error": "email already registered"
            }), 409

        flash(message, "danger")
        return redirect(url_for("auth.register"))

    except SQLAlchemyError:
        db.session.rollback()

        current_app.logger.exception(
            "Database error during registration."
        )

        message = (
            "Registration is temporarily unavailable. "
            "Please try again later."
        )

        if request.is_json:
            return jsonify({"error": message}), 503

        flash(message, "danger")
        return redirect(url_for("auth.register"))

    # Successful registration
    if request.is_json:
        return jsonify({
            "id": user.id,
            "name": user.name,
            "email": user.email
        }), 201

    flash(
        "Account created successfully. Please log in.",
        "success"
    )
    return redirect(url_for("auth.login"))


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    if request.is_json:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({"error": "Invalid request data."}), 400
    else:
        data = request.form

    email_value = data.get("email", "")
    password = data.get("password", "")

    if not isinstance(email_value, str) or not isinstance(password, str):
        if request.is_json:
            return jsonify({"error": "Invalid input."}), 400

        flash("Please enter valid login details.", "danger")
        return redirect(url_for("auth.login"))

    email = email_value.strip().lower()

    if not email or not password:
        message = "Please enter both email and password."

        if request.is_json:
            return jsonify({"error": message}), 400

        flash(message, "danger")
        return redirect(url_for("auth.login"))

    email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    if len(email) > 120 or not re.fullmatch(email_pattern, email):
        message = "Please enter a valid email address."

        if request.is_json:
            return jsonify({"error": message}), 400

        flash(message, "danger")
        return redirect(url_for("auth.login"))

    try:
        user = User.query.filter_by(email=email).first()

    except SQLAlchemyError:
        db.session.rollback()

        current_app.logger.exception(
            "Database error during login."
        )

        message = (
            "Login is temporarily unavailable. "
            "Please try again later."
        )

        if request.is_json:
            return jsonify({"error": message}), 503

        flash(message, "danger")
        return redirect(url_for("auth.login"))

    password_valid = False

    if user and user.password_hash:
        try:
            password_valid = check_password_hash(
                user.password_hash,
                password
            )
        except (ValueError, TypeError):
            password_valid = False

    if not user or not password_valid:
        message = "Invalid email or password."

        if request.is_json:
            return jsonify({"error": message}), 401

        flash(message, "danger")
        return redirect(url_for("auth.login"))

    session.clear()
    session["user_id"] = user.id

    if request.is_json:
        return jsonify({
            "message": "Login successful",
            "user_id": user.id,
            "name": user.name
        }), 200

    flash("Welcome back!", "success")
    return redirect(url_for("home"))


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():

    session.clear()

    if request.is_json:
        return jsonify({
            "message": "Logged out successfully"
        }), 200

    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
