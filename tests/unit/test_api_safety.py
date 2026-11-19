import shutil

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


def test_override_rejects_blank_actor_before_audit(monkeypatch):
    monkeypatch.setenv("PROGRAM_OS_API_TOKEN", "expected-test-token")
    api._PROTECTED_CALLS.clear()

    response = client.post(
        "/atlas/override",
        headers={"authorization": "Bearer expected-test-token"},
        json={
            "actor": "",
            "assessment_id": "atlas-portfolio",
            "new_status": "RED",
            "rationale": "Test-only override.",
        },
    )

    assert response.status_code == 422


def test_override_rejects_oversized_rationale_before_audit(monkeypatch):
    monkeypatch.setenv("PROGRAM_OS_API_TOKEN", "expected-test-token")
    api._PROTECTED_CALLS.clear()

    response = client.post(
        "/atlas/override",
        headers={"authorization": "Bearer expected-test-token"},
        json={
            "actor": "tester",
            "assessment_id": "atlas-portfolio",
            "new_status": "RED",
            "rationale": "x" * 2001,
        },
    )

    assert response.status_code == 422


def test_custom_demo_data_is_blocked_without_explicit_opt_in(monkeypatch, tmp_path):
    custom = tmp_path / "private-demo-data"
    shutil.copytree("examples/atlas/data", custom)
    monkeypatch.setattr(api, "DATA_DIR", custom)
    monkeypatch.delenv("PROGRAM_OS_ALLOW_CUSTOM_DATA_API", raising=False)
    monkeypatch.delenv("PROGRAM_OS_API_TOKEN", raising=False)

    response = client.get("/atlas/demo")

    assert response.status_code == 503
    assert "Custom demo data is disabled" in response.json()["detail"]


def test_custom_demo_data_requires_bearer_auth_when_opted_in(monkeypatch, tmp_path):
    custom = tmp_path / "private-demo-data"
    shutil.copytree("examples/atlas/data", custom)
    monkeypatch.setattr(api, "DATA_DIR", custom)
    monkeypatch.setenv("PROGRAM_OS_ALLOW_CUSTOM_DATA_API", "true")
    monkeypatch.setenv("PROGRAM_OS_API_TOKEN", "expected-test-token")
    api._PROTECTED_CALLS.clear()

    unauthenticated = client.get("/atlas/demo")
    authenticated = client.get(
        "/atlas/demo",
        headers={"authorization": "Bearer expected-test-token"},
    )

    assert unauthenticated.status_code == 401
    assert authenticated.status_code == 200
    assert authenticated.json()["evidence_count"] == 48


def test_custom_evidence_endpoint_requires_bearer_auth_when_opted_in(monkeypatch, tmp_path):
    custom = tmp_path / "private-demo-data"
    shutil.copytree("examples/atlas/data", custom)
    monkeypatch.setattr(api, "DATA_DIR", custom)
    monkeypatch.setenv("PROGRAM_OS_ALLOW_CUSTOM_DATA_API", "true")
    monkeypatch.setenv("PROGRAM_OS_API_TOKEN", "expected-test-token")
    api._PROTECTED_CALLS.clear()

    response = client.get(
        "/atlas/evidence/ATLAS-101",
        headers={"authorization": "Bearer expected-test-token"},
    )

    assert response.status_code == 200
    assert response.json()["evidence_id"] == "ATLAS-101"


def test_live_call_quota_blocks_when_exhausted(monkeypatch):
    from fastapi import HTTPException

    monkeypatch.setenv("PROGRAM_OS_MAX_LIVE_CALLS_PER_PROCESS", "1")
    monkeypatch.setattr(api, "_LIVE_CALLS_PER_PROCESS", 0)
    api._reserve_live_call()
    try:
        api._reserve_live_call()
        assert False, "Quota should have rejected the second model call"
    except HTTPException as exc:
        assert exc.status_code == 429


def test_agent_draft_citation_validation_failure(monkeypatch):
    from program_os.agent import AgentAssessmentDraft
    from program_os.models import Rag, Trend

    monkeypatch.setenv("PROGRAM_OS_API_TOKEN", "expected-test-token")
    monkeypatch.setenv("PROGRAM_OS_ENABLE_LIVE_AGENT", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "fake-test-key")
    monkeypatch.setattr(api, "_LIVE_CALLS_PER_PROCESS", 0)
    api._PROTECTED_CALLS.clear()
    monkeypatch.setattr(api, "run_agent_assessment", lambda question, evidence: AgentAssessmentDraft(
        proposed_rag=Rag.GREEN,
        trend=Trend.STABLE,
        conclusion="Fabricated evidence.",
        cited_evidence_ids=["FAKE-CITATION"],
    ))
    response = client.post("/atlas/agent-draft",
        headers={"authorization": "Bearer expected-test-token"},
        json={"question": "Assess Atlas."})
    assert response.status_code == 422
    assert "failed validation" in response.json()["detail"]
