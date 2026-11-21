## Goal

Give the standalone CLI entry point in `scripts/db/` its typed configuration at the entry boundary, so it no longer loads `agent.toml` inside `db/` (REQ-004, REQ-005, AC-004).

## Scope
**Release unit**: RU-2

## Assumptions
- `tests/db/test_recovery_drill.py` is run as an affected test and is not a target row.
- Stop-and-report condition: if this CLI cannot obtain the typed configuration without loading `agent.toml` inside `scripts/db/`, the implementation stops and reports instead of inventing a new configuration source (the Issue's AI Implementation Instruction). The plan's Risk list names this as the known failure mode for standalone CLI entry points.

## Design decisions
- The CLI receives the typed maintenance configuration from its caller (a wrapper that owns `config/agent.toml`) or from an explicit entry-boundary argument; the `--archive-dir` command-line override keeps precedence over the configured value.

## Alternatives considered
- Let the drill CLI keep its own load: rejected by AC-004, which allows no load call inside `scripts/db/`.

## Implementation
### Target file
`scripts/db/recovery_drill.py`
### Procedure
- Update the `build_db_config()` call (line 155) and the `_resolve_archive_dir()` call (line 289) to the injected-configuration signatures defined by Plan rows 8 and 9.
- Add the entry-boundary parameter that supplies the typed configuration to the drill entry point.
### Method
- Drill artifact paths and the archive directory are read from the injected configuration; the drill behaviour itself is unchanged (REQ-005).
### Details
- Verified 2026-11-21: this module imports `build_db_config` from `db.config` (line 32) and `_archive_db_file`, `_resolve_archive_dir` from `db.rotation` (line 37); the `--help` text documents the archive-directory default, which must be reworded to name the injected configuration rather than `rotation._resolve_archive_dir` reading `agent.toml`.

## Compatibility considerations
- Deployment impact: none (`config/agent.toml` `cp` line unchanged); the entry point is invoked by the same caller, which now supplies the configuration.

## Security considerations
- N/A: no trust-boundary change.

## Rollback considerations
- N/A: revert the commit within release unit RU-2.

## Validation plan
- `uv run pytest tests/db/test_recovery_drill.py -v` (affected test)
- `uv run python tools/check_db_separation.py`
- `uv run ruff check scripts/db/recovery_drill.py`, `uv run mypy scripts/db/recovery_drill.py`

## Completion criteria
- No `ConfigLoader` use in this module; the CLI obtains its paths and archive directory from the typed configuration supplied at the entry boundary, or the implementation reports the gap instead of guessing a source.

## Out of Scope
- Definition of the typed configuration (Plan row 9), the caller-side construction (Plan row 16), test changes (Plan row 26).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - the typed-candidate model is defined by that Issue; coordination dependency, either order works |
| 2 | Add or update tests per Validation plan | Pending | — | — | Gated: same - affected test only, no assertion changes proven |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: same - shared surface must be re-verified after that Issue lands |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Gated: same - the maintenance documentation row is Plan row 30 |

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
- **Requirement ID**: REQ-004, REQ-005 (the CLI entry obtains typed configuration at its entry boundary)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `scripts/db/recovery_drill.py`
