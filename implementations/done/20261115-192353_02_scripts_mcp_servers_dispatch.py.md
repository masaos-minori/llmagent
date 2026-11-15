## Goal

Replace `scripts/mcp_servers/dispatch.py`'s local `_write_tools` union with the imported canonical `ALL_SIDE_EFFECTING_TOOLS` (new), so `_is_side_effecting()` covers MDQ `index_paths`/`refresh_index` and dedup no longer misses a side-effecting tool.

## Scope
**Release unit**: N/A: not part of a release unit

- Covers `REQ-002`: `_is_side_effecting()` derives membership from the canonical set instead of a local union.

## Assumptions
- `ALL_SIDE_EFFECTING_TOOLS` is created by sibling procedure `20261115-192353_01_scripts_shared_tool_constants.py.md` and equals the current union plus `MDQ_WRITE_TOOLS` (verified: `dispatch._write_tools` is 23 members, missing exactly `index_paths` and `refresh_index`).
- The canonical name resolves from the earlier-`seq` sibling; this document does not create it.

## Design decisions
- Keep the module-level alias name `_write_tools` and assign it the canonical set directly (`_write_tools = ALL_SIDE_EFFECTING_TOOLS`), so `_is_side_effecting()` and every call site stay unchanged; only the source of membership moves.

## Alternatives considered
- N/A: single obvious delegation; the Plan fixes importing the canonical set.

## Implementation
### Target file
- `scripts/mcp_servers/dispatch.py`

### Procedure
1. In the `from shared.tool_constants import (...)` block (lines 28-37), drop the now-unused category imports (`CICD_WRITE_TOOLS`, `DELETE_TOOLS`, `GIT_WRITE_TOOLS`, `GITHUB_DANGEROUS_TOOLS`, `GITHUB_WRITE_TOOLS`, `RAG_WRITE_TOOLS`, `SHELL_TOOLS`, `WRITE_TOOLS`) and import `ALL_SIDE_EFFECTING_TOOLS` instead. These eight names are referenced only inside the union being removed (lines 46-53).
2. Replace the `_write_tools = (set(...) | ...)` union (lines 45-54) with `_write_tools = ALL_SIDE_EFFECTING_TOOLS`.

### Method
- Behavior-preserving for all currently-covered tools; adds `index_paths`/`refresh_index` to the dedup membership, closing the documented gap. `_is_side_effecting()` (lines 158-160) keeps its `tool_name in _write_tools` body.

### Details
- `frozenset` supports `in` the same as the previous `set`, so the membership test is unaffected. Do not touch the durable dedup store or `_is_side_effecting()` logic.

## Compatibility considerations
- Import cleanup required: leaving the eight category imports unused would trip `ruff` F401; they are removed in step 1.
- Import direction unchanged (`mcp_servers/` importing from `shared/`).

## Security considerations
- Aligns with ADR-004: keyed MDQ calls now dedup instead of executing twice, so a duplicated side-effecting call is served from cache.

## Rollback considerations
- Revert the commit: restore the union and the eight category imports.

## Validation plan
- `pytest tests/mcp_servers/test_mcp_dispatch.py` — a keyed MDQ `index_paths`/`refresh_index` duplicate is deduplicated (served), not re-executed; no new failures.
- `uv run ruff check scripts/mcp_servers/dispatch.py` — no unused imports; `uv run mypy --no-namespace-packages scripts/` clean.

## Completion criteria
- `scripts/mcp_servers/dispatch.py` no longer defines a local category union; `_write_tools` is `ALL_SIDE_EFFECTING_TOOLS`.
- `index_paths`/`refresh_index` are covered by `_is_side_effecting()` and dedup.

## Out of Scope
- Changing `_is_side_effecting()` logic or the dedup store; editing `tool_constants.py` (owned by sibling seq 01); `server.py` idempotency boundary (`mcproute001`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Import `ALL_SIDE_EFFECTING_TOOLS`, drop unused category imports, set `_write_tools` to canonical | Completed | 20261115 | 20261115 | REQ-002 _write_tools = ALL_SIDE_EFFECTING_TOOLS; category imports dropped |
| 2 | Add/extend dispatch dedup test covering MDQ `index_paths`/`refresh_index` keyed duplicate | Completed | — | 20261115 | REQ-002, REQ-005 test_keyed_mdq_duplicate_is_deduplicated added to test_mcp_dispatch.py |
| 3 | Run validation sequence (`rules/toolchain.md`) | Completed | — | 20261115 | pytest + ruff + mypy 484 passed targeted; ruff/lint-imports/mypy clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261115 | N/A: no doc row in this Plan N/A: no doc row in this Plan |

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
- **Requirement ID**: `REQ-002` (dispatch derives side-effect membership from the canonical set)
- **Source issue**: `issues/20261111-163800_sideeffect001_side-effect-classification-central.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-052032_sideeffect001_side-effect-classification-central.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-192353
- **Related target files**: `scripts/mcp_servers/dispatch.py`