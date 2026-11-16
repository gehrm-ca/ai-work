"""FastAPI surface for the V2 Atlas demo."""
from __future__ import annotations

import os
import secrets
import threading
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .agent import run_agent_assessment
from .audit import AuditStore, audit_override, create_override, propose_learning_from_override
from .demo import build_demo_payload
from .evidence import load_evidence_dir
from .models import Rag


DATA_DIR = Path(os.getenv("PROGRAM_OS_ATLAS_DIR", "examples/atlas/data"))
AUDIT_PATH = Path(os.getenv("PROGRAM_OS_AUDIT_PATH", "/tmp/program-os/audit.jsonl"))
_PROTECTED_CALLS: dict[str, deque[float]] = defaultdict(deque)
_PROTECTED_CALLS_LOCK = threading.Lock()


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() in {"1", "true", "yes", "on"}


def live_agent_enabled() -> bool:
    return _env_truthy("PROGRAM_OS_ENABLE_LIVE_AGENT")


def protected_api_auth_configured() -> bool:
    return bool(os.getenv("PROGRAM_OS_API_TOKEN"))


def live_agent_ready() -> bool:
    return (
        live_agent_enabled()
        and protected_api_auth_configured()
        and bool(os.getenv("OPENAI_API_KEY"))
    )


def _protected_rate_limit_per_minute() -> int:
    raw = os.getenv("PROGRAM_OS_PROTECTED_RPM", "30").strip()
    try:
        value = int(raw)
    except ValueError:
        value = 30
    return max(1, min(value, 600))


def _authorize_protected_request(request: Request) -> None:
    expected = os.getenv("PROGRAM_OS_API_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=503,
            detail=(
                "Protected API operations are disabled. Configure PROGRAM_OS_API_TOKEN "
                "before enabling overrides or live agent calls."
            ),
        )

    authorization = request.headers.get("authorization", "")
    scheme, _, supplied = authorization.partition(" ")
    if scheme.lower() != "bearer" or not supplied or not secrets.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Valid bearer authentication is required.")

    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    cutoff = now - 60.0
    limit = _protected_rate_limit_per_minute()
    with _PROTECTED_CALLS_LOCK:
        calls = _PROTECTED_CALLS[client]
        while calls and calls[0] < cutoff:
            calls.popleft()
        if len(calls) >= limit:
            raise HTTPException(
                status_code=429,
                detail="Protected API rate limit exceeded. Retry after the current minute window.",
            )
        calls.append(now)


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


@app.get("/capabilities")
def capabilities() -> dict:
    return {
        "deterministic_demo": True,
        "protected_api_auth_configured": protected_api_auth_configured(),
        "live_agent_enabled": live_agent_ready(),
    }


@app.get("/atlas/demo")
def atlas_demo() -> dict:
    return build_demo_payload(DATA_DIR)


@app.post("/atlas/agent-draft")
def atlas_agent_draft(request: AssessmentRequest, http_request: Request) -> dict:
    if not live_agent_enabled():
        raise HTTPException(
            status_code=503,
            detail=(
                "Live agent calls are disabled. Set "
                "PROGRAM_OS_ENABLE_LIVE_AGENT=true explicitly to enable them."
            ),
        )

    _authorize_protected_request(http_request)

    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured; deterministic demo endpoints remain available.",
        )
    evidence = load_evidence_dir(DATA_DIR)
    draft = run_agent_assessment(request.question, evidence)
    return draft.model_dump(mode="json")


@app.post("/atlas/override")
def atlas_override(request: OverrideRequest, http_request: Request) -> dict:
    _authorize_protected_request(http_request)

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
