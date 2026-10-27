## Goal

Record the persistence threading boundary in `docs/41_db/db_04_api_and_operations-module-boundaries-and-helper.md`
(REQ-007): turn-boundary writes run on worker threads via `asyncio.to_thread`;
connection-per-call remains the default rule; the single exception is a boundary-reused
connection opened with `check_same_thread=False` used sequentially only.

## Scope

- Only `docs/41_db/db_04_api_and_operations-module-boundaries-and-helper.md`.
- Add a threading-boundary subsection to section 2 (`SQLiteHelper`), adjacent to the
  existing connection-options paragraph (current L33-35 lists `write_mode`,
  `row_factory`, `load_vec`, `reuse_connection` with no threading rule — verified this
  pass; the Plan's "L35" citation is accurate).
- Document the new `check_same_thread` option alongside the existing option list.

## Assumptions

- Deferred target row per the Plan's frozen table: executed in the workflow's Step 10
  docs phase, not during `python-implementation` of the code rows; this document is
  generated now so the docs phase has the procedure ready.
- Content must match the shipped outcome of `..._01_...` (knob) and `..._02_...`
  (per-call connections opened inside the worker thread; no boundary-owned reused
  connection today). Phrase the reused-connection exception as the authorized
  mechanism with its usage rule, not as current shipped fact, if implementation
  confirms the per-call shape — align the final wording with the implemented state in
  the docs phase.
- `docs/00_index.md` mapping (L124/L152/L191 per the Plan) routes
  SQLite/connection/WAL/transactions and Session/DB persistence here; no other doc row
  is in this Plan, so no cross-doc edits.
- Existing docs `implementations/done/20261004-112553_190_*db_04*` and
  `20261019-095521_05_*db_04*` cover earlier db_04 revisions; they do not cover the
  threading rule (checked: neither names `check_same_thread` threading content), so
  this row is Not implemented.

## Design decisions

- One subsection inside section 2 rather than a new top-level section: db_04's scope is
  module boundaries + helper options; the threading rule is a property of the helper's
  connection lifecycle.

## Alternatives considered

- Recording the rule in `docs/23_agent/*` turn-flow docs instead: rejected — the Plan's
  Documentation Impact maps it to db_04 via `docs/00_index.md`; no agent-docs row exists
  in the frozen table.

## Implementation

### Target file

`docs/41_db/db_04_api_and_operations-module-boundaries-and-helper.md`

### Procedure

Add the threading-boundary subsection and extend the connection-options sentence.

### Method

1. Extend the options sentence (current L35) to include `check_same_thread` (default
   `True`, per-instance via `__init__` and per-open via `open`).
2. Add subsection "Threading boundary" containing:
   - Default rule: connections are opened, used, and closed on one thread
     (connection-per-call); `check_same_thread=True` enforcement stays in force for all
     non-turn paths.
   - Turn-boundary writes (`agent/turn_persistence.py`) execute on worker threads via
     `asyncio.to_thread`, with sequential awaits preserving within-turn write order.
   - The single authorized exception: a connection reused across threads must be opened
     with `check_same_thread=False` and used sequentially only, never concurrently.
3. Link the turn-boundary description to the agent state/persistence doc already linked
   from db_04's module-boundary section (keep the cross-link style of the file).

### Details

- Keep wording factual against implemented behavior at docs-phase time; do not describe
  the pre-offload (loop-thread) behavior as current.
- Documentation files under `docs/` are written in English (per `skills/DESIGN.md`
  output language).

## Compatibility considerations

- Run the docs checker(s) from `routing.md` Tools ("When to run which tool") after the
  edit (stale/needs-confirmation registration), per AGENTS.md Global Rule 9.

## Security considerations

- No security surface; documentation only.

## Rollback considerations

- Additive subsection; removal reverts cleanly.

## Validation plan

- `tools/stale_detector.py` on this procedure document after implementation confirms the
  constructs referenced.
- Applicable docs checker per `routing.md`; full validation sequence
  (`rules/toolchain.md`).

## Completion criteria

- db_04 contains the threading rule (worker-thread turn writes, connection-per-call
  default, `check_same_thread=False` sequential-only exception) and lists the new option.

## Out of Scope

- Schema/WAL/`busy_timeout` documentation changes (db_01 territory).
- Any `docs/23_agent/*` edit (no row in the frozen table).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| 20261028-003125-15 | 4 | docs | Planned | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-007
- **Source issue**: `issues/20261026-225134_sess008_offload-session-sqlite-writes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-090510_sess008_offload-session-sqlite-writes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-003125
- **Related target files**: `docs/41_db/db_04_api_and_operations-module-boundaries-and-helper.md`
