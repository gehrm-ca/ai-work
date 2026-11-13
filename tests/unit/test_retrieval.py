from pathlib import Path

from program_os.evidence import load_evidence_dir
from program_os.retrieval import retrieve_evidence


def test_partner_retrieval_returns_operational_evidence():
    evidence = load_evidence_dir(Path("examples/atlas/data"))
    hits = retrieve_evidence(
        evidence,
        "partner integration recovery launch dependency",
        project_ids=("PLAT",),
        limit=8,
    )
    ids = {hit.evidence.evidence_id for hit in hits}
    assert "ATLAS-101" in ids
    assert "PAGE-PLAT" in ids or "MTG-1111-PORTFOLIO" in ids
