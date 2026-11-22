
import os
import uuid

from flask import (
    Blueprint, request, jsonify, render_template,
    redirect, url_for, session, flash, current_app
)
from sqlalchemy.exc import SQLAlchemyError
from PIL import Image, UnidentifiedImageError

from extensions import db
from models import Post, User, Like, Comment


posts_bp = Blueprint("posts", __name__)

ALLOWED_IMAGE_FORMATS = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp"
}


# --------------------------------------------------
# IMAGE HELPER FUNCTIONS
# --------------------------------------------------

def validate_image(file):
    """Check that the uploaded file is a valid supported image."""

    if not file or not file.filename:
        return None

    try:
        image = Image.open(file.stream)
        image_format = image.format
        image.verify()

        if image_format not in ALLOWED_IMAGE_FORMATS:
            return None

        file.stream.seek(0)
        return ALLOWED_IMAGE_FORMATS[image_format]

    except (UnidentifiedImageError, OSError, ValueError):
        return None


def save_image(file):
    """Save an uploaded image using a randomly generated filename."""

    extension = validate_image(file)

    if not extension:
        raise ValueError("Please upload a valid JPG, PNG, or WEBP image.")

    filename = f"{uuid.uuid4().hex}{extension}"
    upload_folder = current_app.config["UPLOAD_FOLDER"]

    os.makedirs(upload_folder, exist_ok=True)
    file.save(os.path.join(upload_folder, filename))

    return filename


def remove_image(filename):
    """Remove an image from the uploads folder."""

    if not filename:
        return

    upload_folder = os.path.abspath(
        current_app.config["UPLOAD_FOLDER"]
    )

    image_path = os.path.abspath(
        os.path.join(upload_folder, filename)
    )

    if os.path.dirname(image_path) != upload_folder:
        return

    if os.path.isfile(image_path):
        os.remove(image_path)


def get_uploaded_image():
    """Return the uploaded image, if one was provided."""

    return request.files.get("image")


# --------------------------------------------------
# FEED
# --------------------------------------------------

@posts_bp.route("/feed", methods=["GET"])
def feed():
    posts = Post.query.order_by(Post.created_at.desc()).all()

    current_user_id = session.get("user_id")

    return render_template(
        "feed.html",
        posts=posts,
        current_user_id=current_user_id
    )


# --------------------------------------------------
# CREATE POST
# --------------------------------------------------

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
            return jsonify({"error": "Please log in again."}), 401

        flash("Please log in again.", "warning")
        return redirect(url_for("auth.login"))

    data = request.get_json(silent=True) or request.form

    content = data.get("content", "")
    kind = data.get("kind", "status")
    image_file = get_uploaded_image()

    if not isinstance(content, str) or not isinstance(kind, str):
        return jsonify({"error": "Invalid post data"}), 400

    content = content.strip()
    kind = kind.strip().lower()

    if not content and not (image_file and image_file.filename):
        return jsonify({
            "error": "Please write something or upload a photo."
        }), 400

    if len(content) > 2000:
        return jsonify({"error": "Post cannot exceed 2000 characters"}), 400

    if kind not in ["status", "achievement"]:
        return jsonify({"error": "Invalid post type"}), 400

    filename = None

    if image_file and image_file.filename:
        try:
            filename = save_image(image_file)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

    post = Post(
        user_id=user.id,
        content=content,
        kind=kind,
        image_filename=filename
    )

    try:
        db.session.add(post)
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()

        if filename:
            remove_image(filename)

        return jsonify({"error": "Could not save post"}), 500

    return jsonify({
        "message": "Post created successfully",
        "id": post.id,
        "user_id": post.user_id,
        "content": post.content,
        "kind": post.kind,
        "image_filename": post.image_filename
    }), 201


# --------------------------------------------------
# EDIT POST
# --------------------------------------------------

