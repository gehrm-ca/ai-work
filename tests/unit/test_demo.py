from pathlib import Path

from program_os.demo import build_demo_payload, build_friday_status


DATA = Path("examples/atlas/data")


def test_demo_has_prioritized_monday_actions():
    payload = build_demo_payload(DATA)
    actions = payload["monday_actions"]
    assert len(actions) >= 6
    scores = [item["priority_score"] for item in actions]
    assert scores == sorted(scores, reverse=True)
    assert all(item["evidence_ids"] for item in actions)


def test_friday_status_preserves_official_vs_forecast():
    status = build_friday_status(DATA)
    assert status.official_rag.value == "GREEN"
    assert status.forecast_rag.value == "AMBER"
    assert status.confidence.value == "Moderate"
    assert status.contradictions


def test_demo_exposes_inspectable_evidence_records():
    payload = build_demo_payload(DATA)
    records = payload["evidence_records"]

    assert len(records) == 48
    assert {item["evidence_id"] for item in records} == {
        item["source_id"] for item in records
    }
    sample = next(item for item in records if item["evidence_id"] == "ATLAS-101")
    assert sample["source_type"] == "jira"
    assert sample["authority_tier"] == 1
    assert sample["payload"]["title"] == "Partner API integration"
