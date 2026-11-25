## Goal

Hold `PendingConfigState` on `AppServices` so the pending view survives across CLI commands and is
visible to `/mcp status` and `/config show` (REQ-009, pending display).

## Scope
**Release unit**: R5-pending-restart

## Assumptions
- Verified against current source: `AppServices` (`context.py:326`) is the fully-initialized service
  container built by `factory.py`; `job_registry` is the placement pattern cliplc003 landed for a
  long-lived service.
- Overlap: `context.py` is also a target row of the archived cliplc003 Plan, judged sequenced rather
  than conflicting; this Plan adds one field.
- The pending state itself is defined by row 8; this document only carries the reference.

## Design decisions
- The field is non-optional in `AppServices`, because the display commands read it on every call and a
  missing pending state would make a pending change invisible.
- The container does not own the pending semantics; it only keeps the instance alive across commands.

## Alternatives considered
- Storing pending state on `AgentContext.cfg` — rejected: the config is the source of truth for applied
  values, and pending records must not look like configuration.

## Implementation
### Target file
`scripts/agent/context.py`

### Procedure
Hold `PendingConfigState` on `AppServices` so the pending view survives across CLI commands.

### Method
- Add `pending_config` (new) to `AppServices.__init__` (`context.py:336`) as a keyword parameter that
  defaults to a freshly constructed `PendingConfigState()`, so callers reach it as
  `ctx.services_required.pending_config` (`services_required` is the `AgentContext` property at
  `context.py:423` that returns `AppServices`). The default keeps the field non-`None`, so the
  required-service invariant loop (`context.py:352-362`) does not need a new entry.
- No behavior is added here beyond carrying the reference; `PendingConfigState` owns no resource, so the
  shutdown coordinator is unchanged.

### Details
- The field is constructed by `factory.py` (row 24), consistent with the other configuration-adjacent
  services.

## Compatibility considerations
- Blast radius: `AppServices` is read by the command mixins, and 10 test call sites construct it directly
  (`tests/agent/test_context.py` x9, `tests/agent/commands/test_cmd_mcp.py:801`) alongside the single
  production site (`factory.py:361`). `pending_config` is therefore added as a keyword parameter that
  defaults to a freshly constructed `PendingConfigState()`: the field is never `None`, the required-service
  invariant holds, and the existing call sites keep compiling.

## Security considerations
- No configuration value is stored here; the pending record names fields, not values (row 8).

## Rollback considerations
- Revert the Phase 5 commit.

## Validation plan
- `uv run pytest tests/agent/test_context.py -q`
- `uv run pytest tests/agent/services/test_config_pending_state.py -q` (row 28)
- `uv run ruff check scripts tests`, `uv run mypy scripts`, `uv run lint-imports`

## Completion criteria
- `AppServices` carries the pending state, and the display commands reach it through the container rather
  than through a module-level store.

## Out of Scope
- The pending-record model and the degraded guard (row 8).
- The display rendering (rows 20, 21).

### Companion test files
- `tests/agent/test_context.py`
  - Procedure: assert `AppServices` carries the pending state.
  - Validation: `uv run pytest tests/agent/test_context.py -q`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-194300 | 20261125-204907 | re-check the cliplc003 overlap before running AppServices gains the pending_config keyword and always holds a PendingConfigState, so the display commands never see a missing container |
| 2 | Add or update tests per Validation plan | Completed | 20261125-194300 | 20261125-204907 | companion test file companion cases in tests/agent/test_context.py green |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-194300 | 20261125-204907 | R5 unit gate as row 8 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | `AppServices.pending_config` is always a `PendingConfigState` rather than an optional: the container holds one, so the display commands need no `None` branch, while `pending_state_for` still returns `None` for a ctx that has no container at all | Yes | 2026-11-25 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-009 (pending display); AC-5
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `scripts/agent/context.py`, `tests/agent/test_context.py`