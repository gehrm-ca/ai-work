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
from pydantic import BaseModel, Field

from .agent import run_agent_assessment
from .audit import AuditStore, audit_override, create_override, propose_learning_from_override
from .demo import build_demo_payload
from .evidence import index_evidence, load_evidence_dir
from .models import Rag


DEFAULT_DATA_DIR = Path("examples/atlas/data")
DATA_DIR = Path(os.getenv("PROGRAM_OS_ATLAS_DIR", str(DEFAULT_DATA_DIR)))
AUDIT_PATH = Path(os.getenv("PROGRAM_OS_AUDIT_PATH", "/tmp/program-os/audit.jsonl"))
_PROTECTED_CALLS: dict[str, deque[float]] = defaultdict(deque)
_PROTECTED_CALLS_LOCK = threading.Lock()
_LIVE_CALLS_LOCK = threading.Lock()
_LIVE_CALLS_PER_PROCESS = 0


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() in {"1", "true", "yes", "on"}


def live_agent_enabled() -> bool:
    return _env_truthy("PROGRAM_OS_ENABLE_LIVE_AGENT")


def custom_demo_data_configured() -> bool:
    return DATA_DIR != DEFAULT_DATA_DIR


def custom_demo_data_allowed() -> bool:
    return _env_truthy("PROGRAM_OS_ALLOW_CUSTOM_DATA_API")


def max_live_calls_per_process() -> int:
    raw = os.getenv("PROGRAM_OS_MAX_LIVE_CALLS_PER_PROCESS", "10")
    try:
        return max(0, min(int(raw), 1000))
    except ValueError:
        return 10


def _reserve_live_call() -> None:
    global _LIVE_CALLS_PER_PROCESS
    with _LIVE_CALLS_LOCK:
        if _LIVE_CALLS_PER_PROCESS >= max_live_calls_per_process():
            raise HTTPException(status_code=429, detail="Local live-agent call quota reached. Restart only after reviewing spend.")
        _LIVE_CALLS_PER_PROCESS += 1


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


def _authorize_demo_data_request(request: Request) -> None:
    if not custom_demo_data_configured():
        return
    if not custom_demo_data_allowed():
        raise HTTPException(
            status_code=503,
            detail=(
                "Custom demo data is disabled by default. Do not point the local "
                "Atlas API at employer/customer data. If you intentionally need a "
                "custom local dataset, set PROGRAM_OS_ALLOW_CUSTOM_DATA_API=true "
                "and configure PROGRAM_OS_API_TOKEN."
            ),
        )
    _authorize_protected_request(request)


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
    question: str = Field(
        default="Can Atlas launch on December 4, and what should the PM do next?",
        min_length=1,
        max_length=4000,
    )


class OverrideRequest(BaseModel):
    actor: str = Field(min_length=1, max_length=120)
    assessment_id: str = Field(min_length=1, max_length=200)
    new_status: Rag
    rationale: str = Field(min_length=1, max_length=2000)
    missed_context: str | None = Field(default=None, max_length=2000)
    exception_type: str = Field(default="one_time_exception", min_length=1, max_length=120)
    expected_consequence_if_wrong: str | None = Field(default=None, max_length=2000)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "0.2.0"}


@app.get("/capabilities")
def capabilities() -> dict:
    return {
        "deterministic_demo": True,
        "protected_api_auth_configured": protected_api_auth_configured(),
        "live_agent_enabled": live_agent_ready(),
        "custom_demo_data_configured": custom_demo_data_configured(),
        "custom_demo_data_allowed": custom_demo_data_allowed(),
    }


@app.get("/atlas/demo")
def atlas_demo(http_request: Request) -> dict:
    _authorize_demo_data_request(http_request)
    return build_demo_payload(DATA_DIR)


@app.get("/atlas/evidence/{evidence_id}")
def atlas_evidence(evidence_id: str, http_request: Request) -> dict:
    _authorize_demo_data_request(http_request)
    evidence = index_evidence(load_evidence_dir(DATA_DIR)).get(evidence_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail="Evidence record not found.")
    return evidence.model_dump(mode="json")


@app.post("/atlas/agent-draft")
def atlas_agent_draft(request: AssessmentRequest, http_request: Request) -> dict:
    if custom_demo_data_configured() and not custom_demo_data_allowed():
        raise HTTPException(
            status_code=503,
            detail=(
                "Custom demo data is disabled for the live-agent path. Set "
                "PROGRAM_OS_ALLOW_CUSTOM_DATA_API=true only after reviewing the "
                "model-provider data boundary."
            ),
        )
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
    _reserve_live_call()
    evidence = load_evidence_dir(DATA_DIR)
    draft = run_agent_assessment(request.question, evidence)
    # This route is deliberately draft-only. Reject fabricated/unavailable citations.
    from .grounding import GroundingError, validate_citations

    try:
        validate_citations(draft, evidence)
    except GroundingError as exc:
        raise HTTPException(status_code=422, detail="Draft citations failed validation.") from exc
    return {"draft_only": True, "validated_final_assessment": False, **draft.model_dump(mode="json")}


@app.post("/atlas/override")
def atlas_override(request: OverrideRequest, http_request: Request) -> dict:
    _authorize_protected_request(http_request)

    override = create_override(
        # A shared local bearer token proves possession, not a human identity.
        # Never trust the actor field as an authenticated audit principal.
        actor="local-token-holder",
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
