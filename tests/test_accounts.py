import os
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from app.main import app

pytestmark = pytest.mark.skipif(
    os.getenv("CG_INTEGRATION") != "1", reason="requires a migrated test database"
)


def test_account_isolation_and_deletion():
    with TestClient(app) as first, TestClient(app) as second:
        for client in (first, second):
            credentials = {"email": f"{uuid4()}@example.invalid", "password": "synthetic-account-123"}
            reg = client.post("/api/v1/auth/register", json=credentials)
            assert reg.status_code == 201, reg.text
            client.headers["x-csrf-token"] = reg.json()["csrf"]
        r = first.put("/api/v1/profile", json={"name": "Example", "skills": ["Python"]})
        assert r.status_code == 200, r.text
        assert second.get("/api/v1/profile").json()["profile"]["name"] == ""
        sid = first.post("/api/v1/chat/sessions").json()["id"]
        assert second.get(f"/api/v1/chat/sessions/{sid}/messages").status_code == 404
        assert first.get("/api/v1/admin/ingestion").status_code == 403
        assert (
            first.put(
                "/api/v1/preferences", json={"preferences": ["retrieval"]}, headers={"x-csrf-token": "wrong"}
            ).status_code
            == 403
        )
        for client in (first, second):
            assert client.delete("/api/v1/auth/me").status_code == 200
            assert client.get("/api/v1/auth/me").status_code == 401


@pytest.mark.skipif(os.getenv("CG_INTEGRATION") != "1", reason="migrated database required")
def test_consent_is_account_scoped_and_revocable(monkeypatch):
    from app.core.config import settings
    from app.agents import orchestrator

    monkeypatch.setattr(settings, "llm_api_key", "test-double")
    monkeypatch.setattr(settings, "llm_model", "fixture")

    def forbidden(*args):
        raise AssertionError("Network path reached without consent")

    monkeypatch.setattr(orchestrator, "completion", forbidden)
    with TestClient(app) as client:
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": f"{uuid4()}@example.invalid", "password": "synthetic-account-123"},
        )
        client.headers["x-csrf-token"] = reg.json()["csrf"]
        assert client.get("/api/v1/auth/me").json()["provider_consent"] is False
        sid = client.post("/api/v1/chat/sessions").json()["id"]

        def message():
            return client.post(
                f"/api/v1/chat/sessions/{sid}/messages",
                json={"message": "Remember that I prefer backend", "allow_provider": True},
            ).json()

        assert message()["mode"].startswith("Deterministic")
        for flag in (True, False):
            assert client.put("/api/v1/privacy/provider-consent", json={"allowed": flag}).status_code == 200
            assert client.get("/api/v1/auth/me").json()["provider_consent"] is flag
        assert message()["mode"].startswith("Deterministic")
        assert (
            client.post(
                "/api/v1/profile/resume?hosted=true",
                files={"file": ("cv.pdf", b"%PDF-test", "application/pdf")},
            ).status_code
            == 403
        )
        client.delete("/api/v1/auth/me")
