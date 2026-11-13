from pathlib import Path

from program_os.evidence import load_evidence_dir


ATLAS = Path("examples/atlas/data")


def test_atlas_has_48_immutable_evidence_records():
    evidence = load_evidence_dir(ATLAS)
    assert len(evidence) == 48
    assert len({item.evidence_id for item in evidence}) == 48
