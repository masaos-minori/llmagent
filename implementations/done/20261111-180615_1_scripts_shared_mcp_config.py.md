## Goal
Delete the single-valued `FailurePolicy` enum, the `McpServerConfig.failure_policy` field, and its parse step from `scripts/shared/mcp_config.py` (`REQ-001`, Plan Phase 1).

## Scope
**Release unit**: N/A: not part of a release unit

- **Target file**: `scripts/shared/mcp_config.py` (frozen-table row 1).

## Assumptions
- A-1 (from the Plan): a stale `failure_policy` key in an existing `agent.toml` is still accepted, because `_build_single_server` reads keys by name (`v.get(...)`) and there is no unknown-key or allowed-key validation in `scripts/shared/mcp_config.py`; verified once by the load check in the Validation plan.

## Design decisions
- Delete the enum, field, and parse call outright; no alias, shim, or deprecation path (`rules/coding.md` Deprecation policy; the Plan's zero-caller `rg` record shows the only readers are `scripts/agent/startup_reporter.py` — covered by document `20261111-180615_2` — and the field itself).
- Keep `from enum import StrEnum` (line 13): it is still used by `TransportType` (line 31) and `StartupMode` (line 37).
- Do not add strict rejection of unknown config keys: the frozen row requires the stale key to keep loading (Plan Requirement `REQ-001`).

## Alternatives considered
- Keep the enum "for future policies" — rejected in the Plan Design: nothing branches on it and a future policy can add it back together with its behavior.
- Reject a leftover `failure_policy` key — rejected in the Plan Design: it would add new strict validation outside the Issue scope.

## Implementation
### Target file
`scripts/shared/mcp_config.py`

### Procedure
1. Delete the `FailurePolicy` enum (lines 25-28).
2. Delete the `failure_policy` field from `McpServerConfig` (line 95).
3. Delete the `failure_policy=...` keyword argument in `_build_single_server` (line 321).

### Method
Direct deletion only; no rename, no replacement, no signature change. `McpServerConfig` keeps all other fields and defaults unchanged, so every existing constructor call continues to work.

### Details
Before (line 25-28):

```python
class FailurePolicy(StrEnum):
    """Failure policy for MCP servers."""

    FAIL_FAST = "fail-fast"
```

After: block removed entirely (line 24's blank line and lines 29-30's blank lines collapse so `TransportType` keeps two blank lines; `ruff format` confirms).

Before (line 95):

```python
    failure_policy: FailurePolicy = FailurePolicy.FAIL_FAST  # Reserved: runtime call-failure behavior; currently single-valued (FAIL_FAST) with no branching
```

After: line removed.

Before (line 321, inside `_build_single_server`'s `McpServerConfig(...)` call):

```python
        failure_policy=FailurePolicy(v.get("failure_policy", "fail-fast")),
```

After: keyword argument removed; all sibling `v.get(...)` reads unchanged.

## Compatibility considerations
- A stale `failure_policy` key in an existing `agent.toml` stays silently ignored (`v.get`-based parsing, no key whitelist). `rg` confirms `config/agent.toml` carries no `failure_policy` key today, so no configuration file changes here.
- Consumers are updated by the companion documents in the same cycle: `scripts/agent/startup_reporter.py` (document 2), `tests/agent/test_startup.py` (companion row, document 2), and the MCP field reference (document 4). This document changes none of them.
- `tests/shared/test_mcp_config.py` and `tests/shared/test_mcp_config_validation.py` reference no `failure_policy` symbol and must keep passing unchanged.

## Security considerations
No security surface change: a defaulted enum field is removed from a config model; no input validation semantics change. `uv run bandit -r scripts/ -c pyproject.toml -ll` must stay at exit 0.

## Rollback considerations
Single-commit revert: the field has a dataclass default and no persisted form, so no data, config, or migration rollback is needed. Reverting restores `FailurePolicy` and consumers still compile because every consumer reads the field defensively or not at all.

## Validation plan
- `uv run pytest tests/shared/test_mcp_config.py tests/shared/test_mcp_config_validation.py -v` — pass, no `failure_policy` reference remains.
- `rg -n "FailurePolicy|failure_policy" scripts/shared/mcp_config.py` — no hit (whole-repo zero-caller check is Plan Phase 1/3).
- One-off load check (Plan Tests, manual, no new test file): construct a server entry containing a leftover `failure_policy` key through `_build_single_server` and confirm it loads without error (falsifies A-1).
- `uv run ruff check scripts/shared/mcp_config.py`; `uv run mypy --no-namespace-packages scripts/` — no new findings.

## Completion criteria
- `FailurePolicy`, `McpServerConfig.failure_policy`, and the parse keyword are gone from `scripts/shared/mcp_config.py`.
- All Validation plan commands pass.
- No file outside this document's target file changed (consumer edits belong to documents 2 and 4).

## Out of Scope
- `scripts/agent/startup_reporter.py` and `tests/agent/test_startup.py` (document 2), the MCP documentation bullet (document 4).
- Any validation that rejects unknown keys in `[mcp_servers.*]` tables.
- `ToolConfig`/`tool_definitions` cleanups owned by other issues (Plan Out-of-Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261111-183553 | 20261111-183706 | deleted enum/field/parse kwarg; changed: scripts/shared/mcp_config.py; stale-detector clean; Details Before block corrected to current docstring form |
| 2 | Add or update tests per Validation plan | Completed | — | 20261111-183725 | no new tests; one-off load check only 71 targeted tests passed; no test change needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261111-183725 | 20261111-184841 | ruff/mypy/lint-imports/bandit(High+Medium 0)/module-size pass; full suite 12111 passed, 9 skipped; diff-cover: no new lines (pure deletion) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261111-184841 | document 4 owns the docs change N/A: docs/00_index.md row 166 references docs carry no failure_policy mention (rg); bullet removal owned by sibling document 4 in this batch |

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
- **Requirement ID**: `REQ-001` (Plan rows AC-1, AC-2)
- **Source issue**: issues/20261111-163923_compat009_workflow-legacy-compat-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-170504_compat009_workflow-legacy-compat-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-180615
- **Related target files**: `scripts/shared/mcp_config.py`