
from datetime import datetime, timezone

from extensions import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    headline = db.Column(db.String(150), default="")
    password_hash = db.Column(db.String(256), nullable=True)

    profile = db.relationship(
        "Profile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )


class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
        unique=True
    )

    name = db.Column(db.String(100), nullable=False)
    skills = db.Column(db.JSON, nullable=False)
    specialization = db.Column(db.String(150), default="")
    bio = db.Column(db.Text, default="")

    user = db.relationship("User", back_populates="profile")


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    content = db.Column(db.String(2000), nullable=False)

    # Optional photo attached to the post
    image_filename = db.Column(db.String(255), nullable=True)

    kind = db.Column(
        db.String(20),
        nullable=False,
        default="status"
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    author = db.relationship("User", backref="posts")


class Connection(db.Model):
    __tablename__ = "connection"

    id = db.Column(db.Integer, primary_key=True)

    follower_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False
    )

    followed_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        db.UniqueConstraint(
            "follower_id",
            "followed_id",
            name="unique_follow_relationship"
        ),
        db.CheckConstraint(
            "follower_id != followed_id",
            name="prevent_self_follow"
        ),
    )
