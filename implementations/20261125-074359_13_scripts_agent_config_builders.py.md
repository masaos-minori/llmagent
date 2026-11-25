## Goal

Route section assembly through the shared primitives and expose the candidate-build entry the reload
path calls, so startup and reload run one builder and reject the same inputs (REQ-001, shared type
rules; REQ-002, reload candidate through the startup parser).

## Scope
**Release unit**: R1-strict-primitives

## Assumptions
- Verified against current source: `build_agent_config(cfg_override=...)` (`config_builders.py:154`)
  already runs `_resolve_config_source_and_registry` (`config_builders.py:83`) and
  `_run_production_validation` (`config_builders.py:101`); routing reload through it is what makes
  AC-1 hold by construction (OD-01).
- Overlap: this file is also a target row of the archived cliplc004 Plan
  (`plans/done/20261124-095950_cliplc004_bounded-shutdown-machine.md`), whose procedure
  `implementations/20261125-000005_18_scripts_agent_config_builders.py.md` covers
  `_assemble_agent_config`. The two changes touch different functions, so they do not conflict, and the
  overlap must be re-checked before this row runs.
- `ProductionConfigValidator` rules are reused unchanged; this document does not alter them.

## Design decisions
- The candidate-build entry is the same function startup uses, with `cfg_override` supplied by the
  reload path; no second builder is introduced.
- `_run_production_validation` stays on the reload path, which is what rejects a removed or moved key
  before any live change.

## Alternatives considered
- Validating the raw dict inside the reload service — rejected (OD-01 option a).

## Implementation
### Target file
`scripts/agent/config_builders.py`

### Procedure
Route section assembly through the shared primitives and expose the candidate-build entry the reload
path calls, keeping `_run_production_validation` on that path.

### Method
- The unknown-key rejection uses the declared key set from row 1's `reject_unknown_keys`; the existing
  `_check_unknown_production_keys` behavior is unchanged.
- The entry the reload path calls returns the typed `AgentConfig` candidate without mutating live
  state.

### Details
- The call site in `scripts/agent/context.py:406` is not changed by this document; `factory.py` does not
  call `build_agent_config` (corrected in the Plan during Step 3a).

## Compatibility considerations
- Blast radius: `build_agent_config` is the startup entry point; behavior changes only for values that
  were previously coerced.

## Security considerations
- Unknown-key errors name the key, not its value.

## Rollback considerations
- Revert the Phase 1 commit.

## Validation plan
- `uv run pytest tests/agent/test_config_builders.py tests/agent/services/test_config_reload_parity.py -q`
- `uv run pytest tests/integration/test_standard_config_integration.py -m integration -q`
- `uv run ruff check scripts tests`, `uv run mypy scripts`

## Completion criteria
- Startup and reload accept and reject the same values for every row of the parity table, and the
  integration config path still passes.

## Out of Scope
- The reload service's use of the entry (row 6).
- The section-builder call sites (row 14).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | re-check the cliplc004 overlap before running |
| 2 | Add or update tests per Validation plan | Pending | — | — | rows 27, 30 |
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
- **Requirement ID**: REQ-001 (shared strict type rules), REQ-002 (reload candidate through the startup parser); AC-1, AC-6
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `scripts/agent/config_builders.py`
