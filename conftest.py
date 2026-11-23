
import os
import tempfile
from pathlib import Path
import pytest

# Create a separate database for pytest
TEST_DB_PATH = Path(tempfile.mkdtemp()) / "test.db"

# Set this BEFORE pytest imports app.py
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"


@pytest.fixture(autouse=True)
def configure_test_app():
    from app import app

    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False
    )

    yield
