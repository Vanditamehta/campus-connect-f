
from flask import (
    Blueprint, request, jsonify, render_template,
    redirect, url_for, session, flash
)
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db
from models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    data = request.get_json(silent=True) or request.form

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")

    if not name or not email or not password:
        if request.is_json:
            return jsonify({"error": "name, email and password are required"}), 400
        flash("All fields are required.", "danger")
        return redirect(url_for("auth.register"))

    if len(password) < 8:
        if request.is_json:
            return jsonify({"error": "Password must contain at least 8 characters"}), 400
        flash("Password must contain at least 8 characters.", "danger")
        return redirect(url_for("auth.register"))

    if not request.is_json and password != confirm_password:
        flash("Passwords do not match.", "danger")
        return redirect(url_for("auth.register"))

    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        if request.is_json:
            return jsonify({"error": "email already registered"}), 409
        flash("This email is already registered.", "danger")
        return redirect(url_for("auth.register"))

    user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password)
    )

    db.session.add(user)
    db.session.commit()

    if request.is_json:
        return jsonify({
            "id": user.id,
            "name": user.name,
            "email": user.email
        }), 201

    flash("Account created successfully. Please log in.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json(silent=True) or request.form

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()

    if not user or not user.password_hash or not check_password_hash(
        user.password_hash, password
    ):
        if request.is_json:
            return jsonify({"error": "Invalid email or password"}), 401
        flash("Invalid email or password.", "danger")
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


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():

    session.clear()

    if request.is_json:
        return jsonify({"message": "Logged out successfully"}), 200

    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
