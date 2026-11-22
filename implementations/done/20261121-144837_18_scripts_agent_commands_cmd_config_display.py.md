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
- Finding (2026-11-22, execution): the Method statement "pass the mapping the Agent process owns" required adding a lazy `ConfigLoader().load("agent.toml")` at the call site, because before this row the command called `_build_db_cfg()` with no argument and loaded nothing. The call is kept through `db.config.build_db_config` rather than using `ctx.cfg.db` so that the tests which patch that function continue to fire; the printed key names and the `(config error: {e})` fallback are unchanged, and the companion passes with the value mirrored by `tests/agent/_config_test_defaults.SHIPPED_MEMORY_EMBED_URL`.

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
| 1 | Implement the change described in Implementation > Procedure/Method | Completed | 2026-11-22 | 2026-11-22 | Implemented under the gate: the lazy import and the False fallback are preserved; the displayed strings are byte-for-byte the characterization baselines. |
| 2 | Add or update tests per Validation plan (companion file) | Completed | 2026-11-22 | 2026-11-22 | Characterization companion is green unchanged. |
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
- **Related target files**: `scripts/agent/commands/cmd_config_display.py`, `tests/agent/commands/test_cmd_config_char.py`
