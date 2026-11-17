## Goal

Replace the bare `int()` / `list()` coercions in `CicdConfig.from_dict` with `get_typed(...)`-style validation so a wrong-typed TOML value raises `ValueError` instead of being silently coerced (REQ-001).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `get_typed` returns the value unchanged for a correct type and raises `ValueError` otherwise; the mandatory `default=` preserves the missing-key default.
- The dataclass defaults are `max_log_size_kb=256`, `repo_allowlist=[]`, `workflow_allowlist=[]` (confirmed in source).

## Design decisions
- Route each typed field through `get_typed(d, "<key>", <type>, "<a noun>", default=<dataclass default>)`, mirroring the canonical precedent in `scripts/mcp_servers/git/git_models.py`.

## Alternatives considered
- Retaining bare `int()`/`list()`: rejected by `rules/coding.md` type-coercion policy (silent truncation of `1048576.0`→`1048576`, `True`→`1`).

## Implementation
### Target file
`scripts/mcp_servers/cicd/cicd_models.py`

### Procedure
1. Replace `int(d.get("max_log_size_kb", 256))` with `get_typed(d, "max_log_size_kb", int, "an integer", default=256)` (REQ-001).
2. Replace `list(d.get("repo_allowlist", []))` with `list(get_typed(d, "repo_allowlist", list, "a list", default=[]))` and `list(d.get("workflow_allowlist", []))` with `list(get_typed(d, "workflow_allowlist", list, "a list", default=[]))` (REQ-001).
3. Import `get_typed` from `shared.config_utils` alongside the existing `get_str`.

### Method
- In `CicdConfig.from_dict` (lines 40-42), substitute the three expressions verbatim. Preserve all other fields and the `@classmethod` signature.

### Details
- Copy each `default=` verbatim from the dataclass field definition (`max_log_size_kb: int = 256`; lists default to `[]`). Omitting `default=` would mean "reject missing keys" and change behavior.

### Companion test files
- `tests/mcp_servers/cicd/test_cicd_models.py`
  - Procedure: add a wrong-typed-value test asserting `ValueError` for `max_log_size_kb` and a missing-key default (T-001; REQ-005)
  - Validation: `uv run pytest tests/mcp_servers/cicd` green

## Compatibility considerations
- Valid-config behavior is unchanged: `get_typed` returns the same value for a correctly-typed key and the same default for a missing/None key. A previously-silently-malformed value now raises `ValueError` at load.

## Security considerations
- The config loader is the fail-fast boundary; wrong types now raise instead of producing a silently wrong value. Do not weaken this.

## Rollback considerations
- Revert the commit; the change is confined to `CicdConfig.from_dict`.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/cicd/cicd_models.py` + `tests/mcp_servers/cicd/test_cicd_models.py` | Unit | `uv run pytest tests/mcp_servers/cicd` | green; new wrong-typed test asserts `ValueError`, missing-key returns default |
| Changed files | Lint / type | `uv run ruff check` + `uv run mypy` on `cicd_models.py` | clean |

## Completion criteria
- No bare `int()` / `list()` remains in `CicdConfig.from_dict`; a wrong-typed `max_log_size_kb` raises `ValueError`; missing keys return defaults (AC-001).

## Out of Scope

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (route `CicdConfig.from_dict` numeric/list fields through `get_typed`)
- **Source issue**: issues/20261118-025551_mcpget001_mcp-models-type-coercion.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-041831_mcpget001_mcp-models-type-coercion.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-070059
- **Related target files**: `scripts/mcp_servers/cicd/cicd_models.py`, `tests/mcp_servers/cicd/test_cicd_models.py`
