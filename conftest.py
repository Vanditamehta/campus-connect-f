import os
import tempfile
from pathlib import Path

# Create a separate database for pytest
TEST_DB_PATH = Path(tempfile.mkdtemp()) / "test.db"

# Set this BEFORE pytest imports app.py
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
