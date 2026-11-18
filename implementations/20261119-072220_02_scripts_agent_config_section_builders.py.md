## Goal

Add a public string-key resolver `get_str_or_default` to `scripts/agent/config_section_builders.py` that wraps the private `_get_str_or_default`, exposing a public accessor for `config_path.py` to route through (`REQ-002`, `REQ-003`).

## Scope
**Release unit**: N/A: no release unit.

## Assumptions

- No public string-key resolver currently exists in the config-builders package (verified: `config_builders.py` re-exports only underscore-prefixed names at L32-41); so one must be added (UNK-01 resolved to Option A).
- Adding the public function does not change the `.importlinter` layer relationship — `config_path.py` already imports from `config_section_builders` today, so `lint-imports` stays clean (REQ-002).
- The existing private `_get_str_or_default` (L79-85) is retained and used by the builders; the public wrapper delegates to it so there is a single implementation.

## Design decisions

- Add `get_str_or_default(cfg, key, default="")` directly above or below `_get_str_or_default` that delegates:
  ```python
  def get_str_or_default(cfg: dict[str, Any], key: str, default: str = "") -> str:
      """Public wrapper around ``_get_str_or_default`` for cross-module use."""
      return _get_str_or_default(cfg, key, default)
  ```
- Keep `_get_str_or_default` unchanged as the single implementation.

## Alternatives considered

- Routing `config_path.py` through an already-public accessor: none exists, so this was rejected (see the `config_path.py` document's Alternatives considered).

## Implementation
### Target file
`scripts/agent/config_section_builders.py`
### Procedure
Add a public `get_str_or_default` that delegates to the existing private `_get_str_or_default`.
### Method
1. Insert `get_str_or_default(cfg, key, default="")` immediately after the `_get_str_or_default` definition (L86) in `config_section_builders.py`.
2. Its body is a single delegation `return _get_str_or_default(cfg, key, default)`, preserving the signature and default.
3. Do not modify `_get_str_or_default` itself or any other builder.
### Details

- Preserve the exact resolution semantics (`_or_default(_get_str(cfg, key), default)` via the wrapped helper) so callers get an identical value (REQ-003).
- This is an additive change: no existing caller or signature changes (REQ-002).

## Compatibility considerations

N/A: purely additive public helper; no change to existing public signatures or behavior (REQ-002).

## Security considerations

N/A: no change to config validation or resolution semantics.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/config_section_builders.py` | Unit: new public accessor mirrors `_get_str_or_default` | `uv run pytest tests/agent/test_config_builders.py` | all pass |
| `scripts/agent/config_section_builders.py` | Static: format, lint, type + lint-imports | `uv run ruff check` / `uv run mypy` / `lint-imports` on the touched files | clean; no new cross-layer violation |

## Completion criteria

- `config_section_builders.py` exposes a public `get_str_or_default` that delegates to `_get_str_or_default` (single implementation, no logic duplicated).
- Existing config-builder tests pass (`tests/agent/test_config_builders.py`).
- ruff check, mypy, and lint-imports are clean with no new cross-layer violation (REQ-002).

## Out of Scope

- Refactoring any other builder or consumer in `config_section_builders`.
- Changing `_get_str_or_default`'s signature or internals.
- Re-exporting the new name from `config_builders.py` (a Reference File, not a target).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add public `get_str_or_default` to `config_section_builders` (`scripts/agent/config_section_builders.py`, REQ-002) | Pending | — | — | |
| 2 | Verify accessor mirrors `_get_str_or_default`; run ruff/mypy/lint-imports (`scripts/agent/config_section_builders.py`, REQ-002) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002`, `REQ-003`
- **Source issue**: `issues/20261118-224540_cfgpriv001_config-builder-private-import.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-000535_cfgpriv001_config-builder-private-import.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-072220
- **Related target files**: `scripts/agent/config_section_builders.py`
