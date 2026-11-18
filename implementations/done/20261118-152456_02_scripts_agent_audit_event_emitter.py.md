## Goal

Split the single `partial_completion` audit key into two independently recorded signals in the
turn-end audit event: keep `partial_completion` as the pure "LLM stream was cut off" signal
(`had_partial_text`) and add `was_compensated` (`was_compensated` = partial DB rows were rolled
back). Both are threaded from `Orchestrator._execute_turn` through `emit_turn_end` into
`build_turn_end_event` (`REQ-001`, `REQ-002`, `REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `emit_turn_end` has one production caller (`orchestrator.py:200`) and `build_turn_end_event`
  has one internal caller (`emit_turn_end`, `audit_event_emitter.py:132`); both signatures are
  changed in this document. No other production caller exists (verified via `rg`).
- `audit_logger.info` receives the event dict; adding keys does not break the audit pipeline.
- `test_audit_log_format.py` asserts only that record keys are sorted, not a fixed key set, so
  additive keys do not break it (verified against current source).

## Design decisions
- Add `had_partial_text: bool` and `was_compensated: bool` (default `False`) to both
  `emit_turn_end` and `build_turn_end_event`, positioned after the existing `is_partial`
  parameter so any positional caller keeps its earlier arguments intact.
- Repurpose `partial_completion` from the old `or`-combined value to `had_partial_text` so a
  compensated-no-partial turn reports `partial_completion=false` (`REQ-001`). Record
  `had_partial_text` and `was_compensated` as explicit additional keys.

## Alternatives considered
- Keep `partial_completion` as the combined value and only add the two new keys. Rejected:
  violates `REQ-001` (a compensated-no-partial turn would still report `partial_completion=true`).
- Remove `partial_completion` entirely. Rejected: would break existing consumers/tests that
  read `partial_completion`; repurposing preserves the field's presence while fixing its
  meaning.

## Implementation
### Target file
`scripts/agent/audit_event_emitter.py`

### Procedure
1. In `emit_turn_end` (`audit_event_emitter.py:120`), add two parameters after `is_partial`:
   `had_partial_text: bool = False` and `was_compensated: bool = False`. Forward both to
   `build_turn_end_event`.
2. In `build_turn_end_event` (`audit_event_emitter.py:101`), add the same two parameters after
   `is_partial`.
3. In the returned event dict, change `"partial_completion": is_partial`
   (`audit_event_emitter.py:116`) to `"partial_completion": had_partial_text`, and add two keys
   alongside the existing fields: `"had_partial_text": had_partial_text` and
   `"was_compensated": was_compensated`.

### Method
- `emit_turn_end` signature becomes
  `(self, line, answer, turn_started_at, error_kind, is_partial=False, had_partial_text=False, was_compensated=False)`.
- `build_turn_end_event` signature becomes
  `(self, elapsed_ms, error_kind, is_partial=False, had_partial_text=False, was_compensated=False)`.
- Event dict gains `had_partial_text` and `was_compensated`; `partial_completion` now mirrors
  `had_partial_text`.

### Details
- The `is_partial` parameter is retained (backward compatible) but is no longer the source of
  `partial_completion`; the caller in `orchestrator.py` now passes the two real signals.
- Insert the two new keys within the dict literal so the event remains a plain JSON-serializable
  dict.

## Compatibility considerations
- Both signatures gain optional parameters with defaults; no existing positional caller breaks.
- The turn-end event dict gains two keys; no in-repo consumer reads `partial_completion`, so
  nothing production-side breaks. `test_audit_log_format.py` is unaffected (sorted-keys only).

## Security considerations
N/A: additive audit fields; no auth, secret, or input-handling change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run ruff format --check` && `uv run ruff check` on `audit_event_emitter.py`.
- `uv run mypy --no-namespace-packages` on `audit_event_emitter.py`.
- `uv run pytest tests/agent/test_orchestrator.py tests/agent/test_audit_log_format.py`.

## Completion criteria
- `emit_turn_end` and `build_turn_end_event` each accept `had_partial_text` and
  `was_compensated` and forward them into the event dict.
- `partial_completion` equals `had_partial_text` (not the combined value).
- `ruff format`, `ruff check`, and `mypy` pass.
- Existing orchestrator and audit-log-format tests pass.

## Out of Scope
- Any change to the audit logger schema or persistence of the new keys.
- Consumers of the audit stream outside this repo.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261118 | 20261118 | implemented,2:tests added+passing,3:validation green (4386 passed) |
| 2 | Add or update tests per Validation plan | Completed | 20261118 | 20261118 | N/A: no test file is the target of this row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261118 | 20261118 | — |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261118 | 20261118 | N/A: no doc edit required for this file |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`
- **Source issue**: issues/20261118-141333_ispartial001_partial-flag-metric-conflation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-143411_ispartial001_partial-flag-metric-conflation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-152456
- **Related target files**: scripts/agent/audit_event_emitter.py
