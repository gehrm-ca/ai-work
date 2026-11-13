"""Append-only override audit and governed learning proposal helpers."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .models import AuditEvent, LearningProposal, Override, Rag


class AuditStore:
    def __init__(self, path: Path):
        self.path = path

    def append(self, event: AuditEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.model_dump(mode="json"), sort_keys=True) + "\n")

    def read_all(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [
            json.loads(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


def create_override(
    *,
    actor: str,
    assessment_id: str,
    new_status: Rag,
    rationale: str,
    missed_context: str | None,
    exception_type: str,
    expected_consequence_if_wrong: str | None,
) -> Override:
    return Override(
        override_id=f"ovr-{uuid4().hex[:12]}",
        assessment_id=assessment_id,
        actor=actor,
        new_status=new_status,
        rationale=rationale,
        missed_context=missed_context,
        exception_type=exception_type,
        expected_consequence_if_wrong=expected_consequence_if_wrong,
        created_at=datetime.now(timezone.utc),
    )


def audit_override(store: AuditStore, override: Override) -> AuditEvent:
    event = AuditEvent(
        event_id=f"audit-{uuid4().hex[:12]}",
        actor=override.actor,
        event_type="assessment_override",
        entity_type="Assessment",
        entity_id=override.assessment_id or "unknown",
        before=None,
        after=override.model_dump(mode="json"),
        created_at=datetime.now(timezone.utc),
    )
    store.append(event)
    return event


def propose_learning_from_override(override: Override) -> LearningProposal:
    return LearningProposal(
        proposal_id=f"learn-{uuid4().hex[:12]}",
        triggering_case_ids=[override.assessment_id or override.override_id],
        failure_category="human_override_review",
        root_cause_hypothesis=(
            "The system may have missed project-specific context or may need a "
            "better decision rule; outcome evidence is required before deciding."
        ),
        proposed_change=(
            "Review the override and eventual outcome. If the pattern repeats, "
            "propose a scoped rule, prompt, retrieval, or data-model change."
        ),
        expected_improvement="Improve future judgment without treating one override as truth.",
        possible_regressions=[
            "Overfitting a one-time exception",
            "Weakening a valid hard gate",
            "Increasing false confidence",
        ],
        approved=False,
        rollback="No runtime behavior is changed until an approved versioned proposal exists.",
    )
