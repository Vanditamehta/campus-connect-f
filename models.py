
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

    social_links = db.relationship(
        "SocialLink",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="SocialLink.id"
    )

    profile_sections = db.relationship(
        "ProfileSection",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="ProfileSection.id"
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

    profile_image_filename = db.Column(
        db.String(255),
        nullable=True
    )

    user = db.relationship("User", back_populates="profile")


class SocialLink(db.Model):
    __tablename__ = "social_link"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False
    )

    title = db.Column(
        db.String(50),
        nullable=False
    )

    url = db.Column(
        db.String(500),
        nullable=False
    )

    user = db.relationship(
        "User",
        back_populates="social_links"
    )


class ProfileSection(db.Model):
    __tablename__ = "profile_section"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False
    )

    section_type = db.Column(
        db.String(50),
        nullable=False
    )

    data = db.Column(
        db.JSON,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    user = db.relationship(
        "User",
        back_populates="profile_sections"
    )


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    content = db.Column(db.String(2000), nullable=False)
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


class Like(db.Model):
    __tablename__ = "like"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False
    )

    post_id = db.Column(
        db.Integer,
        db.ForeignKey("post.id", ondelete="CASCADE"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "post_id",
            name="unique_user_post_like"
        ),
    )

    user = db.relationship("User", backref="likes")
    post = db.relationship("Post", backref="likes")


class Comment(db.Model):
    __tablename__ = "comment"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False
    )

    post_id = db.Column(
        db.Integer,
        db.ForeignKey("post.id", ondelete="CASCADE"),
        nullable=False
    )

    content = db.Column(db.String(1000), nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    user = db.relationship("User", backref="comments")
    post = db.relationship("Post", backref="comments")
