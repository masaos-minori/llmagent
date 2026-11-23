## Goal

Add the immutable `SessionPersistenceSnapshot` (new), a capture method, snapshot parameters on both persist methods, and a generation check (REQ-006 one-snapshot persistence; AC-3).

## Scope
**Release unit**: N/A: not part of a release unit

Single-file change; consumed by seq 02 (pre-transition finalization) and seq 14 (shutdown).

## Assumptions
- Current code verified: `persist_session_diagnostics` (59-80) and `persist_session_memories` (187-217) each read `ctx.session.session_id` and `ctx.conv.history` independently (`session_persister.py:65,198,210`).
- Both steps already skip when session_id is None; snapshot handling must preserve that skip.

## Design decisions
- Frozen dataclass with a defensive tuple copy of history plus session id, generation, turn id, and statistics (REQ-006); both persist methods take an optional snapshot and reject (log and return) when its generation differs from the live generation.
- `persist_session_diagnostics` is already complexity D (21): take the snapshot as input and extract helpers instead of adding branches (plan Risks).

## Alternatives considered
- Reading state once in repl and passing raw fields: rejected — the plan requires one typed, generation-checked snapshot shared with the transition path.

## Implementation
### Target file
`scripts/agent/session_persister.py`
### Procedure
1. Define `SessionPersistenceSnapshot` (new) in this module.
2. Add `capture_snapshot()` (new) returning it from the live context (tuple copy of history).
3. Add an optional snapshot parameter to `persist_session_diagnostics` and `persist_session_memories`; when present, read all state from it and verify its generation against `ctx.session` generation before writing.
4. Keep the no-session skip path unchanged.
### Method
Optional parameter defaulting to None (live read), so existing callers stay valid until seq 14 and seq 02 pass snapshots.
### Details
N/A: no further non-inferable facts.

### Companion test files
- `tests/agent/test_session_persister.py`
  - Procedure: add tests for snapshot immutability (history mutation after capture does not change the snapshot), one snapshot used by both steps, and generation-mismatch rejection.
  - Validation: `uv run pytest tests/agent/test_session_persister.py -q`.

## Compatibility considerations
- Parameters are optional; current call sites (`repl.py:94-97`) keep working until seq 14 switches them.

## Security considerations
N/A: no new data exposure; snapshots copy existing session state.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_session_persister.py -q`.
- `uv run radon cc scripts/agent/session_persister.py -s` — no complexity increase over the D (21) baseline.

## Completion criteria
Shutdown and pre-transition persistence evaluate one snapshot, and a snapshot whose generation differs is rejected with no writes (AC-3).

## Out of Scope
Shutdown capture (seq 14), transition integration (seq 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-23 | 2026-11-23 | Added SessionPersistenceSnapshot, capture_snapshot(), _checked_snapshot(); both persist steps take an optional snapshot and reject stale generations; latency summary helper extracted (radon D(21)->C(20)). Executed before seq 02 per plan Phase 2 order. |
| 2 | Add or update tests per Validation plan (companion row 24) | Completed | 2026-11-23 | 2026-11-23 | Tests written first per plan Phase 2 tests/agent/test_session_persister.py: 5 snapshot tests added; 20 tests pass. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-23 | 2026-11-23 | ruff, mypy, lint-imports, bandit, radon pass; full-suite pass due at batch end. mypy/lint-imports pass at cluster gate 2026-11-23; 5 tests pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-23 | 2026-11-23 | Generated docs via seq 19 Docs updated via seq 15-20 (2026-11-23) |

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
- **Requirement ID**: `REQ-006` (immutable persistence snapshot, generation check)
- **Source issue**: `issues/20261119-145300_cliplc002_session-transition-generation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-232757_cliplc002_session-transition-generation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-094714
- **Related target files**: `scripts/agent/session_persister.py`, `tests/agent/test_session_persister.py`