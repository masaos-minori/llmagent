## Goal

Route `resolve_memory_jsonl_dir()` (`scripts/agent/memory/config_path.py`) through a public config accessor instead of importing the private `_get_str_or_default` from `config_section_builders`, returning the identical path for identical input (`REQ-001`, `REQ-002`, `REQ-003`).

## Scope
**Release unit**: N/A: no release unit.

## Assumptions

- The public accessor `get_str_or_default(cfg, key, default="")` is added to `config_section_builders.py` by the sibling document (this file must not import an underscore-prefixed symbol; REQ-001).
- The late import pattern inside `resolve_memory_jsonl_dir()` is intentional (keeps the memory module free of top-level config imports) and is preserved — only the imported symbol changes from private to public.
- The resolved default remains `/opt/llm/memory` and the returned value equals `ctx.cfg.memory.memory_jsonl_dir` for identical input (REQ-003).

## Design decisions

- Replace the late import `from agent.config_section_builders import _get_str_or_default` with `from agent.config_section_builders import get_str_or_default` and change the call to `get_str_or_default(cfg, "memory_jsonl_dir", "/opt/llm/memory")`. Keep everything else in the function unchanged.
- Keep the import inside the function body (late import), matching the existing pattern.

## Alternatives considered

- Routing through an already-existing public accessor: inspected `config_builders.py`'s export surface (L32-41) — only underscore-prefixed names (`_build_*_config`, `_get_or_default`, `_get_str_or_default`) are re-exported; no public string-key resolver exists. So a new public `get_str_or_default` (new) (added by the sibling document) is required (UNK-01 resolved to Option A).

## Implementation
### Target file
`scripts/agent/memory/config_path.py`
### Procedure
Replace the private import and its call site with the public accessor; preserve the late import and default.
### Method
1. In `resolve_memory_jsonl_dir()`, replace the late import line (currently L20):
   ```python
   from agent.config_section_builders import _get_str_or_default
   ```
   with:
   ```python
   from agent.config_section_builders import get_str_or_default
   ```
2. Replace the call (currently L23):
   ```python
   return _get_str_or_default(cfg, "memory_jsonl_dir", "/opt/llm/memory")
   ```
   with:
   ```python
   return get_str_or_default(cfg, "memory_jsonl_dir", "/opt/llm/memory")
   ```
3. Align the function docstring prose that names the private `_get_str_or_default` helper (L14-16) to name the public `get_str_or_default` (new) instead, so the docstring does not point at a symbol this change removed (consistent with the wfrev002 doc-accuracy goal). Do not change which key or default is read.
### Details

- Do NOT change the key (`memory_jsonl_dir`) or the default (`/opt/llm/memory`) (REQ-003).
- Do not add a top-level config import; keep the import scoped inside the function.

## Compatibility considerations

N/A: no public/runtime interface change; the resolved value is identical for identical input (REQ-003).

## Security considerations

N/A: no change to config loading or path resolution semantics.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/memory/config_path.py` | Unit: resolver returns typed config value; no underscore import | `uv run pytest tests/agent/memory/test_config_path.py` | all pass |
| `scripts/agent/memory/config_path.py` | Static: format, lint, type | `uv run ruff check` / `uv run mypy` on the touched files | clean |

## Completion criteria

- `config_path.py` no longer imports any underscore-prefixed symbol from `config_section_builders` (REQ-001).
- `resolve_memory_jsonl_dir()` returns the same path as before, equal to the typed `cfg.memory.memory_jsonl_dir` (REQ-002, REQ-003).
- `tests/agent/memory/test_config_path.py` passes; a test asserting equality with the typed `cfg.memory.memory_jsonl_dir` is present (REQ-003).
- ruff check and mypy are clean on the touched file (REQ-001, REQ-002).

## Out of Scope

- Changing which config key is read (`memory_jsonl_dir`) or its default (`/opt/llm/memory`).
- Refactoring any other builder or consumer in `config_section_builders`.
- Any change to `memcfg001`'s original `KeyError('memory')` fix.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Route `resolve_memory_jsonl_dir()` through the public accessor (`scripts/agent/memory/config_path.py`, REQ-001/002/003) | Completed | 20261119-102031 | 20261119-102031 | — |
| 2 | Add the typed-equality test and run ruff/mypy/tests (`scripts/agent/memory/config_path.py`, REQ-001/002/003) | Completed | 20261119-102031 | 20261119-102031 | — |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`
- **Source issue**: `issues/20261118-224540_cfgpriv001_config-builder-private-import.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-000535_cfgpriv001_config-builder-private-import.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-072220
- **Related target files**: `scripts/agent/memory/config_path.py`
