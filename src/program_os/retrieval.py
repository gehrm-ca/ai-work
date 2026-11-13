"""Small, inspectable retrieval layer for the V2 vertical slice.

The V2 prototype starts with deterministic lexical/entity retrieval. pgvector is
an architectural target, not a requirement for proving the trust and decision loop.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Iterable

from .models import Evidence

_TOKEN_RE = re.compile(r"[a-z0-9_/-]{3,}")


@dataclass(frozen=True)
class RetrievalHit:
    evidence: Evidence
    score: float
    matched_terms: tuple[str, ...]


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def retrieve_evidence(
    evidence: Iterable[Evidence],
    query: str,
    *,
    project_ids: Iterable[str] = (),
    limit: int = 12,
) -> list[RetrievalHit]:
    query_terms = _tokens(query)
    projects = set(project_ids)
    hits: list[RetrievalHit] = []

    for item in evidence:
        haystack = " ".join(
            (
                item.evidence_id,
                item.source_type,
                item.project_id,
                json.dumps(item.payload, sort_keys=True),
            )
        ).lower()
        matched = tuple(sorted(term for term in query_terms if term in haystack))
        score = float(len(matched))

        if item.project_id in projects:
            score += 4.0
        if item.project_id == "atlas" and projects:
            score += 1.0
        score += max(0.0, 1.25 - (0.25 * item.authority_tier))

        if score > 0:
            hits.append(RetrievalHit(item, score, matched))

    hits.sort(
        key=lambda hit: (
            hit.score,
            hit.evidence.source_updated_at,
            -hit.evidence.authority_tier,
        ),
        reverse=True,
    )
    return hits[:limit]
