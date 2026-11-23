
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Application environment
APP_ENV = os.environ.get("APP_ENV", "development").lower()

# Secret key configuration
SECRET_KEY = os.environ.get("SECRET_KEY")

if APP_ENV == "production":
    if not SECRET_KEY or len(SECRET_KEY) < 32:
        raise RuntimeError(
            "Production requires a SECRET_KEY of at least 32 characters."
        )
elif not SECRET_KEY:
    SECRET_KEY = "dev-only-secret-key-for-local-development"


# Database configuration
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///" + os.path.join(BASE_DIR, "campusconnect.db")
)

# Production must use PostgreSQL, not SQLite
if APP_ENV == "production" and not DATABASE_URL.startswith(
    ("postgres://", "postgresql://", "postgresql+psycopg://")
):
    raise RuntimeError(
        "Production requires a PostgreSQL DATABASE_URL."
    )

# Convert PostgreSQL URLs to use Psycopg 3
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql+psycopg://",
        1
    )
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1
    )


class Config:
    SQLALCHEMY_DATABASE_URI = DATABASE_URL

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = SECRET_KEY

    # Automatically create tables during local development and testing.
    # Set AUTO_CREATE_DB=false in production.
    AUTO_CREATE_DB = (
        os.environ.get("AUTO_CREATE_DB", "true").lower() == "true"
    )

    # Image upload settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
