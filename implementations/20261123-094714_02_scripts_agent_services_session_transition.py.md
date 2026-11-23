## Goal

Create `SessionTransitionService` (new) with idle check, snapshot, old-session finalization, temporary build, atomic commit, and rollback for /clear new and /session load (REQ-002 transition service, REQ-003 idle refusal; AC-1).

## Scope
**Release unit**: N/A: not part of a release unit

New module `scripts/agent/services/session_transition.py`; consumed by seq 06 (conversation_service) and seq 12 (cmd_session). No other file is modified here.

## Assumptions
- UNK-01 (plan): idle means `ctx.turn.persistence_boundary` is None; verify at execution and fall back to refusing when a turn is active by another flag.
- UNK-02 (plan): a failed old-session Memory finalization warns and continues (data already persisted); owner confirms at review.
- UNK-03 (plan): check `memory.on_session_stop` idempotence; guard with a finalized-session marker if double finalization is unsafe.
- Commands run serially in the REPL loop; the idle check is a guard, not a lock (plan Assumptions).
- `refresh_session_correlation` and `reset_session_stats` from `scripts/agent/commands/mixin_base.py` are reused read-only (Reference Files row).

## Design decisions
- `load(ctx, session_id)` and `clear_new` (new) share one pipeline: idle check -> `SessionTransitionSnapshot` (new) of id, generation, history copy, undo floor, correlation id, statistics -> finalize the old session through `SessionPersister` with a `SessionPersistenceSnapshot` (new) (type defined in seq 03) -> build the new state off to the side (restore builder from seq 04, or empty history for clear_new) -> commit all fields together (session id, generation bump, history, undo floor, correlation, stats) -> on any failure restore the snapshot fields and re-raise (plan Design).
- Refuse with an explicit reason while a turn persistence boundary is active (REQ-003).

## Alternatives considered
- Making `restore_session`/`clear_conversation` themselves transactional: rejected in the plan — a separate service owns the transition; the restore becomes a pure builder (seq 04).

## Implementation
### Target file
`scripts/agent/services/session_transition.py` (new)
### Procedure
1. Define `SessionTransitionSnapshot` (new) (frozen dataclass) and the refusal path for an active turn boundary.
2. Implement finalization via `SessionPersister` (capture a `SessionPersistenceSnapshot` (new) and run both persist steps; warn-continue on failure per UNK-02).
3. Implement `load`: call the seq 04 builder, commit its result atomically.
4. Implement `clear_new` (new): finalize old session, commit an empty (system prompt only) history with a fresh session start.
5. Implement rollback: restore every snapshotted field and re-raise the original error.
### Method
Snapshot-restore on frozen dataclass fields; the context is untouched until the commit step; the module imports `session_restore`, `session_persister`, and models only.
### Details
- The commit must bump `generation` through the seq 01 bump helper so all post-commit title/background staleness checks see the new value.
- Import layer: `scripts/agent/services/` may import `scripts/agent/` models per `skills/DESIGN.md` Shared Vocabulary; verify with `PYTHONPATH=scripts uv run lint-imports`.

### Companion test files
- `tests/agent/services/test_session_transition.py` (new)
  - Procedure: inject failure at each pipeline step (finalize, build, commit) and assert the previous session is unchanged; cover idle refusal, /clear new finalization order, and rollback completeness.
  - Validation: `uv run pytest tests/agent/services/test_session_transition.py -q`.

## Compatibility considerations
- New public module; generated API docs and the agent API manifest (seq 18-20) must be regenerated before the plan closes.
- Open Issues cliplc003/cliplc011 also name `cmd_session.py`; this plan lands first (plan Assumptions).

## Security considerations
- Rollback re-raises the original exception; error text reaching the UI must not leak DB internals beyond the existing session-not-found messages.

## Rollback considerations
N/A: new file; revert the commit removes it.

## Validation plan
- `uv run pytest tests/agent/services/test_session_transition.py tests/agent/services -q`.
- `PYTHONPATH=scripts uv run lint-imports`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`.

## Completion criteria
A failed load leaves the previous session unchanged at every step, /clear new finalizes the old session before switching, and an active-turn request is refused with an explicit reason (AC-1).

## Out of Scope
The restore builder (seq 04), command rewiring (seq 06, 12), persistence snapshot type (seq 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan (companion row 21) | Pending | — | — | Tests written first per plan Phase 3 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Generated docs via seq 18-20 |

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
- **Requirement ID**: `REQ-002` (atomic transition service), `REQ-003` (idle refusal)
- **Source issue**: `issues/20261119-145300_cliplc002_session-transition-generation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-232757_cliplc002_session-transition-generation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-094714
- **Related target files**: `scripts/agent/services/session_transition.py`, `tests/agent/services/test_session_transition.py`
