from pathlib import Path

from program_os.audit import AuditStore, audit_override, create_override, propose_learning_from_override
from program_os.models import Rag


def test_override_is_audited_without_changing_system_behavior(tmp_path: Path):
    store = AuditStore(tmp_path / "audit.jsonl")
    override = create_override(
        actor="pm-1",
        assessment_id="asmt-1",
        new_status=Rag.GREEN,
        rationale="Customer fallback is contractually approved.",
        missed_context="Approved fallback not present in source evidence.",
        exception_type="one_time_exception",
        expected_consequence_if_wrong="Launch dependency may fail.",
    )
    event = audit_override(store, override)
    learning = propose_learning_from_override(override)

    assert event.event_type == "assessment_override"
    assert len(store.read_all()) == 1
    assert learning.approved is False
    assert learning.effective_version is None


def test_audit_chain_detects_modified_record(tmp_path: Path):
    import json
    store = AuditStore(tmp_path / "audit.jsonl")
    for i in range(2):
        override = create_override(
            actor="local-operator", assessment_id=f"asmt-{i}", new_status=Rag.AMBER,
            rationale="Needs review.", missed_context=None, exception_type="one_time_exception",
            expected_consequence_if_wrong=None,
        )
        audit_override(store, override)
    assert store.verify_integrity() is True
    records = store.read_all()
    records[0]["actor"] = "impersonated"
    store.path.write_text("\n".join(json.dumps(row) for row in records) + "\n")
    assert store.verify_integrity() is False
