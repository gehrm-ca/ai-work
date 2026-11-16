from fastapi.testclient import TestClient

import program_os.api as api


client = TestClient(api.app)


def test_live_agent_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("PROGRAM_OS_ENABLE_LIVE_AGENT", raising=False)
    assert api.live_agent_enabled() is False


def test_live_agent_requires_explicit_enable_flag(monkeypatch):
    monkeypatch.setenv("PROGRAM_OS_ENABLE_LIVE_AGENT", "true")
    assert api.live_agent_enabled() is True

    monkeypatch.setenv("PROGRAM_OS_ENABLE_LIVE_AGENT", "false")
    assert api.live_agent_enabled() is False


def test_api_key_alone_does_not_enable_live_agent(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-not-a-real-key")
    monkeypatch.delenv("PROGRAM_OS_ENABLE_LIVE_AGENT", raising=False)
    assert api.live_agent_enabled() is False
    assert api.live_agent_ready() is False


def test_live_agent_is_not_ready_without_protected_api_token(monkeypatch):
    monkeypatch.setenv("PROGRAM_OS_ENABLE_LIVE_AGENT", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-not-a-real-key")
    monkeypatch.delenv("PROGRAM_OS_API_TOKEN", raising=False)
    assert api.live_agent_ready() is False


def test_override_is_disabled_without_api_token(monkeypatch):
    monkeypatch.delenv("PROGRAM_OS_API_TOKEN", raising=False)
    response = client.post(
        "/atlas/override",
        json={
            "actor": "tester",
            "assessment_id": "atlas-portfolio",
            "new_status": "RED",
            "rationale": "Test-only override.",
        },
    )
    assert response.status_code == 503


def test_override_rejects_invalid_bearer_token(monkeypatch):
    monkeypatch.setenv("PROGRAM_OS_API_TOKEN", "expected-test-token")
    response = client.post(
        "/atlas/override",
        headers={"authorization": "Bearer wrong-token"},
        json={
            "actor": "tester",
            "assessment_id": "atlas-portfolio",
            "new_status": "RED",
            "rationale": "Test-only override.",
        },
    )
    assert response.status_code == 401


def test_override_accepts_valid_bearer_token(monkeypatch, tmp_path):
    monkeypatch.setenv("PROGRAM_OS_API_TOKEN", "expected-test-token")
    monkeypatch.setattr(api, "AUDIT_PATH", tmp_path / "audit.jsonl")
    api._PROTECTED_CALLS.clear()

    response = client.post(
        "/atlas/override",
        headers={"authorization": "Bearer expected-test-token"},
        json={
            "actor": "tester",
            "assessment_id": "atlas-portfolio",
            "new_status": "RED",
            "rationale": "Test-only override.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["override"]["actor"] == "tester"
    assert body["learning_proposal"]["approved"] is False


def test_protected_endpoint_rate_limit(monkeypatch, tmp_path):
    monkeypatch.setenv("PROGRAM_OS_API_TOKEN", "expected-test-token")
    monkeypatch.setenv("PROGRAM_OS_PROTECTED_RPM", "1")
    monkeypatch.setattr(api, "AUDIT_PATH", tmp_path / "audit.jsonl")
    api._PROTECTED_CALLS.clear()
    headers = {"authorization": "Bearer expected-test-token"}
    payload = {
        "actor": "tester",
        "assessment_id": "atlas-portfolio",
        "new_status": "RED",
        "rationale": "Test-only override.",
    }

    first = client.post("/atlas/override", headers=headers, json=payload)
    second = client.post("/atlas/override", headers=headers, json=payload)

    assert first.status_code == 200
    assert second.status_code == 429


def test_evidence_endpoint_is_public_and_inspectable():
    response = client.get("/atlas/evidence/ATLAS-101")

    assert response.status_code == 200
    body = response.json()
    assert body["source_type"] == "jira"
    assert body["project_id"] == "PLAT"
    assert body["authority_tier"] == 1
    assert body["payload"]["title"] == "Partner API integration"


def test_evidence_endpoint_returns_404_for_unknown_id():
    response = client.get("/atlas/evidence/NOT-REAL")

    assert response.status_code == 404
