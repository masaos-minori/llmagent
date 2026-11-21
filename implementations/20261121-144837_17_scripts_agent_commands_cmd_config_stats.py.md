## Goal

Update the call site so `cmd_config_stats.py` supplies its own configuration mapping to `build_db_config()`, keeping the load in the process that owns `config/agent.toml` (REQ-003, AC-004).

## Scope
**Release unit**: RU-2

## Assumptions
- `tests/agent/commands/test_agent_cmd_config.py` is run as an affected test and is not a target row; no assertion changes were proven.
- The lazy import is kept: the command module must not import `db` at module import time.

## Design decisions
- The Agent side remains the owner of `config/agent.toml`, so this module keeps loading it and passes the loaded mapping to the typed builder — that is the owner/reader relationship the Plan's Design D1 defines.
- The `ValueError`/`RuntimeError` catch that reports "not configured" is preserved; with injection the failure comes from the supplied mapping, so the wording stays accurate.

## Alternatives considered
- N/A: call-site update only.

## Implementation
### Target file
`scripts/agent/commands/cmd_config_stats.py`
### Procedure
- Change the `_build_db_cfg()` call (line 53) to the injected-configuration signature defined by Plan row 8.
- Keep the behaviour that returns `False` when the configuration cannot supply the paths.
### Method
- Pass the mapping this module already loads; no new helper, no change to the command output.
### Details
- Verified 2026-11-21: the call is inside a `try` that catches `ValueError` and `RuntimeError`, so the failure mode is unchanged for the same values.

## Compatibility considerations
- Deployment impact: none.

## Security considerations
- N/A: no trust-boundary change.

## Rollback considerations
- N/A: revert the commit within release unit RU-2.

## Validation plan
- `uv run pytest tests/agent/commands/test_agent_cmd_config.py -v` (affected test)
- `uv run ruff check scripts/agent/commands/cmd_config_stats.py`, `uv run mypy scripts/agent/commands/cmd_config_stats.py`

## Completion criteria
- The command obtains the DB paths through the typed configuration it supplies; no config load remains inside `scripts/db/`.

## Out of Scope
- Definition of the typed configuration (Plan rows 8, 9), test changes (Plan row 25).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - the typed-candidate model is defined by that Issue; coordination dependency, either order works |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: no assertion changes proven; run as affected test. Gated: same as step 1 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: same - shared surface must be re-verified after that Issue lands |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Gated: same - documentation rows are separate procedure documents |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|---|---|---|---|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003 (the owning process supplies the configuration to the typed builder)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `scripts/agent/commands/cmd_config_stats.py`
