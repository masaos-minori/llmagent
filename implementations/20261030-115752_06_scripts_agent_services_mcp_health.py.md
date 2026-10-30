# Implementation Procedure: `scripts/agent/services/mcp_health.py`

## Goal

Make the posture-gate error/remediation text name the mandatoriness registry as the classification source, so operators see where a classification decision lives (plan row: error/remediation text names the registry; REQ-008 observability via existing channels).

## Scope

- Docstring and remediation-string edits in `scripts/agent/services/mcp_health.py` only: `_is_fatal_gate` docstring (:139-146), `PostureGate.required` field docstring (:100, :111), and `_remediation` (:266-278).
- No logic change: `_is_fatal_gate`'s rule (`gate.required or gate.failure_class in _SAFETY_INTEGRITY_CLASSES`, :147) stays byte-identical (issue Constraint: do not weaken fail-closed rules).

## Assumptions

- Lightweight row: text confined to docstrings/remediation strings, no public-contract change.
- The registry path string is written as literal text (`registry/component_mandatoriness.yaml`), not imported — this file does not need the loader (the startup stage in row 5 owns loading).

## Design decisions

- `_remediation` (:266-278): when an Availability failure is reported for a `required=false` server, append that the classification authority is the mandatoriness registry — a `required=false` value that contradicts a registry `required` entry now aborts at the row-5 stage anyway, so the remediation tells the operator where to fix the classification rather than the config.
- `_is_fatal_gate` docstring (:142-145): replace the phrase naming only `agent_08_04`/ADR-004 with a pointer to the machine-readable registry as the effective classification source (ADR-004 Group 3 item 13 division stays: criteria in ADR-004, classification in the registry, table in `agent_08_04` derived).

## Alternatives considered

- N/A: text-only change per the plan row.

## Implementation

### Target file

`scripts/agent/services/mcp_health.py`

### Procedure

1. `PostureGate` docstring (:100): extend the `required` description with "classification source: `registry/component_mandatoriness.yaml` (validated against config at startup)".
2. `_is_fatal_gate` docstring (:142-145): same source pointer; keep the INV-09/INV-10 citation.
3. `_remediation` (:266-278): add the registry-name sentence to the availability-failure branch only; safety/integrity remediation text is unchanged (those failures are fatal regardless of classification).

### Method

Edit strings; verify with existing posture tests that no assertion pins the old wording.

### Details

- `tests/agent/test_mcp_health_posture.py` is the characterization lock (plan Tests Regression row) — it must stay green without edits; if it pins exact remediation strings, update only the availability-branch expectation and record it as an assertion-text change, not a meaning change.

## Compatibility considerations

- Operator-facing message text changes; no behavioral change. Grep for test assertions on the changed strings before landing.

## Security considerations

- N/A: no logic change; observability requirement satisfied by existing `ServiceWarning`/remediation machinery (REQ-008).

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_mcp_health_posture.py` unchanged-green; `uv run pytest tests/agent` (plan Phase 3 suite).
- Gates: `uv run mypy scripts`, `uv run ruff check scripts tests tools`.

## Completion criteria

- Fatal/warning output for an availability failure names the registry as the classification authority; posture test suite green without meaning changes (plan AC-6: production behavior unchanged).

## Out of Scope

- The cross-check itself (rows 4-5), registry content (row 1).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the three text edits per Procedure | Pending | — | — | |
| 3 | Run `tests/agent/test_mcp_health_posture.py` + toolchain gates | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-008 (fatal/disabled decisions keep an observable reason via existing machinery)
- **Source issue**: `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-115752
- **Related target files**: `scripts/agent/services/mcp_health.py`
