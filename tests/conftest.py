import os
import sys
import tempfile
from pathlib import Path

import pytest

# Point the import-time init_db() at a throwaway file, never the real employees.db.
os.environ.setdefault(
    "DATABASE_PATH", os.path.join(tempfile.gettempdir(), "employees_import_test.db")
)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app as flask_app, init_db  # noqa: E402


@pytest.fixture
def client(tmp_path):
    flask_app.config.update(TESTING=True, DATABASE=str(tmp_path / "test.db"))
    init_db()
    with flask_app.test_client() as c:
        yield c
