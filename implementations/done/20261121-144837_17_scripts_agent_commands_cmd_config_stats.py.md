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
- Finding (2026-11-22, execution): the Method statement "pass the mapping this module already loads" is not accurate for this file: before this row the command did not load `config/agent.toml`, it called `build_db_config()` with no argument. The row required a new lazy `ConfigLoader().load("agent.toml")` at the call site, which is what was implemented. The call still goes through `db.config.build_db_config` rather than `ctx.cfg.db` so that `tests/agent/commands/test_agent_cmd_config.py`'s patch targets continue to fire.
- Finding (2026-11-22, execution): the `except (ValueError, RuntimeError)` catch is preserved and now covers two sources: the load itself (`RuntimeError` when the file is missing) and the mapping validation (`ValueError`). This module never prints the "not configured" wording the Design decision refers to — it only returns `False` — and the message text itself now comes from the typed builders, which name the supplied configuration (Plan row 15). No test asserts the old wording (`test_agent_cmd_config.py` supplies its own `side_effect=ValueError("bad config")`), so the command's behaviour is unchanged.

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
| 1 | Implement the change described in Implementation > Procedure/Method | Completed | 2026-11-22 | 2026-11-22 | Implemented under the gate: the lazy import and the (config error: {e}) and False fallbacks are preserved. |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-22 | 2026-11-22 | N/A: no assertion changes proven; run as an affected test - green. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-22 | 2026-11-22 | $V |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-22 | 2026-11-22 | Documentation rows are separate procedure documents. |

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
