
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    flash,
    request
)

from extensions import db

from models import (
    User,
    Profile,
    Connection,
    Post,
    Comment,
    Like,
    ProfileSection
)


main_bp = Blueprint("main", __name__)


def get_logged_in_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    user = db.session.get(User, user_id)

    if user is None:
        session.clear()

    return user


# =====================================================
# VIEW ANOTHER STUDENT'S PUBLIC PROFILE
# =====================================================

@main_bp.route("/people/profile/<int:user_id>", methods=["GET"])
def public_profile(user_id):

    student = db.session.get(User, user_id)

    if student is None:
        flash("Student not found.", "danger")
        return redirect(url_for("main.people"))

    student_profile = Profile.query.filter_by(
        user_id=student.id
    ).first()

    if student_profile is None:
        flash("This student has not created a profile yet.", "info")
        return redirect(url_for("main.people"))

    is_owner = session.get("user_id") == student.id

    # Fetch the student's profile sections
    profile_sections = (
        ProfileSection.query
        .filter_by(user_id=student.id)
        .order_by(ProfileSection.id.asc())
        .all()
    )

    # Fetch the student's recent posts
    recent_posts = (
        Post.query
        .filter_by(user_id=student.id)
        .order_by(Post.created_at.desc(), Post.id.desc())
        .limit(10)
        .all()
    )

    # Fetch the student's recent comments
    recent_comments = (
        Comment.query
        .filter_by(user_id=student.id)
        .order_by(Comment.created_at.desc(), Comment.id.desc())
        .limit(10)
        .all()
    )

    # Fetch the student's recent reactions
    recent_reactions = (
        Like.query
        .filter_by(user_id=student.id)
        .order_by(Like.created_at.desc(), Like.id.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "profile.html",
        profile=student_profile,
        user=student,
        is_owner=is_owner,
        profile_sections=profile_sections,
        recent_posts=recent_posts,
        recent_comments=recent_comments,
        recent_reactions=recent_reactions
    )


# =====================================================
# DISCOVER AND SEARCH STUDENTS
# =====================================================

@main_bp.route("/people", methods=["GET"])
def people():

    current_user = get_logged_in_user()

    if current_user is None:
        flash("Please log in to discover students.", "warning")
        return redirect(url_for("auth.login"))

    search_query = request.args.get("q", "").strip()
    skill_query = request.args.get("skill", "").strip()

    users_query = User.query.filter(
        User.id != current_user.id
    )

    # Search students by name
    if search_query:
        users_query = users_query.filter(
            User.name.ilike(f"%{search_query}%")
        )

    users = users_query.order_by(User.name.asc()).all()

    # Filter students by skill
    if skill_query:

        filtered_users = []

        for user in users:

            profile = user.profile

            if profile and profile.skills:

                skills = profile.skills

                if isinstance(skills, str):
                    skills = [skills]

                if any(
                    skill_query.lower() in str(skill).lower()
                    for skill in skills
                ):
                    filtered_users.append(user)

        users = filtered_users

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
        current_user=current_user,
        search_query=search_query,
        skill_query=skill_query
    )


# =====================================================
# FOLLOW A STUDENT
# =====================================================

@main_bp.route("/people/follow/<int:user_id>", methods=["POST"])
def follow_user(user_id):

    current_user = get_logged_in_user()

    if current_user is None:
        flash("Please log in to follow students.", "warning")
        return redirect(url_for("auth.login"))

    if current_user.id == user_id:
        flash("You cannot follow yourself.", "warning")
        return redirect(url_for("main.people"))

    target_user = db.session.get(User, user_id)

    if target_user is None:
        flash("Student not found.", "danger")
        return redirect(url_for("main.people"))

    existing_connection = Connection.query.filter_by(
        follower_id=current_user.id,
        followed_id=user_id
    ).first()

    if existing_connection:
        flash("You are already following this student.", "info")
        return redirect(url_for("main.people"))

    try:

        connection = Connection(
            follower_id=current_user.id,
            followed_id=user_id
        )

        db.session.add(connection)
        db.session.commit()

        flash(
            f"You are now following {target_user.name}.",
            "success"
        )

    except Exception:

        db.session.rollback()

        flash(
            "Unable to follow this student. Please try again.",
            "danger"
        )

    return redirect(url_for("main.people"))


# =====================================================
# UNFOLLOW A STUDENT
# =====================================================

@main_bp.route("/people/unfollow/<int:user_id>", methods=["POST"])
def unfollow_user(user_id):

    current_user = get_logged_in_user()

    if current_user is None:
        flash("Please log in to manage connections.", "warning")
        return redirect(url_for("auth.login"))

    connection = Connection.query.filter_by(
        follower_id=current_user.id,
        followed_id=user_id
    ).first()

    if connection is None:
        flash("You are not following this student.", "warning")
        return redirect(url_for("main.people"))

    try:

        db.session.delete(connection)
        db.session.commit()

        flash("Student unfollowed successfully.", "success")

    except Exception:

        db.session.rollback()

        flash(
            "Unable to unfollow this student.",
            "danger"
        )

    return redirect(url_for("main.people"))


# =====================================================
# VIEW FOLLOWERS AND FOLLOWING
# =====================================================

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

    followers = [
        user for user in followers
        if user is not None
    ]

    following = [
        user for user in following
        if user is not None
    ]

    return render_template(
        "connections.html",
        followers=followers,
        following=following,
        current_user=current_user
    )
