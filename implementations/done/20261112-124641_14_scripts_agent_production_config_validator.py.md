## Goal
Report an empty or absent `sqlite_vec_so` from `ProductionConfigValidator.validate()` like the existing `allowed_root` check (`REQ-005` / `AC-5`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `sqlite_vec_so` is a known top-level key (`valid_keys` update block); the `allowed_root` check (`config.get("allowed_root")`, non-empty string, else `self._record(errors, warnings, msg)`) is the pattern (checked).
- Existing tests that call `validate()` and assert `errors == []` with a minimal config (for example the `allowed_root` acceptance test, located by name) lack the key and will fail; update only those fixtures to include `sqlite_vec_so` (UNK-05), in the companion test file.
- Overlap: `plans/20261112-122030_rmcompat007_history-comment-sweep.md` edits one comment (about line 171) in this file; compatible.
- Code change in `scripts/` (`Requires deploy`): commit and push first; deployment is the user's decision.

## Design decisions
- Add the check beside the `allowed_root` check so both appear in the same section; the message names the key and where to set it, and prints no value.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`scripts/agent/production_config_validator.py`

### Procedure
1. Write the failing tests first (companion).
2. Add the check after the `allowed_root` block.

### Method
- `sqlite_vec_so = config.get("sqlite_vec_so")`; `if not (isinstance(sqlite_vec_so, str) and sqlite_vec_so.strip()): self._record(errors, warnings, "sqlite_vec_so is empty or absent (required for processes that open rag.sqlite or session.sqlite; set the sqlite-vec library path in agent.toml)")`.

### Details
- The file is 14129 bytes, far below the size gate.
- Reuse `_record`; do not add a new severity path.

### Companion test files
- `tests/agent/test_production_config_validator.py`
  - Procedure: Add tests: `validate({"sqlite_vec_so": ""})` and a config without the key report an error naming `sqlite_vec_so`; a non-empty value naming a missing file reports none; update the existing minimal-config fixtures that assert `errors == []` to include a non-empty `sqlite_vec_so`. Written first and shown failing.
  - Validation: `uv run pytest tests/agent/test_production_config_validator.py -v`; then the wider `tests/agent` suite.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_production_config_validator.py -v`, then `uv run pytest tests/agent -q`.
- `uv run ruff format`/`ruff check`/`mypy`/`bandit` on the files; `uv run lint-imports`; `uv run python tools/check_module_size.py` — clean.

## Completion criteria
- Agent startup validation reports an empty or absent `sqlite_vec_so` with an explicit message; a non-empty missing path is accepted; existing tests are updated minimally and pass.

## Out of Scope
- Checking that the library file exists; EventBus validation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the failing tests first and confirm they fail | Completed | 20261112-204830 | 20261112-204830 |  |
| 2 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112-204830 | 20261112-204830 |  |
| 3 | Run the affected suites and the validation sequence (`rules/toolchain.md`) for the changed files | Completed | 20261112-204830 | 20261112-204830 |  |
| 4 | Hand off to `skills/deploy/SKILL.md` after commit and push (the user decides on deployment) | Completed | 20261112-204830 | 20261112-204830 |  |

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
- **Requirement ID**: `REQ-005` — Agent startup validation reports an empty or absent `sqlite_vec_so`
- **Source issue**: issues/20261109-113421_adrrev019_docs-stale-statements.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-112439_adrrev019_docs-stale-statements.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-124641
- **Related target files**: `scripts/agent/production_config_validator.py`, `tests/agent/test_production_config_validator.py`