import os
from uuid import uuid4
from fastapi.testclient import TestClient
import pytest
from app.main import app

pytestmark = pytest.mark.skipif(
    os.getenv("CG_SEEDED_TESTS") != "1", reason="requires default synthetic seed and embeddings"
)


def test_conversations():
    with TestClient(app) as client:
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": f"{uuid4()}@example.invalid", "password": "synthetic-account-123"},
        )
        client.headers["x-csrf-token"] = reg.json()["csrf"]

        def new():
            return client.post("/api/v1/chat/sessions").json()["id"]

        def send(s, msg):
            response = client.post(f"/api/v1/chat/sessions/{s}/messages", json={"message": msg})
            assert response.status_code == 200, response.text
            return response.json()

        a = new()
        assert "search_jobs" in send(a, "Find remote Python internships for 2028 graduates")["tools"]
        send(a, "Only AI/ML ones")
        result = send(a, "At least 50,000 INR per month")
        assert result["constraints"]["graduation_year"] == 2028 and result["results"]
        assert all(r["job"]["mode"] in ("remote", None) for r in result["results"])
        top = result["results"][0]["job"]["id"]
        assert send(a, "Explain the best match")["evidence"][0]["result"]["job"]["id"] == top
        b = new()
        send(b, "Find backend internships")
        assert (
            send(b, "Exclude jobs requiring three years of professional experience")["constraints"][
                "max_experience"
            ]
            < 3
        )
        assert len(send(b, "Compare the top two jobs")["evidence"][0]["result"]) == 2
        c = new()
        send(c, "Find ML internships")
        assert send(c, "Remember that I prefer retrieval and search engineering")["pending_preference"]
        assert client.get("/api/v1/preferences").json()["preferences"] == []
        send(c, "confirm")
        assert client.get("/api/v1/preferences").json()["preferences"] == ["retrieval and search engineering"]
        assert send(c, "Show newly ranked jobs")["results"]
        assert client.delete("/api/v1/auth/me").status_code == 200


def test_negative_followup_keeps_session_on_conflict():
    with TestClient(app) as client:
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": f"{uuid4()}@example.invalid", "password": "synthetic-account-123"},
        )
        client.headers["x-csrf-token"] = reg.json()["csrf"]
        sid = client.post("/api/v1/chat/sessions").json()["id"]

        def turn(message):
            r = client.post(f"/api/v1/chat/sessions/{sid}/messages", json={"message": message})
            assert r.status_code == 200, r.text
            return r.json()

        try:
            assert turn("Find Python internships")["constraints"]["employment"] == "internship"
            result = turn("No onsite roles please")
            assert result["constraints"]["exclude_mode"] == ["onsite"]
            assert result["results"] and all(item["job"]["mode"] != "onsite" for item in result["results"])
            result = turn("I do not want internships")
            assert result["constraints"]["employment"] == "internship"
            assert "conflict" in result["message"].lower() and result["tools"] == []
            assert turn("clear filters")["constraints"] == {}
        finally:
            client.delete("/api/v1/auth/me")
