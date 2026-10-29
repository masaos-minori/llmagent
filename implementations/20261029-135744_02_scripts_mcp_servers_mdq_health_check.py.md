## Goal

Extend `_collect_dependencies()`'s `except` tuple so a missing/broken
`mdq_mcp_server.toml` degrades to the documented empty-config-view contract instead of
raising at module-scope import (REQ-003).

## Scope

- One `except` line (`scripts/mcp_servers/mdq/health_check.py:169`) plus one new import.

## Assumptions

- The whole probe block inside the `try` (`health_check.py:142-168`) stays under the same
  except; only the caught-type list changes.
- Defaults initialized at `health_check.py:134-140` already provide the empty-config-view
  contract the swallowed path returns.

## Design decisions

- Add `ConfigMissingError` / `ConfigParseError` / `ConfigReadError` explicitly and drop
  `FileNotFoundError` (Plan Design: explicit classes keep the swallow scoped; `load()`
  never surfaces a bare `FileNotFoundError`).
- Keep `PermissionError` in the tuple: the DB-probe block can still raise a raw
  `PermissionError` outside the loader (Plan Assumptions).

## Alternatives considered

- N/A: base-`ValueError` catch rejected in the Plan's Design section — the `try` block
  covers the DB/schema/index probe, so a wide catch would mask probe-side bugs.

## Implementation
### Target file

`scripts/mcp_servers/mdq/health_check.py`

### Procedure

Replace the except tuple at line 169; add the config-error import to the existing
`shared.*` group (`health_check.py:19`).

### Method

```python
from shared.config_errors import ConfigMissingError, ConfigParseError, ConfigReadError
...
    except (
        ConfigMissingError,
        ConfigParseError,
        ConfigReadError,
        PermissionError,
        KeyError,
        TypeError,
    ) as e:
        deps["config"] = f"check failed: {e}"
```

### Details

- The `deps["config"] = f"check failed: {e}"` body and the seven-value return contract
  (`health_check.py:172-180`) are unchanged; on a config error, `mdq_cfg` remains the
  `{}` initialized at line 136.
- No change to `check_health()` behavior for the healthy path.

## Compatibility considerations

- N/A: no signature, return contract, or caller change; `mdq_server.py` module-scope
  usage continues to work.

## Security considerations

- N/A: catch list stays scoped to config errors plus the pre-existing probe errors.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_config.py -v` — T2 (in the sibling test
  procedure document) passes.
- `uv run pytest tests/mcp_servers/mdq` — suite green (fail-closed gate tests unchanged).
- `uv run ruff check scripts/mcp_servers/mdq tests/mcp_servers/mdq`;
  `uv run mypy --no-namespace-packages scripts/mcp_servers/mdq`;
  `uv run bandit -r scripts/ -c pyproject.toml -ll`.
- `PYTHONPATH=scripts uv run lint-imports` — no import-layer violation.

## Completion criteria

- With `ConfigLoader.load` raising `ConfigMissingError`, `_collect_dependencies()` returns
  without raising, with `deps["config"]` recorded and `mdq_cfg` empty (AC-3).
- The existing mdq suite stays green (fail-closed posture gate unchanged).

## Out of Scope

- `scripts/shared/config_loader.py` and `scripts/shared/config_errors.py` (untouchable).
- `scripts/mcp_servers/mdq/mdq_server.py` (sibling procedure document).
- Tests (sibling procedure document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend the `except` tuple and add the import per Method | Pending | — | — | REQ-003 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | REQ-004 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003 (`_collect_dependencies()` swallows the loader's config
  errors and keeps the empty-config-view contract)
- **Source issue**: issues/20261029-012525_ebrev001_mdq-config-loader-exception-mismatch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-075321_ebrev001_mdq-config-loader-exception-mismatch.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-135744
- **Related target files**: scripts/mcp_servers/mdq/health_check.py
