from flask import (
    Blueprint, request, jsonify, render_template,
    redirect, url_for, session, flash
)
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models import Post, User


posts_bp = Blueprint("posts", __name__)


@posts_bp.route("/feed", methods=["GET"])
def feed():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template("feed.html", posts=posts)


@posts_bp.route("/post", methods=["POST"])
def create_post():
    user_id = session.get("user_id")

    if not user_id:
        if request.is_json:
            return jsonify({"error": "Please log in first"}), 401

        flash("Please log in to create a post.", "warning")
        return redirect(url_for("auth.login"))

    user = db.session.get(User, user_id)

    if user is None:
        session.clear()

        if request.is_json:
            return jsonify({"error": "User not found. Please log in again."}), 401

        flash("Please log in again.", "warning")
        return redirect(url_for("auth.login"))

    data = request.get_json(silent=True) or request.form

    content = data.get("content", "")
    kind = data.get("kind", "status")

    if not isinstance(content, str) or not isinstance(kind, str):
        return jsonify({"error": "Invalid post data"}), 400

    content = content.strip()
    kind = kind.strip().lower()

    if not content:
        if request.is_json:
            return jsonify({"error": "Post content cannot be empty"}), 400
        flash("Post content cannot be empty.", "danger")
        return redirect(url_for("posts.feed"))

    if len(content) > 2000:
        if request.is_json:
            return jsonify({"error": "Post cannot exceed 2000 characters"}), 400
        flash("Post cannot exceed 2000 characters.", "danger")
        return redirect(url_for("posts.feed"))

    if kind not in ["status", "achievement"]:
        if request.is_json:
            return jsonify({"error": "Invalid post type"}), 400
        flash("Invalid post type.", "danger")
        return redirect(url_for("posts.feed"))

    post = Post(
        user_id=user.id,
        content=content,
        kind=kind
    )

    try:
        db.session.add(post)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()

        if request.is_json:
            return jsonify({"error": "Could not save post"}), 500

        flash("Something went wrong. Please try again.", "danger")
        return redirect(url_for("posts.feed"))

    if request.is_json:
        return jsonify({
            "message": "Post created successfully",
            "id": post.id,
            "user_id": post.user_id,
            "content": post.content,
            "kind": post.kind
        }), 201

    flash("Your post was published successfully!", "success")
    return redirect(url_for("posts.feed"))