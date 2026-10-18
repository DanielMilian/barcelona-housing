import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg2://{u}:{p}@localhost:{port}/{db}".format(
        u=os.environ["WAREHOUSE_USER"],
        p=os.environ["WAREHOUSE_PASSWORD"],
        port=os.environ["WAREHOUSE_PORT"],
        db=os.environ["WAREHOUSE_DB"],
    ),
)
os.environ["API_KEY"] = "test-key"

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session")
def client():
    return TestClient(app, headers={"X-API-Key": "test-key"})
