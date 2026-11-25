"""scripts/shared/write_outcome.py — Write-outcome vocabulary and write-audit field contract.

The vocabulary names the outcomes that a write can end in when its effect on the
remote side is not known: an ambiguous transport failure leaves the caller unable to
tell whether the write was applied, and a completion audit that cannot be written
after an applied write leaves the audit record missing although the write landed.
Neither outcome is retried automatically, so the no-retry rule is stated once here
and read by every server that performs writes.

The field builder is the shared audit-record contract: every server writes the same
identifiers in the same order, so a record from one server is comparable with a
record from another. It accepts identifiers only, never payload text, so a payload
cannot enter an audit record through it.
"""

from __future__ import annotations

from typing import Literal

WriteOutcome = Literal["outcome_unknown", "applied_audit_failed"]

OUTCOME_UNKNOWN: str = "outcome_unknown"
APPLIED_AUDIT_FAILED: str = "applied_audit_failed"

# Neither outcome is retried automatically: an unknown outcome may already have been
# applied remotely, and an applied write with a missing audit record must be resolved
# by a human rather than replayed.
NO_AUTO_RETRY_OUTCOMES: frozenset[str] = frozenset(
    {OUTCOME_UNKNOWN, APPLIED_AUDIT_FAILED}
)

AUDIT_PHASES: frozenset[str] = frozenset({"intent", "completion"})


def build_write_audit_fields(
    op: str,
    phase: str,
    session_id: str,
    request_id: str,
    call_id: str,
) -> dict[str, str]:
    """Return the ordered key-value fields of one write-audit record.

    `phase` is "intent" for the record written before the API call and "completion"
    for the record written after an applied write. An empty identifier is rendered as
    "-" so the record always carries every field. Identifiers only: no payload text.
    """
    if phase not in AUDIT_PHASES:
        raise ValueError(f"unknown audit phase: {phase}")
    return {
        "op": op,
        "phase": phase,
        "session": session_id or "-",
        "request": request_id or "-",
        "call": call_id or "-",
    }
