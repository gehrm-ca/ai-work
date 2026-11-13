from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from program_os.models import Evidence


def test_evidence_is_immutable():
    evidence = Evidence(
        evidence_id="e1",
        source_type="jira",
        source_id="A-1",
        project_id="PLAT",
        source_updated_at=datetime.now(timezone.utc),
        retrieved_at=datetime.now(timezone.utc),
        authority_tier=1,
        payload={"status": "Open"},
    )
    with pytest.raises(ValidationError):
        evidence.authority_tier = 2
