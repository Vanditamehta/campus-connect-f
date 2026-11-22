
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "campusconnect.db")
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

    # Automatically create tables during local development and testing.
    # Set AUTO_CREATE_DB=false in production.
    AUTO_CREATE_DB = (
        os.environ.get("AUTO_CREATE_DB", "true").lower() == "true"
    )

    # Image upload settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
