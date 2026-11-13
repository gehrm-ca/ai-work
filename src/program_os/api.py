"""FastAPI surface for the V2 Atlas demo."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .agent import run_agent_assessment
from .audit import AuditStore, audit_override, create_override, propose_learning_from_override
from .demo import build_demo_payload
from .evidence import load_evidence_dir
from .models import Rag


DATA_DIR = Path(os.getenv("PROGRAM_OS_ATLAS_DIR", "examples/atlas/data"))
AUDIT_PATH = Path(os.getenv("PROGRAM_OS_AUDIT_PATH", "/tmp/program-os/audit.jsonl"))

app = FastAPI(
    title="Program OS",
    version="0.2.0",
    description="Evidence-grounded portfolio control and decision intelligence.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AssessmentRequest(BaseModel):
    question: str = "Can Atlas launch on December 4, and what should the PM do next?"


class OverrideRequest(BaseModel):
    actor: str
    assessment_id: str
    new_status: Rag
    rationale: str
    missed_context: str | None = None
    exception_type: str = "one_time_exception"
    expected_consequence_if_wrong: str | None = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "0.2.0"}


@app.get("/atlas/demo")
def atlas_demo() -> dict:
    return build_demo_payload(DATA_DIR)


@app.post("/atlas/agent-draft")
def atlas_agent_draft(request: AssessmentRequest) -> dict:
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured; deterministic demo endpoints remain available.",
        )
    evidence = load_evidence_dir(DATA_DIR)
    draft = run_agent_assessment(request.question, evidence)
    return draft.model_dump(mode="json")


@app.post("/atlas/override")
def atlas_override(request: OverrideRequest) -> dict:
    override = create_override(
        actor=request.actor,
        assessment_id=request.assessment_id,
        new_status=request.new_status,
        rationale=request.rationale,
        missed_context=request.missed_context,
        exception_type=request.exception_type,
        expected_consequence_if_wrong=request.expected_consequence_if_wrong,
    )
    event = audit_override(AuditStore(AUDIT_PATH), override)
    learning = propose_learning_from_override(override)
    return {
        "override": override.model_dump(mode="json"),
        "audit_event": event.model_dump(mode="json"),
        "learning_proposal": learning.model_dump(mode="json"),
    }
