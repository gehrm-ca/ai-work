import pytest

from program_os.confidence import ConfidenceInputs, calculate_confidence
from program_os.models import ConfidenceBand


def test_high_confidence_when_evidence_factors_are_strong():
    result = calculate_confidence(ConfidenceInputs(0.9, 0.9, 0.9, 0.9, 0.9))
    assert result.band == ConfidenceBand.HIGH


def test_conflict_reduces_confidence():
    result = calculate_confidence(ConfidenceInputs(0.9, 0.45, 0.9, 0.9, 0.8))
    assert result.band != ConfidenceBand.HIGH
    assert "source_agreement" in result.limiting_factors


def test_missing_mandatory_evidence_forces_low_confidence():
    result = calculate_confidence(
        ConfidenceInputs(0.95, 0.95, 0.95, 0.95, 0.95, mandatory_evidence_missing=True)
    )
    assert result.band == ConfidenceBand.LOW
    assert result.score <= 0.49


def test_invalid_factor_is_rejected():
    with pytest.raises(ValueError):
        calculate_confidence(ConfidenceInputs(1.1, 0.9, 0.9, 0.9, 0.9))
