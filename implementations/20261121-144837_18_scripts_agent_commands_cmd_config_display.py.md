## Goal

Update the call site so `cmd_config_display.py` supplies its own configuration mapping to `build_db_config()`, keeping the load in the process that owns `config/agent.toml` (REQ-003, AC-004).

## Scope
**Release unit**: RU-2

## Assumptions
- `tests/agent/commands/test_cmd_config_char.py` is this row's companion: it lies under `tests/`, is named by exactly this row, and its content follows the output defined here, so it gets no document of its own.
- The printed output strings are characterization baselines; this row must not change what is printed.
- The lazy import is kept.

## Design decisions
- Only the argument source changes; the displayed key names and the `(config error: ...)` fallback wording stay, because the companion test asserts exact output strings.
- The stale `rag.toml` name in the configuration-directory line is not touched by this row (unrelated cleanup, out of scope).

## Alternatives considered
- N/A: call-site update only.

## Implementation
### Target file
`scripts/agent/commands/cmd_config_display.py`
### Procedure
- Change the `_build_db_cfg()` call (line 176) to the injected-configuration signature defined by Plan row 8.
- Keep the `try/except ValueError` fallback that prints `(config error: {e})`.
### Method
- Pass the mapping the Agent process owns; no new helper, no formatting change.
### Details
- Verified 2026-11-21: `_print_rag_config()` prints `rag_db_path` and `session_db_path` from the typed result only; it does not print the embedding endpoint, so the companion's expected output is unchanged by REQ-001.

### Companion test files
- `tests/agent/commands/test_cmd_config_char.py`
  - Procedure: Remove the `RAGConfig` import and the `ctx.cfg.rag` fixture construction (lines 18, 31); the output assertions stay unchanged.
  - Validation: `uv run pytest tests/agent/commands/test_cmd_config_char.py -v`

## Compatibility considerations
- Deployment impact: none.

## Security considerations
- N/A: no trust-boundary change.

## Rollback considerations
- N/A: revert the commit within release unit RU-2.

## Validation plan
- `uv run pytest tests/agent/commands/test_cmd_config_char.py -v`
- `uv run ruff check scripts/agent/commands/cmd_config_display.py`, `uv run mypy scripts/agent/commands/cmd_config_display.py`

## Completion criteria
- The command obtains the DB paths through the typed configuration it supplies, and the characterization output strings are byte-for-byte unchanged.

## Out of Scope
- Definition of the typed configuration (Plan rows 8, 9); the `RAGConfig` dataclass itself (Plan row 1).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - the typed-candidate model is defined by that Issue; coordination dependency, either order works |
| 2 | Add or update tests per Validation plan (companion file) | Pending | — | — | Gated: same - shared surface must be re-verified after that Issue lands |
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
- **Related target files**: `scripts/agent/commands/cmd_config_display.py`, `tests/agent/commands/test_cmd_config_char.py`
