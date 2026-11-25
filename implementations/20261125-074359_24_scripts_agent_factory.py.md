## Goal

Construct `PendingConfigState` and wire it into `AppServices` during startup, so the pending view exists
before the first command reads it (REQ-009, pending display).

## Scope
**Release unit**: R5-pending-restart

## Assumptions
- Verified against current source: `factory.py` assembles `AppServices` at `factory.py:357-370`, and
  `job_registry` at `factory.py:355` is the construction pattern cliplc003 landed.
- Corrected during Step 3a re-verification: `factory.py` does not call `build_agent_config`; that call is
  in `scripts/agent/context.py:406`, so this document does not change any config-build call site.
- Overlap: `factory.py` is also a target row of the archived cliplc003 Plan, judged sequenced rather than
  conflicting; this Plan adds one constructor call.

## Design decisions
- The service is constructed in the factory rather than lazily in a command, because the degraded guard
  must survive across commands (row 8).
- The factory passes no configuration values into the service; it only constructs it and attaches it.

## Alternatives considered
- Constructing the pending state in `cmd_config` — rejected: the state would not survive across commands.

## Implementation
### Target file
`scripts/agent/factory.py`

### Procedure
Construct `PendingConfigState` and wire it into `AppServices` during startup.

### Method
- One constructor call, placed with the other configuration-adjacent services.
- The instance is passed to `AppServices` as the field row 23 defines.

### Details
- No other factory wiring changes; the import-graph contract `shared-is-leaf` is unaffected because the
  service lives in `agent.services`.

## Compatibility considerations
- Blast radius: the factory is the single startup assembly point; `tests/agent/test_agent_factory.py`
  asserts the wiring.

## Security considerations
- No configuration value is passed into the service at construction.

## Rollback considerations
- Revert the Phase 5 commit.

## Validation plan
- `uv run pytest tests/agent/test_agent_factory.py -q`
- `uv run pytest tests/agent/services/test_config_pending_state.py -q` (row 28)
- `uv run ruff check scripts tests`, `uv run mypy scripts`, `uv run lint-imports`

## Completion criteria
- The factory constructs the pending state and `AppServices` receives the same instance the display
  commands read.

## Out of Scope
- The pending-record model and the degraded guard (row 8).
- The container field itself (row 23).

### Companion test files
- `tests/agent/test_agent_factory.py`
  - Procedure: assert the factory constructs `PendingConfigState` and wires the same instance into
    `AppServices`.
  - Validation: `uv run pytest tests/agent/test_agent_factory.py -q`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | re-check the cliplc003 overlap before running |
| 2 | Add or update tests per Validation plan | Pending | — | — | companion test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-009 (pending display); AC-5
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `scripts/agent/factory.py`, `tests/agent/test_agent_factory.py`
