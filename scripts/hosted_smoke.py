"""Explicit opt-in smoke run against your configured provider and local, seeded API."""

import argparse
from uuid import uuid4
import httpx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-provider-call", action="store_true", required=True)
    parser.parse_args()
    with httpx.Client(base_url="http://127.0.0.1:8000/api/v1", timeout=150) as client:
        account = client.post(
            "auth/register",
            json={"email": f"provider-check-{uuid4()}@example.invalid", "password": str(uuid4())},
        )
        account.raise_for_status()
        client.headers["x-csrf-token"] = account.json()["csrf"]
        try:
            client.put("privacy/provider-consent", json={"allowed": True}).raise_for_status()
            session = client.post("chat/sessions")
            session.raise_for_status()
            path = f"chat/sessions/{session.json()['id']}/messages"
            for prompt in ["Find remote Python internships for 2028 graduates.", "Only AI/ML ones."]:
                response = client.post(path, json={"message": prompt, "allow_provider": True})
                response.raise_for_status()
                data = response.json()
                assert (
                    data["mode"] == "LLM tool routing" and "search_jobs" in data["tools"] and data["results"]
                ), data["message"]
                assert (
                    data["constraints"].get("mode") == "remote"
                    and data["constraints"].get("graduation_year") == 2028
                )
                for row in data["results"]:
                    assert client.get("jobs/" + row["job"]["id"]).json()["title"] == row["job"]["title"]
                print(
                    {"mode": data["mode"], "tools": data["tools"], "grounded_results": len(data["results"])}
                )
            assert data["constraints"].get("domain", "").casefold() == "ai/ml"
            expected = data["results"][0]["job"]
            explanation = client.post(
                path, json={"message": "Explain the first result.", "allow_provider": True}
            )
            explanation.raise_for_status()
            answer = explanation.json()
            assert answer["mode"] == "LLM tool routing", answer["message"]
            assert any(
                item["tool"] == "explain_job_match" and item["result"]["job"]["id"] == expected["id"]
                for item in answer["evidence"]
            ), answer["message"]
            assert expected["title"] in answer["message"]
            print({"grounded_explanation": True, "tools": answer["tools"]})
        finally:
            client.delete("auth/me").raise_for_status()


if __name__ == "__main__":
    main()
