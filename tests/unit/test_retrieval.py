from pathlib import Path

from program_os.evidence import load_evidence_dir
from program_os.retrieval import retrieve_evidence


DATA = Path("examples/atlas/data")


def ids_for(query: str, limit: int = 16) -> set[str]:
    evidence = load_evidence_dir(DATA)
    return {
        hit.evidence.evidence_id
        for hit in retrieve_evidence(evidence, query, limit=limit)
    }


def test_partner_retrieval_returns_operational_evidence():
    ids = ids_for("partner integration recovery launch dependency")
    assert "ATLAS-101" in ids
    assert "PAGE-PLAT" in ids
    assert "MTG-1111-PORTFOLIO" in ids
    assert "RETRO-PLAT-Q3" in ids


def test_defect_trend_retrieval_keeps_full_time_series():
    ids = ids_for("What does the current defect trend imply for launch readiness?")
    assert {"TEST-1108", "TEST-1110", "TEST-1112"}.issubset(ids)


def test_compliance_retrieval_includes_approval_note_and_decision():
    ids = ids_for("Is the compliance approval path creating a launch-readiness risk?")
    assert {"D-03", "PAGE-SEC", "MTG-1112-SEC", "DEP-MAP-1112"}.issubset(ids)


def test_resource_tradeoff_retrieval_includes_dependency_map():
    ids = ids_for(
        "What portfolio intervention should we make for the shared Platform/AI "
        "resource conflict, including the downside elsewhere?"
    )
    assert {"RES-1112", "DEP-MAP-1112", "ATLAS-109", "ATLAS-101"}.issubset(ids)


def test_critical_dependency_retrieval_includes_launch_commitment():
    ids = ids_for(
        "What is the readiness status if a critical dependency is forecast "
        "after launch and no viable mitigation exists?"
    )
    assert {"DEP-MAP-1112", "D-01", "MILESTONES-1112"}.issubset(ids)
