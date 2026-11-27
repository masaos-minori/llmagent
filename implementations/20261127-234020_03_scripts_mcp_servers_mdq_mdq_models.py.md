# Implementation Procedure — scripts/mcp_servers/mdq/mdq_models.py

## Goal

Define the single stale-state vocabulary and the SQL expression that agrees with it, so health and
outline report from one definition (REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-004 (one shared stale-state set), REQ-001 and REQ-002 (the persisted-fingerprint
fields the models expose). Acceptance criterion: AC-3.

## Assumptions
- Full form: this row defines the shared vocabulary that seq 04 and seq 05 consume.
- The column names come from seq 01; this document uses them and does not redefine them.
- The state set is a closed vocabulary: fresh, stale, missing, unknown, inconsistent.
- `tests/mcp_servers/mdq/test_mdq_stale_detection.py` is this row's companion.

## Design decisions
- `STALE_STATES` (new) is the closed state set; `classify_stale_state()` (new) maps a stored row
  plus the current filesystem observation to one state, and `is_stale()` (line 308) stays the
  boundary predicate used inside it.
- `STALE_SQL_CONDITION` (line 313) is redesigned against the new columns so the SQL agrees with
  the Python function on the database-observable part; chunks without a document row are the
  inconsistent state.
- `OutlineResponse.stale_warning` (line 240) carries the state name instead of a free-form
  sentence, so health and outline share the same wording source.

## Alternatives considered
- Keep `is_stale()` as the only definition and add a separate SQL string: rejected, because two
  definitions drift apart; the companion test is the guard that keeps them equal.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_models.py`

### Procedure
- Add `STALE_STATES` (new) and `classify_stale_state()` (new).
- Redesign `STALE_SQL_CONDITION` (line 313) against `source_content_hash` (new),
  `path_mtime_fingerprint` (new), and the chunk truncation fields.
- Change `OutlineResponse.stale_warning` (line 240) to carry the state name.

### Method
- The Python function takes the stored row and the current stat result; the SQL expression covers
  only what the database can observe, so the two agree on the states that do not need a
  filesystem read.

### Details
- A chunk with no document row is the inconsistent state; a path that no longer exists is the
  missing state; a stored row whose hash fields cannot be compared is the unknown state.

### Companion test files
- `tests/mcp_servers/mdq/test_mdq_stale_detection.py`
  - Procedure: add the same-mtime content change, mtime rollback, deletion, and state-set cases
    with real files; keep the boundary characterization tests and the SQL-versus-Python agreement
    test, extended to the new columns.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_mdq_stale_detection.py` — the SQL
    condition agrees with the Python state function for every state.

## Compatibility considerations
- `is_stale()` and `STALE_SQL_CONDITION` consumers are `scripts/mcp_servers/mdq/health_check.py`,
  `scripts/mcp_servers/mdq/mdq_service.py`, and the companion test, all rows of this Plan;
  `tools/stale_detector.py` is not affected (its `is_stale` is the tool's own field).

## Security considerations
- N/A: state vocabulary only.

## Rollback considerations
- N/A: revert the commit; the redesigned SQL depends on the seq 01 columns, so rollback is
  together with that row.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_stale_detection.py`
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- The five states are the only stale vocabulary, and the SQL expression and the Python function
  agree on every case the database can observe (AC-3).

## Out of Scope
- Filesystem inspection in outline (seq 04); health reporting (seq 05); the FTS5 identity
  (mdqmcp006).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion `tests/mcp_servers/mdq/test_mdq_stale_detection.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | `docs/22_mcp/mcp_04_04_mdq.md` (seq 18) |

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
- **Requirement ID**: REQ-004 (one shared stale-state set)
- **Source issue**: `issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-170412_mdqmcp004_mdq-file-identity-stale.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-234020
- **Related target files**: `scripts/mcp_servers/mdq/mdq_models.py`, `tests/mcp_servers/mdq/test_mdq_stale_detection.py`
