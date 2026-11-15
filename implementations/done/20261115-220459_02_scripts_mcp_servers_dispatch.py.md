## Goal

Derive `scripts/mcp_servers/dispatch.py`'s side-effect membership test
(`_is_side_effecting`) from the imported canonical set
`ALL_SIDE_EFFECTING_TOOLS` instead of a local union, so dedup covers the MDQ
`index_paths`/`refresh_index` tools. (`REQ-002`)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- `ALL_SIDE_EFFECTING_TOOLS` (defined in `shared/tool_constants.py`, row 01) equals
  today's `_write_tools` union plus `MDQ_WRITE_TOOLS`; replacing the local union
  with the import is behavior-preserving except that it closes the MDQ dedup gap.
- `dispatch_tool()` is the shared dispatch entry every MCP server imports; its
  `_is_side_effecting()` (lines 158-160) drives the idempotency dedup branch.

## Design decisions

- Replace the module-level `_write_tools` union with a direct reference to the
  imported `ALL_SIDE_EFFECTING_TOOLS`; keep `_is_side_effecting()` unchanged in
  shape (`return tool_name in <set>`).

## Alternatives considered

- **Keep the local union and just add `MDQ_WRITE_TOOLS`.** Rejected: reintroduces
  the second local reconstruction this Plan removes; the canonical set is the one
  source.

## Implementation
### Target file
`scripts/mcp_servers/dispatch.py`

### Procedure
1. Add `ALL_SIDE_EFFECTING_TOOLS` to the `from shared.tool_constants import (...)`
   block (lines 28-37).
2. Replace the `_write_tools` union (lines 45-54) with a reference to the imported
   set, e.g. `_write_tools = ALL_SIDE_EFFECTING_TOOLS`.
3. Leave `_is_side_effecting()` (lines 158-160) logic unchanged.

### Method
Delete the eight-set `set(...) | set(...) | ...` expression at lines 45-54 and
bind `_write_tools` to the imported frozenset. Do not rename `_write_tools`
(other code and tests may reference it) and do not touch the dedup cache body.

### Details

- Before: `_write_tools` = `set(WRITE_TOOLS) | set(DELETE_TOOLS) |
  set(GIT_WRITE_TOOLS) | set(RAG_WRITE_TOOLS) | set(CICD_WRITE_TOOLS) |
  set(GITHUB_WRITE_TOOLS) | set(GITHUB_DANGEROUS_TOOLS) | set(SHELL_TOOLS)` —
  excludes `MDQ_WRITE_TOOLS`.
- After: membership includes `index_paths`/`refresh_index`, which route through
  `dispatch_tool()` (`mdq_server.py:321`) and are `retryable` in
  `config/mcp_dedup.toml`, so a keyed duplicate is now served instead of
  re-executed.
- `dispatch.py` is imported by every MCP server; keep the public dispatch
  contract (`dispatch_tool`, `DispatchResult`) untouched.

## Compatibility considerations

`dispatch.py` is the shared dispatch entry used by every MCP server and by
`tests/mcp_servers/test_mcp_dispatch.py`. The dedup set grows by exactly the two
MDQ tools; nothing else changes.

## Security considerations

Expanding the dedup set closes a keyless-execution gap (ADR-004): a duplicated
keyed MDQ call previously executed twice. Verify the MDQ dedup path with a test.

## Rollback considerations
N/A: revert the commit.

## Validation plan

| Target | Strategy | Tool / Command | Expected |
|---|---|---|---|
| `scripts/mcp_servers/dispatch.py` | Integration: keyed MDQ call is deduplicated, not re-executed | `uv run pytest tests/mcp_servers/test_mcp_dispatch.py` | dedup serves duplicate; no new failures |
| Whole change | Static: mypy, ruff, import layer | `uv run mypy --no-namespace-packages scripts/`, `uv run ruff check scripts/`, `PYTHONPATH=scripts uv run lint-imports` | all pass |

## Completion criteria

- `dispatch.py` no longer defines a local `_write_tools` union; it references the
  imported `ALL_SIDE_EFFECTING_TOOLS`.
- `index_paths`/`refresh_index` are covered by dedup.
- Existing dispatch tests pass.

## Out of Scope

- Changing the dedup cache TTL/eviction, retry class, or `dispatch_tool()`
  signature.
- Editing `http_transport.py` or `tool_policy.py` (rows 03-04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the local `_write_tools` union with the imported canonical set | Completed | 20261116-071355 | 20261116-071355 |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261116-071355 | 20261116-071355 |  |

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
- **Requirement ID**: `REQ-002` (derive dispatch side-effect membership from the canonical set)
- **Source issue**: `issues/20261111-163800_sideeffect001_side-effect-classification-central.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-052032_sideeffect001_side-effect-classification-central.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-220459
- **Related target files**: `scripts/mcp_servers/dispatch.py`