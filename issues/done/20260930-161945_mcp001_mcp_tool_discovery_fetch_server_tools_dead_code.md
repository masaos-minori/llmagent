# McpToolDiscoveryService._fetch_server_tools() is dead code

## Priority
Medium

## Summary
`McpToolDiscoveryService._fetch_server_tools()` in `scripts/agent/services/mcp_tool_discovery.py` is defined but never called anywhere in the repository. `discover_all()` uses the sibling `McpToolsHttpClient.fetch_tools()` path instead. Remove the dead method (or wire it in deliberately) to eliminate a second, diverging tool-validation implementation.

## Background
The module documents a unified severity scheme and duplicate-tool handling for the live tool-discovery pass. `discover_all()` builds the `RuntimeToolRegistry` via `McpToolsHttpClient.fetch_tools()` plus `ToolEntryValidator.validate_entry()`. A separate async method `_fetch_server_tools()` implements an equivalent-but-not-identical fetch-and-validate flow using `self._validate_and_normalize_entry()` that no caller reaches.

## Problem
Two parallel implementations of nearly identical MCP `/v1/tools` fetch-and-validate logic coexist. One is dead. Future maintainers may assume both are live, copy logic between them, or be confused about which path governs production behavior. The two paths also differ subtly in how `cfg.required` escalates per-entry findings, so the dead path is not a byte-for-byte duplicate -- it is latent divergence.

## Reason for Change
Dead code silently accumulates and drifts. This method has had no caller since it was introduced, and its existence risks masking which validation path is authoritative.

## Implementation Intent
Confirm via a caller search that nothing (including tests, dynamic dispatch, or subclass overrides) invokes `_fetch_server_tools()`, then delete the method and its private helper if it too is unused. Preserve behavior by ensuring `discover_all()`'s active path is unchanged.

## Target Files or Areas
- `scripts/agent/services/mcp_tool_discovery.py` (`_fetch_server_tools()`, and check whether `_validate_and_normalize_entry()` becomes unused)

## Required Changes
- Search all of `scripts/` (and `tests/`) for every reference to `_fetch_server_tools` and `_validate_and_normalize_entry`.
- If truly uncalled, delete `_fetch_server_tools()`.
- If `_validate_and_normalize_entry()` is also unused, remove it too; otherwise leave it.
- Do not alter `discover_all()` or `McpToolsHttpClient.fetch_tools()` behavior.

## Constraints
- Behavior of the live discovery path must be unchanged -- this is a deletion-only change.
- Confirm no test asserts on the dead method before removing it.

## Acceptance Criteria
- No remaining definition or call site for `_fetch_server_tools()` in the repository.
- `discover_all()` still builds the same `RuntimeToolRegistry` and emits the same findings (no regression).
- `ruff` / `mypy` clean on the file.

## Testing Expectations
- Existing discovery tests still pass and cover `discover_all()` end-to-end.
- Optionally add a guard test asserting `_fetch_server_tools` no longer exists as an attribute on `McpToolDiscoveryService`.

## Documentation Impact
Check whether any design doc or module docstring references `_fetch_server_tools()` as an active path; update if so.

## Out of Scope
- Any refactor of the live `McpToolsHttpClient.fetch_tools()` path.
- Unifying the two validation implementations into one (a separate improvement).

## Dependencies
N/A: none.

## Unresolved Questions
Whether the dead method was intended to replace `fetch_tools()` in a planned follow-up; if so, track that separately rather than re-wiring it here.

## AI Implementation Instruction
Deletion only. Before deleting, grep every caller across scripts/ and tests/. If any caller exists, report Blocked rather than deleting. Keep discover_all() behavior identical.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260930-161945
- **Related target files**: scripts/agent/services/mcp_tool_discovery.py
