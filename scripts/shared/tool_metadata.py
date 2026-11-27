#!/usr/bin/env python3
"""scripts/shared/tool_metadata.py

Closed policy vocabulary for runtime tool metadata (REQ-001, REQ-003).

Each vocabulary dimension is declared as one ``Literal`` alias plus the matching
``frozenset`` of allowed values, so the type checker and ``validate_tool_schema_v2()``
read the same definition and cannot drift. Values are closed: an open value would let
a producer declare a value no consumer can interpret.

``TOOL_FIELD_SET_VERSION`` is the single place the field-set version value is written;
no per-tool version constants exist. This module defines no per-tool values — per-tool
declarations stay in the producers.

The module imports nothing from ``agent``: ``shared`` stays an import-linter leaf and
both producers and Agent consumers read these values.

Boundary: the capability set holds only the values the approval preflight needs now;
preview-display values stay with the preview work item (UNK-02), and the call-state
contract stays with the MCP two-layer defense issues (REQ-010).
"""

from __future__ import annotations

from typing import Literal

SideEffectClass = Literal["read_only", "local_write", "external_write"]
SIDE_EFFECT_CLASS_VALUES: frozenset[str] = frozenset(
    {"read_only", "local_write", "external_write"}
)

RetryPolicy = Literal[
    "never",
    "safe_read_retry",
    "same_logical_call_only",
    "reconcile_then_retry",
]
RETRY_POLICY_VALUES: frozenset[str] = frozenset(
    {"never", "safe_read_retry", "same_logical_call_only", "reconcile_then_retry"}
)

# Declared values that mean 'replayable' in the dedup vocabulary: safe_read_retry
# retries live in the transport layer and are not dedup replay targets.
RETRY_POLICY_RETRYABLE_VALUES: frozenset[str] = frozenset(
    {"same_logical_call_only", "reconcile_then_retry"}
)


def retry_policy_is_retryable(value: str | None) -> bool:
    """True when a declared retry_policy maps to the dedup 'retryable' class."""
    return value in RETRY_POLICY_RETRYABLE_VALUES


ReconciliationPolicy = Literal["not_required", "local_state", "external_state"]
RECONCILIATION_POLICY_VALUES: frozenset[str] = frozenset(
    {"not_required", "local_state", "external_state"}
)

# ``non_escalating`` covers keys no escalation rule reads (e.g. "owner", "run_id",
# "workflow"); the three escalation kinds cannot classify them.
ResourceKeyKind = Literal[
    "path", "branch", "repo", "issue", "pull_request", "non_escalating"
]
RESOURCE_KEY_KIND_VALUES: frozenset[str] = frozenset(
    {"path", "branch", "repo", "issue", "pull_request", "non_escalating"}
)

PreviewCapability = Literal["none", "dry_run"]
PREVIEW_CAPABILITY_VALUES: frozenset[str] = frozenset({"none", "dry_run"})

TOOL_FIELD_SET_VERSION = "2.1"
