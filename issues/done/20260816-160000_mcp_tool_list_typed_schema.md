# Introduce a typed schema (TypedDict) for MCP `TOOL_LIST` definitions across `scripts/mcp_servers/**/*_tools.py`

## Priority
Low

## Summary
Every `scripts/mcp_servers/**/*_tools.py` module (`git_tools.py`, `read_tools.py`,
`write_tools.py`, `delete_tools.py`, and likely others) types its `TOOL_LIST`/tool-property
dicts as bare `dict[str, Any]`, which the Type Safety Rules discourage ("do not use `Any`
... unless needed"). This was raised independently in at least 3 separate refactor cycles
(`git_tools.py`, `read_tools.py`, `write_tools.py`) as a cross-cutting, not single-file,
improvement.

## Reason for Change
`dict[str, Any]` provides no static guarantee about a tool schema's shape (required fields,
value types), so a typo in a `TOOL_LIST` entry (e.g. misspelled key, wrong value type for
`is_write`) would not be caught by `mypy`/`pyright`. A shared `TypedDict` definition would let
every `*_tools.py` module benefit from static shape-checking, and would need to be decided once
and applied uniformly rather than ad hoc per file (each individual refactor cycle correctly
deferred this as out-of-scope for a single-file, no-behavior-change task).

## Implementation Intent
Define `McpToolProperty`, `McpInputSchema`, and `McpTool` `TypedDict`s (exact shape to be derived
from actual usage across all `*_tools.py` files, not guessed) in a shared location (e.g.
`scripts/mcp_servers/models.py` or a new `scripts/mcp_servers/tool_schema_types.py`). Since
`TypedDict` is erased at runtime, this should be a pure static-typing change with zero behavior
impact — but because ~13+ modules share the same `TOOL_LIST` pattern (per `git_tools.py`'s
Proposals note), the full `mypy`/`pyright` surface and the schema-contract test suite must be
re-verified across every affected module, not just one.

## Target Files or Areas
- `scripts/mcp_servers/git/git_tools.py`
- `scripts/mcp_servers/file/{read,write,delete}_tools.py`
- `scripts/mcp_servers/web_search/web_search_tools.py`
- Unknown: `scripts/mcp_servers/{mdq,github,cicd,rag_pipeline,shell}/*_tools.py` — confirm which
  modules define a `TOOL_LIST` before starting (not all were audited)
- `tests/mcp_servers/test_tool_schema_contract.py`, `tests/mcp_servers/test_mcp_tool_schema_exports.py`
  (schema-contract tests exercising all of the above)

## Required Changes
- Read every `TOOL_LIST` entry across all `*_tools.py` modules to derive the actual field set
  before defining the `TypedDict`s (do not guess).
- Define the shared `TypedDict`s in one location.
- Update each `*_tools.py` module's `TOOL_LIST` annotation to use the new types.
- Re-run `mypy`/`pyright` across the full `scripts/mcp_servers/` tree.

## Acceptance Criteria
- `mypy`/`pyright` pass with 0 new errors across all touched `*_tools.py` modules.
- `tests/mcp_servers/test_tool_schema_contract.py` and
  `tests/mcp_servers/test_mcp_tool_schema_exports.py` pass unchanged.
- No `TOOL_LIST` value or JSON-schema shape changes (verify via before/after value-equality
  check per module, as was done for the individual metadata-extraction refactors).

## Testing Expectations
Full `tests/mcp_servers/` regression run; `mypy`/`pyright` on the whole `scripts/mcp_servers/`
tree; explicit before/after `TOOL_LIST` value-equality check per touched module.

## Documentation Impact
None expected — internal type-safety improvement only.

## Out of Scope
- Do not change any tool name, description string, or schema field value.
- Do not touch the shared metadata-literal constants already extracted per module (e.g.
  `_REPO_PATH_PROPERTY`, `_FILESYSTEM_DELETE_METADATA`) — this issue is about typing the
  container shape, not further deduplicating literals.

## AI Implementation Instruction
Enumerate every `*_tools.py` module with `rg -l "TOOL_LIST" scripts/mcp_servers/` before
defining the `TypedDict`s, so the type reflects the full actual field set used repo-wide, not
just the 3-4 modules that originally raised this. Treat this as a single-purpose typing PR — do
not bundle in unrelated tool-schema refactors.
