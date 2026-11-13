"""Live baseline-vs-Program-OS evaluation runner.

Gold expectations are never included in prompts. They are loaded only after
model outputs are produced and are used solely for scoring.
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from agents import Agent, Runner
from pydantic import BaseModel, Field

from program_os.agent import AgentAssessmentDraft, run_agent_assessment
from program_os.confidence import ConfidenceInputs
from program_os.controls import ControlContext
from program_os.evidence import index_evidence, load_evidence_dir
from program_os.grounding import finalize_assessment
from program_os.models import ConfidenceBand, Evidence, Rag
from program_os.retrieval import retrieve_evidence
from program_os.signals import detect_signals

from .baseline import build_baseline_prompt, load_raw_context
from .gold import load_gold_cases
from .scoring import EvalFailure, summarize_failures


CASE_QUERIES = {
    "E01": "Is the partner integration still on schedule, and what should the PM do next?",
    "E02": "How credible is the current partner-integration recovery plan?",
    "E03": "Is export filtering approved launch scope, and what needs to happen next?",
    "E04": "Do we have a resource conflict affecting Platform and AI delivery?",
    "E05": "What does the current defect trend imply for launch readiness?",
    "E06": "Is the compliance approval path creating a launch-readiness risk?",
    "E07": "At the launch gate, can the program be GREEN if required compliance approval is not verified?",
    "E08": "Does the current executive GREEN still match fresher operational evidence?",
    "E09": "Does healthy budget status materially change current delivery risk?",
    "E10": "Are the AI refusal tests meeting the documented launch threshold?",
    "E11": "What do we actually know about the root cause of partner sandbox instability?",
    "E12": "What portfolio intervention should we make for the shared Platform/AI resource conflict, including the downside elsewhere?",
    "E13": "Do the testing results suggest a new risk that should be proposed for human review?",
    "E14": "If export filtering is formally removed from launch scope, the baseline is updated, and stakeholders are aligned, what is the readiness implication?",
    "E15": "What can we conclude about security/testing readiness if current test evidence is unavailable?",
    "E16": "What is the readiness status if a critical dependency is forecast after launch and no viable mitigation exists?",
}


class EvalOutput(BaseModel):
    forecast_rag: Rag
    confidence: ConfidenceBand
    conclusion: str
    risks: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    cited_evidence_ids: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)


BASELINE_INSTRUCTIONS = """You are a program-management assistant.
Review the supplied raw portfolio context and answer the question.
Use only supplied context. Return forecast RAG, confidence, risks,
contradictions, recommended actions, evidence IDs, and missing information.
"""


def _question(case: dict[str, Any]) -> str:
    query = CASE_QUERIES[case["id"]]
    overrides = case.get("scenario_overrides")
    if overrides:
        query += "\nScenario state for this evaluation: " + json.dumps(overrides, sort_keys=True)
    return query


def _baseline_agent(model: str) -> Agent:
    return Agent(
        name="Weak Baseline",
        instructions=BASELINE_INSTRUCTIONS,
        model=model,
        output_type=EvalOutput,
    )


def run_baseline_case(
    *,
    model: str,
    question: str,
    raw_context: str,
) -> EvalOutput:
    prompt = build_baseline_prompt(question, raw_context)
    result = Runner.run_sync(_baseline_agent(model), prompt)
    output = result.final_output
    if not isinstance(output, EvalOutput):
        raise TypeError("Baseline returned an unexpected output type.")
    return output


def _controls(case: dict[str, Any]) -> ControlContext:
    overrides = case.get("scenario_overrides", {})
    dependency_date = overrides.get("critical_dependency_forecast_date")
    approval_status = overrides.get("approval_status")
    current_test_available = overrides.get("current_test_report_available", True)
    return ControlContext(
        mandatory_approval_required=approval_status is not None,
        mandatory_approval_verified=(approval_status == "verified") if approval_status is not None else None,
        critical_dependency_forecast_date=(
            date.fromisoformat(dependency_date) if dependency_date else None
        ),
        committed_launch_date=date(2026, 12, 4) if dependency_date else None,
        viable_mitigation=overrides.get("viable_mitigation", True),
        material_required_evidence_missing=(
            approval_status == "not_verified" or current_test_available is False
        ),
    )


def _confidence_inputs(
    context: list[Evidence],
    draft: AgentAssessmentDraft,
    case: dict[str, Any],
) -> ConfidenceInputs:
    if not context:
        return ConfidenceInputs(0.2, 0.2, 0.2, 0.2, 0.5, mandatory_evidence_missing=True)

    authority_scores = {1: 0.95, 2: 0.85, 3: 0.70, 4: 0.60, 5: 0.50}
    evidence_quality = sum(authority_scores[item.authority_tier] for item in context) / len(context)

    signal_kinds = {signal.kind for signal in detect_signals(context)}
    source_agreement = 0.55 if "cross_source_date_conflict" in signal_kinds else 0.88
    if "official_status_lag" in signal_kinds:
        source_agreement = min(source_agreement, 0.70)

    as_of_text = case.get("scenario_overrides", {}).get("as_of")
    as_of = (
        datetime.fromisoformat(as_of_text)
        if as_of_text
        else datetime(2026, 11, 13, 20, 0, tzinfo=timezone.utc)
    )
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)
    ages = [
        max(0.0, (as_of - item.source_updated_at).total_seconds() / 86400)
        for item in context
    ]
    average_age = sum(ages) / len(ages)
    freshness = 0.92 if average_age <= 3 else 0.78 if average_age <= 10 else 0.60

    overrides = case.get("scenario_overrides", {})
    missing_required = (
        bool(draft.missing_information)
        or overrides.get("current_test_report_available") is False
        or overrides.get("approval_status") == "not_verified"
    )
    coverage = 0.45 if missing_required else 0.90
    if "approval_timing_risk" in signal_kinds:
        coverage = min(coverage, 0.72)

    historical_reliability = (
        0.75 if any(item.source_type == "retrospective" for item in context) else 0.85
    )
    return ConfidenceInputs(
        evidence_quality=evidence_quality,
        source_agreement=source_agreement,
        freshness=freshness,
        coverage=coverage,
        historical_reliability=historical_reliability,
        mandatory_evidence_missing=missing_required,
    )


def run_program_os_case(
    *,
    model: str,
    question: str,
    case: dict[str, Any],
    evidence: list[Evidence],
) -> EvalOutput:
    hits = retrieve_evidence(evidence, question, limit=12)
    context = [hit.evidence for hit in hits]
    if not context:
        context = evidence[:12]

    # Use the same single-agent runtime, but configure the model explicitly for
    # reproducibility in evaluation runs.
    agent = Agent(
        name="Program OS Analyst",
        instructions=(
            "Use only provided evidence. Distinguish official from forecast status. "
            "Cite source IDs for every material conclusion. Surface contradictions, "
            "missing information, assumptions, and downstream tradeoffs. "
            "Do not invent ground truth or make consequential changes."
        ),
        model=model,
        output_type=AgentAssessmentDraft,
    )
    from program_os.agent import render_evidence

    prompt = (
        f"QUESTION\n{question}\n\nEVIDENCE\n{render_evidence(context)}\n\n"
        "Return a grounded forecast and human-review actions."
    )
    raw = Runner.run_sync(agent, prompt).final_output
    if not isinstance(raw, AgentAssessmentDraft):
        raise TypeError("Program OS agent returned an unexpected output type.")

    final = finalize_assessment(
        raw,
        project_id="atlas",
        official_rag=Rag.GREEN,
        evidence=context,
        controls=_controls(case),
        confidence_inputs=_confidence_inputs(context, raw, case),
    )
    return EvalOutput(
        forecast_rag=final.forecast_rag,
        confidence=final.confidence,
        conclusion=final.conclusion,
        risks=raw.risks,
        contradictions=final.contradictions,
        recommended_actions=raw.recommended_actions,
        cited_evidence_ids=final.evidence_ids,
        missing_information=raw.missing_information,
    )


def _tokens(text: str) -> set[str]:
    stop = {
        "the", "a", "an", "is", "are", "to", "of", "for", "and", "or",
        "that", "this", "in", "on", "with", "be", "has", "have",
    }
    return {
        token.strip(".,:;!?()[]{}'\"").lower()
        for token in text.split()
        if token.strip(".,:;!?()[]{}'\"").lower() not in stop
        and len(token.strip(".,:;!?()[]{}'\"")) >= 3
    }


def _semantic_phrase_present(expected: str, actual: str) -> bool:
    expected_tokens = _tokens(expected)
    if not expected_tokens:
        return expected.lower() in actual.lower()
    actual_tokens = _tokens(actual)
    return len(expected_tokens & actual_tokens) / len(expected_tokens) >= 0.55


def score_case(
    case: dict[str, Any],
    output: EvalOutput,
    all_evidence_ids: set[str],
) -> list[EvalFailure]:
    expected = case["expected"]
    combined = " ".join(
        [output.conclusion]
        + output.risks
        + output.contradictions
        + output.recommended_actions
        + output.missing_information
    )
    failures: list[EvalFailure] = []

    unknown_citations = set(output.cited_evidence_ids).difference(all_evidence_ids)
    if unknown_citations:
        failures.append(EvalFailure(
            "fabricated_material_evidence",
            case["id"],
            f"Unknown evidence IDs: {sorted(unknown_citations)}",
        ))

    required_citations = set(expected.get("must_cite", []))
    missing_citations = required_citations.difference(output.cited_evidence_ids)
    if missing_citations:
        failures.append(EvalFailure(
            "incorrect_evidence_citation",
            case["id"],
            f"Missing required citations: {sorted(missing_citations)}",
        ))

    expected_rag = expected.get("forecast_rag")
    if expected_rag and output.forecast_rag.value != expected_rag:
        kind = "incorrect_hard_gate" if expected.get("hard_gate") not in (None, "none") else "incorrect_forecast_direction"
        failures.append(EvalFailure(
            kind,
            case["id"],
            f"Expected {expected_rag}; got {output.forecast_rag.value}.",
        ))

    if (
        expected.get("hard_gate") == "cannot_green"
        and output.forecast_rag == Rag.GREEN
        and output.confidence == ConfidenceBand.HIGH
    ):
        failures.append(EvalFailure(
            "high_confidence_green_with_mandatory_blocker",
            case["id"],
            "Mandatory approval was not verified.",
        ))

    expected_confidence = expected.get("confidence")
    if expected_confidence and output.confidence.value != expected_confidence:
        failures.append(EvalFailure(
            "incorrect_prioritization",
            case["id"],
            f"Expected confidence {expected_confidence}; got {output.confidence.value}.",
        ))

    if expected.get("insufficient_evidence") and not output.missing_information:
        failures.append(EvalFailure(
            "failed_insufficient_evidence",
            case["id"],
            "Expected explicit missing-information handling.",
        ))

    for contradiction in expected.get("contradictions", []):
        if not _semantic_phrase_present(contradiction, " ".join(output.contradictions)):
            failures.append(EvalFailure(
                "missed_material_contradiction",
                case["id"],
                contradiction,
            ))

    for risk in expected.get("risks", []):
        if not _semantic_phrase_present(risk, " ".join(output.risks + output.conclusion.splitlines())):
            failures.append(EvalFailure(
                "missed_critical_risk",
                case["id"],
                risk,
            ))

    recommendation_expectations = expected.get("recommendation_contains", [])
    if recommendation_expectations:
        recommendation_text = " ".join(output.recommended_actions)
        for phrase in recommendation_expectations:
            if not _semantic_phrase_present(phrase, recommendation_text):
                failures.append(EvalFailure(
                    "incorrect_prioritization",
                    case["id"],
                    f"Recommendation missing: {phrase}",
                ))
        if output.recommended_actions and not output.cited_evidence_ids:
            failures.append(EvalFailure(
                "consequential_action_without_evidence_or_tradeoffs",
                case["id"],
                "Recommendation lacks evidence citations.",
            ))

    for forbidden in expected.get("must_not_assert", []):
        if _semantic_phrase_present(forbidden, combined) and output.confidence == ConfidenceBand.HIGH:
            failures.append(EvalFailure(
                "unsupported_high_confidence_assertion",
                case["id"],
                forbidden,
            ))

    return failures


def _dimension_counts(failures: Iterable[EvalFailure]) -> dict[str, int]:
    mapping = {
        "missed_critical_risk": "Detection",
        "missed_material_contradiction": "Detection",
        "incorrect_forecast_direction": "Judgment",
        "incorrect_hard_gate": "Safety/Trust",
        "incorrect_evidence_citation": "Safety/Trust",
        "fabricated_material_evidence": "Safety/Trust",
        "high_confidence_green_with_mandatory_blocker": "Safety/Trust",
        "unsupported_high_confidence_assertion": "Safety/Trust",
        "failed_insufficient_evidence": "Safety/Trust",
        "incorrect_prioritization": "Decision Quality",
        "harmful_portfolio_intervention": "Decision Quality",
        "consequential_action_without_evidence_or_tradeoffs": "Decision Quality",
    }
    counts: Counter[str] = Counter()
    for failure in failures:
        counts[mapping.get(failure.kind, "Other")] += 1
    return dict(counts)


def _serialize_output(output: EvalOutput) -> dict[str, Any]:
    return output.model_dump(mode="json")


def run_live(
    *,
    model: str,
    data_dir: Path,
    gold_path: Path,
    case_ids: set[str] | None = None,
) -> dict[str, Any]:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for live evaluation.")

    evidence = load_evidence_dir(data_dir)
    all_ids = {item.evidence_id for item in evidence}
    raw_context = load_raw_context(data_dir)
    cases = load_gold_cases(gold_path)
    if case_ids:
        cases = [case for case in cases if case["id"] in case_ids]

    report: dict[str, Any] = {
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "agents_sdk": "0.24.0",
        "program_os_version": "0.2.0",
        "dataset": "atlas-v2-001",
        "gold_case_count": len(cases),
        "paths": {},
    }

    for path_name in ("baseline", "program_os"):
        path_failures: list[EvalFailure] = []
        case_results = []
        for case in cases:
            question = _question(case)
            output = (
                run_baseline_case(model=model, question=question, raw_context=raw_context)
                if path_name == "baseline"
                else run_program_os_case(
                    model=model,
                    question=question,
                    case=case,
                    evidence=evidence,
                )
            )
            failures = score_case(case, output, all_ids)
            path_failures.extend(failures)
            case_results.append({
                "case_id": case["id"],
                "name": case["name"],
                "question": question,
                "output": _serialize_output(output),
                "failures": [asdict(failure) for failure in failures],
            })

        summary = summarize_failures(path_failures)
        report["paths"][path_name] = {
            "weighted_penalty": summary.weighted_penalty,
            "catastrophic": summary.catastrophic,
            "catastrophic_failures": [
                asdict(failure) for failure in summary.catastrophic_failures
            ],
            "failure_dimensions": _dimension_counts(path_failures),
            "cases_without_failures": sum(
                1 for item in case_results if not item["failures"]
            ),
            "cases": case_results,
        }

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Program OS live V2 evaluation.")
    parser.add_argument("--model", required=True, help="Exact model identifier to record and use.")
    parser.add_argument("--data-dir", type=Path, default=Path("examples/atlas/data"))
    parser.add_argument("--gold", type=Path, default=Path("tests/evals/gold/atlas_gold.json"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/eval-report.json"))
    parser.add_argument("--case", action="append", dest="cases", help="Run only a case ID; repeatable.")
    args = parser.parse_args()

    report = run_live(
        model=args.model,
        data_dir=args.data_dir,
        gold_path=args.gold,
        case_ids=set(args.cases) if args.cases else None,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "model": report["model"],
        "cases": report["gold_case_count"],
        "baseline": {
            "weighted_penalty": report["paths"]["baseline"]["weighted_penalty"],
            "catastrophic": report["paths"]["baseline"]["catastrophic"],
        },
        "program_os": {
            "weighted_penalty": report["paths"]["program_os"]["weighted_penalty"],
            "catastrophic": report["paths"]["program_os"]["catastrophic"],
        },
    }, indent=2))


if __name__ == "__main__":
    main()
