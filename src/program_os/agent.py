"""Single-agent structured assessment adapter.

The agent interprets ambiguous evidence. Grounding, confidence, and hard RAG
constraints are applied outside the model in grounding.py.
"""
from __future__ import annotations

import json
from typing import Iterable

from agents import Agent, Runner
from pydantic import BaseModel, Field

from .models import Evidence, Rag, Trend


class AgentAssessmentDraft(BaseModel):
    proposed_rag: Rag
    trend: Trend
    conclusion: str
    risks: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    cited_evidence_ids: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)


INSTRUCTIONS = """You are the Program OS portfolio analyst.

Use only the evidence provided in the current request. Do not use outside facts.

Rules:
1. Distinguish official reported status from your forecast.
2. Cite source IDs for every material conclusion.
3. Surface conflicting evidence; never invent ground truth to reconcile it.
4. Treat stale evidence as weaker than fresher operational evidence, but do not
   assume freshness alone establishes truth.
5. Say what is missing when evidence is insufficient.
6. Do not claim a risk is official merely because you inferred it.
7. Do not make consequential project changes; recommend actions for human review.
8. Prefer "insufficient evidence" to unsupported certainty.
9. When proposing a portfolio tradeoff, state the downside imposed elsewhere.
10. Apply this RAG rubric:
    - GREEN: no material blocker or unresolved risk for the subject being assessed,
      with required evidence sufficiently verified.
    - AMBER: a material risk, gap, contradiction, or threshold miss exists, but
      recovery/validation remains plausible or the ultimate consequence is not yet
      established.
    - RED: an explicit launch-critical blocker exists, a committed outcome is
      likely unachievable, or a critical dependency misses the committed outcome
      with no viable mitigation.
    Do not use RED merely because a risk is high, evidence is incomplete, or a
    recovery plan is weak.
11. Assess the subject asked about. Do not import unrelated portfolio risks unless
    they materially change the answer.
12. When a scenario state is explicitly supplied, treat it as the current state
    for that evaluation and treat conflicting source records as historical state.
13. Return the structured output only.
"""


def build_agent() -> Agent:
    return Agent(
        name="Program OS Analyst",
        instructions=INSTRUCTIONS,
        output_type=AgentAssessmentDraft,
    )


def render_evidence(evidence: Iterable[Evidence]) -> str:
    records = []
    for item in evidence:
        records.append({
            "evidence_id": item.evidence_id,
            "source_type": item.source_type,
            "project_id": item.project_id,
            "source_updated_at": item.source_updated_at.isoformat(),
            "retrieved_at": item.retrieved_at.isoformat(),
            "authority_tier": item.authority_tier,
            "payload": item.payload,
        })
    return json.dumps(records, indent=2, default=str)


def run_agent_assessment(question: str, evidence: Iterable[Evidence]) -> AgentAssessmentDraft:
    evidence = list(evidence)
    prompt = (
        f"QUESTION\n{question}\n\n"
        "EVIDENCE\n"
        f"{render_evidence(evidence)}\n\n"
        "Assess forecast status, contradictions, risks, uncertainty, and recommended human actions."
    )
    result = Runner.run_sync(build_agent(), prompt)
    output = result.final_output
    if not isinstance(output, AgentAssessmentDraft):
        raise TypeError("Agent returned an unexpected output type.")
    return output
