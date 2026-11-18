## Goal
Correct the docstrings so they describe the behavior the startup pipeline relies on (`REQ-001`, `REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit
- In scope: the docstrings of `check_routing_drift` and `check_routing_safety_tiers`; no behavior change.

## Assumptions
- `check_routing_drift(strict=True)` raises `RuntimeError` when `drift` is non-empty, so the returned list is informational and empty in strict mode (checked in Step 3a).

## Design decisions
- Docstring-only change; the functions keep their signatures and return types.

## Alternatives considered
N/A: docstring-only change.

## Implementation
### Target file
`scripts/agent/services/routing_drift.py`

### Procedure
1. `check_routing_drift`: first line states it returns the drift messages for informational use; with `strict=True` any drift raises `RuntimeError`, so no message is returned in that mode.
2. `check_routing_safety_tiers`: replace "Returns warning messages." with a statement that it returns one message per registered tool missing from `tool_safety_tiers`, and that the startup pipeline records each as FATAL (ADR-004 INV-07).

### Method
- Keep the existing `Any other exception ... propagates` sentence.

### Details
- No code, import, or message text changes.

## Compatibility considerations
N/A: docstrings only.

## Security considerations
N/A: docstrings only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run ruff check scripts/agent/services/routing_drift.py` and `uv run mypy scripts/agent/services/routing_drift.py`; `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py`.

## Completion criteria
- Both docstrings match the behavior; no code line changed.

## Out of Scope
- Behavior of either function; startup call sites (procedure 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit both docstrings (Implementation > Procedure) | Completed | 20261118-140956 | 20261118-140956 | Changed: scripts/agent/services/routing_drift.py (docstrings only). |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261118-140956 | 20261118-140956 | — |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20261117-123005_adrchk005_startup-fail-closed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-134945_adrchk005_startup-fail-closed.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-135645
- **Related target files**: `scripts/agent/services/routing_drift.py`
