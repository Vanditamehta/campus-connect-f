
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    flash
)

from extensions import db
from models import User, Connection


main_bp = Blueprint("main", __name__)


def get_logged_in_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    user = db.session.get(User, user_id)

    if user is None:
        session.clear()

    return user


# Discover other students
@main_bp.route("/people", methods=["GET"])
def people():
    current_user = get_logged_in_user()

    if current_user is None:
        flash("Please log in to discover students.", "warning")
        return redirect(url_for("auth.login"))

    users = User.query.filter(
        User.id != current_user.id
    ).order_by(User.name.asc()).all()

    followed_ids = {
        connection.followed_id
        for connection in Connection.query.filter_by(
            follower_id=current_user.id
        ).all()
    }

    return render_template(
        "people.html",
        users=users,
        followed_ids=followed_ids,
        current_user=current_user
    )


# View the logged-in user's followers and following
@main_bp.route("/connections", methods=["GET"])
def connections():
    current_user = get_logged_in_user()

    if current_user is None:
        flash("Please log in to view your connections.", "warning")
        return redirect(url_for("auth.login"))

    follower_records = Connection.query.filter_by(
        followed_id=current_user.id
    ).order_by(Connection.created_at.desc()).all()

    following_records = Connection.query.filter_by(
        follower_id=current_user.id
    ).order_by(Connection.created_at.desc()).all()

    followers = [
        db.session.get(User, record.follower_id)
        for record in follower_records
    ]

    following = [
        db.session.get(User, record.followed_id)
        for record in following_records
    ]

    followers = [user for user in followers if user is not None]
    following = [user for user in following if user is not None]

    return render_template(
        "connections.html",
        followers=followers,
        following=following,
        current_user=current_user
    )