@posts_bp.route("/post/<int:post_id>/edit", methods=["POST"])
def edit_post(post_id):
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Please log in first"}), 401

    post = db.session.get(Post, post_id)

    if post is None:
        return jsonify({"error": "Post not found"}), 404

    if post.user_id != user_id:
        return jsonify({
            "error": "You cannot edit another user's post"
        }), 403

    data = request.get_json(silent=True) or request.form

    content = data.get("content", "")
    kind = data.get("kind", post.kind)

    if not isinstance(content, str) or not isinstance(kind, str):
        return jsonify({"error": "Invalid post data"}), 400

    content = content.strip()
    kind = kind.strip().lower()

    image_file = get_uploaded_image()

    remove_existing_image = (
        request.form.get("remove_image") == "true"
    )

    if not content and not (
        (image_file and image_file.filename)
        or (post.image_filename and not remove_existing_image)
    ):
        return jsonify({
            "error": "A post must contain text or a photo."
        }), 400

    if len(content) > 2000:
        return jsonify({"error": "Post cannot exceed 2000 characters"}), 400

    if kind not in ["status", "achievement"]:
        return jsonify({"error": "Invalid post type"}), 400

    new_filename = None

    if image_file and image_file.filename:
        try:
            new_filename = save_image(image_file)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

    old_filename = post.image_filename

    post.content = content
    post.kind = kind

    if new_filename:
        post.image_filename = new_filename
    elif remove_existing_image:
        post.image_filename = None

    try:
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()

        if new_filename:
            remove_image(new_filename)

        return jsonify({"error": "Could not update post"}), 500

    if old_filename and (
        new_filename or remove_existing_image
    ):
        remove_image(old_filename)

    return jsonify({
        "message": "Post updated successfully",
        "id": post.id,
        "content": post.content,
        "kind": post.kind,
        "image_filename": post.image_filename
    }), 200


# --------------------------------------------------
# DELETE POST
# --------------------------------------------------

@posts_bp.route("/post/<int:post_id>/delete", methods=["POST"])
def delete_post(post_id):
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Please log in first"}), 401

    post = db.session.get(Post, post_id)

    if post is None:
        return jsonify({"error": "Post not found"}), 404

    if post.user_id != user_id:
        return jsonify({
            "error": "You cannot delete another user's post"
        }), 403

    filename = post.image_filename

    try:
        # Delete associated likes and comments first.
        Like.query.filter_by(post_id=post_id).delete(
            synchronize_session=False
        )

        Comment.query.filter_by(post_id=post_id).delete(
            synchronize_session=False
        )

        db.session.delete(post)
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Could not delete post"}), 500

    if filename:
        remove_image(filename)

    return jsonify({
        "message": "Post deleted successfully",
        "id": post_id
    }), 200


# --------------------------------------------------
# LIKE POST
# --------------------------------------------------

@posts_bp.route("/post/<int:post_id>/like", methods=["POST"])
def like_post(post_id):
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Please log in first"}), 401

    user = db.session.get(User, user_id)

    if user is None:
        session.clear()
        return jsonify({"error": "Please log in again"}), 401

    post = db.session.get(Post, post_id)

    if post is None:
        return jsonify({"error": "Post not found"}), 404

    existing_like = Like.query.filter_by(
        user_id=user_id,
        post_id=post_id
    ).first()

    if existing_like:
        like_count = Like.query.filter_by(post_id=post_id).count()

        return jsonify({
            "message": "You have already liked this post",
            "liked": True,
            "like_count": like_count
        }), 200

    new_like = Like(
        user_id=user_id,
        post_id=post_id
    )

    try:
        db.session.add(new_like)
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Could not like this post"}), 500

    like_count = Like.query.filter_by(post_id=post_id).count()

    return jsonify({
        "message": "Post liked successfully",
        "liked": True,
        "like_count": like_count
    }), 200


# --------------------------------------------------
# UNLIKE POST
# --------------------------------------------------

