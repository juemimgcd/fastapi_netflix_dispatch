import os

from fastapi.testclient import TestClient

# Ensure settings can be constructed in test env.
os.environ.setdefault("ASYNC_DATABASE_URL", "postgresql+asyncpg://dispatch:dispatch@localhost:5432/dispatch")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET", "test-secret")

from main import app  # noqa: E402


def test_root() -> None:
    with TestClient(app) as client:
        resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Hello World"}


def test_hello() -> None:
    with TestClient(app) as client:
        resp = client.get("/hello/Codex")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Hello Codex"}

