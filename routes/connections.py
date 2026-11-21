
from flask import Blueprint, request, jsonify, session

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from extensions import db
from models import User, Connection


connections_bp = Blueprint("connections", __name__)


def get_logged_in_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    user = db.session.get(User, user_id)

    if user is None:
        session.clear()

    return user


def user_response(user):
    return {
        "id": user.id,
        "name": user.name,
        "headline": user.headline or "",
        "profile_id": user.profile.id if user.profile else None
    }


# List all users except the logged-in user
@connections_bp.route("/api/people", methods=["GET"])
def people():
    current_user = get_logged_in_user()

    if current_user is None:
        return jsonify({"error": "Please log in first."}), 401

    users = User.query.filter(
        User.id != current_user.id
    ).order_by(User.name.asc()).all()

    followed_ids = {
        connection.followed_id
        for connection in Connection.query.filter_by(
            follower_id=current_user.id
        ).all()
    }

    result = []

    for user in users:
        item = user_response(user)
        item["is_following"] = user.id in followed_ids
        result.append(item)

    return jsonify({"people": result}), 200


# Follow another user
@connections_bp.route(
    "/api/follow/<int:user_id>",
    methods=["POST"]
)
def follow_user(user_id):
    current_user = get_logged_in_user()

    if current_user is None:
        return jsonify({"error": "Please log in first."}), 401

    if current_user.id == user_id:
        return jsonify({
            "error": "You cannot follow yourself."
        }), 400

    target_user = db.session.get(User, user_id)

    if target_user is None:
        return jsonify({"error": "User not found."}), 404

    existing = Connection.query.filter_by(
        follower_id=current_user.id,
        followed_id=target_user.id
    ).first()

    if existing:
        return jsonify({
            "error": "You are already following this user."
        }), 409

    connection = Connection(
        follower_id=current_user.id,
        followed_id=target_user.id
    )

    try:
        db.session.add(connection)
        db.session.commit()

    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "This follow relationship already exists."
        }), 409

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({
            "error": "Could not follow this user."
        }), 500

    return jsonify({
        "message": "User followed successfully.",
        "following": user_response(target_user)
    }), 201


# Unfollow a user
@connections_bp.route(
    "/api/unfollow/<int:user_id>",
    methods=["POST"]
)
def unfollow_user(user_id):
    current_user = get_logged_in_user()

    if current_user is None:
        return jsonify({"error": "Please log in first."}), 401

    if current_user.id == user_id:
        return jsonify({
            "error": "You cannot unfollow yourself."
        }), 400

    target_user = db.session.get(User, user_id)

    if target_user is None:
        return jsonify({"error": "User not found."}), 404

    connection = Connection.query.filter_by(
        follower_id=current_user.id,
        followed_id=target_user.id
    ).first()

    if connection is None:
        return jsonify({
            "error": "You are not following this user."
        }), 404

    try:
        db.session.delete(connection)
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({
            "error": "Could not unfollow this user."
        }), 500

    return jsonify({
        "message": "User unfollowed successfully."
    }), 200


# View a user's followers
@connections_bp.route(
    "/api/users/<int:user_id>/followers",
    methods=["GET"]
)
def get_followers(user_id):
    current_user = get_logged_in_user()

    if current_user is None:
        return jsonify({"error": "Please log in first."}), 401

    target_user = db.session.get(User, user_id)

    if target_user is None:
        return jsonify({"error": "User not found."}), 404

    connections = Connection.query.filter_by(
        followed_id=user_id
    ).order_by(Connection.created_at.desc()).all()

    followers = []

    for connection in connections:
        user = db.session.get(User, connection.follower_id)

        if user is not None:
            followers.append(user_response(user))

    return jsonify({
        "user": user_response(target_user),
        "count": len(followers),
        "followers": followers
    }), 200


# View users followed by a user
@connections_bp.route(
    "/api/users/<int:user_id>/following",
    methods=["GET"]
)
def get_following(user_id):
    current_user = get_logged_in_user()

    if current_user is None:
        return jsonify({"error": "Please log in first."}), 401

    target_user = db.session.get(User, user_id)

    if target_user is None:
        return jsonify({"error": "User not found."}), 404

    connections = Connection.query.filter_by(
        follower_id=user_id
    ).order_by(Connection.created_at.desc()).all()

    following = []

    for connection in connections:
        user = db.session.get(User, connection.followed_id)

        if user is not None:
            following.append(user_response(user))

    return jsonify({
        "user": user_response(target_user),
        "count": len(following),
        "following": following
    }), 200


# View the logged-in user's own connection lists
@connections_bp.route(
    "/api/connections",
    methods=["GET"]
)
def my_connections():
    current_user = get_logged_in_user()

    if current_user is None:
        return jsonify({"error": "Please log in first."}), 401

    followers_count = Connection.query.filter_by(
        followed_id=current_user.id
    ).count()

    following_count = Connection.query.filter_by(
        follower_id=current_user.id
    ).count()

    return jsonify({
        "user": user_response(current_user),
        "followers_count": followers_count,
        "following_count": following_count
    }), 200
