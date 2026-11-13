"""Monday intervention priority helpers."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PriorityInputs:
    criticality: float
    probability: float
    impact: float
    time_sensitivity: float
    confidence_modifier: float = 1.0


def intervention_priority(inputs: PriorityInputs) -> float:
    values = (
        inputs.criticality,
        inputs.probability,
        inputs.impact,
        inputs.time_sensitivity,
        inputs.confidence_modifier,
    )
    if any(v < 0 or v > 1 for v in values):
        raise ValueError("Priority factors must be between 0 and 1.")
    return (
        inputs.criticality
        * inputs.probability
        * inputs.impact
        * inputs.time_sensitivity
        * inputs.confidence_modifier
    )
