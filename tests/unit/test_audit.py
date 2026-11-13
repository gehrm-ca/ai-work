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