@posts_bp.route("/post/<int:post_id>/unlike", methods=["POST"])
def unlike_post(post_id):
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Please log in first"}), 401

    user = db.session.get(User, user_id)

    if user is None:
        session.clear()
        return jsonify({"error": "Please log in again"}), 401

    post = db.session.get(Post, post_id)

    if post is None:
        return jsonify({"error": "Post not found"}), 404

    existing_like = Like.query.filter_by(
        user_id=user_id,
        post_id=post_id
    ).first()

    if existing_like is None:
        like_count = Like.query.filter_by(post_id=post_id).count()

        return jsonify({
            "message": "You have not liked this post",
            "liked": False,
            "like_count": like_count
        }), 200

    try:
        db.session.delete(existing_like)
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Could not unlike this post"}), 500

    like_count = Like.query.filter_by(post_id=post_id).count()

    return jsonify({
        "message": "Post unliked successfully",
        "liked": False,
        "like_count": like_count
    }), 200


# --------------------------------------------------
# ADD COMMENT
# --------------------------------------------------

@posts_bp.route("/post/<int:post_id>/comment", methods=["POST"])
def add_comment(post_id):
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Please log in to comment"}), 401

    user = db.session.get(User, user_id)

    if user is None:
        session.clear()
        return jsonify({"error": "Please log in again"}), 401

    post = db.session.get(Post, post_id)

    if post is None:
        return jsonify({"error": "Post not found"}), 404

    data = request.get_json(silent=True) or request.form
    content = data.get("content", "")

    if not isinstance(content, str):
        return jsonify({"error": "Invalid comment"}), 400

    content = content.strip()

    if not content:
        return jsonify({"error": "Comment cannot be empty"}), 400

    if len(content) > 1000:
        return jsonify({
            "error": "Comment cannot exceed 1000 characters"
        }), 400

    comment = Comment(
        user_id=user_id,
        post_id=post_id,
        content=content
    )

    try:
        db.session.add(comment)
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Could not add comment"}), 500

    return jsonify({
        "message": "Comment added successfully",
        "comment": {
            "id": comment.id,
            "post_id": comment.post_id,
            "user_id": comment.user_id,
            "author": user.name,
            "content": comment.content,
            "created_at": comment.created_at.isoformat()
        }
    }), 201


# --------------------------------------------------
# EDIT COMMENT
# --------------------------------------------------

@posts_bp.route("/comment/<int:comment_id>/edit", methods=["POST"])
def edit_comment(comment_id):
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Please log in first"}), 401

    comment = db.session.get(Comment, comment_id)

    if comment is None:
        return jsonify({"error": "Comment not found"}), 404

    if comment.user_id != user_id:
        return jsonify({
            "error": "You cannot edit another user's comment"
        }), 403

    data = request.get_json(silent=True) or request.form
    content = data.get("content", "")

    if not isinstance(content, str):
        return jsonify({"error": "Invalid comment"}), 400

    content = content.strip()

    if not content:
        return jsonify({"error": "Comment cannot be empty"}), 400

    if len(content) > 1000:
        return jsonify({
            "error": "Comment cannot exceed 1000 characters"
        }), 400

    comment.content = content

    try:
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Could not update comment"}), 500

    return jsonify({
        "message": "Comment updated successfully",
        "id": comment.id,
        "content": comment.content,
        "updated_at": comment.updated_at.isoformat()
    }), 200


# --------------------------------------------------
# DELETE COMMENT
# --------------------------------------------------

@posts_bp.route("/comment/<int:comment_id>/delete", methods=["POST"])
def delete_comment(comment_id):
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Please log in first"}), 401

    comment = db.session.get(Comment, comment_id)

    if comment is None:
        return jsonify({"error": "Comment not found"}), 404

    if comment.user_id != user_id:
        return jsonify({
            "error": "You cannot delete another user's comment"
        }), 403

    try:
        db.session.delete(comment)
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Could not delete comment"}), 500

    return jsonify({
        "message": "Comment deleted successfully",
        "id": comment_id
    }), 200
