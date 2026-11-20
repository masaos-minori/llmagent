# Unify MDQ request schemas, database resource scope, and read/write consistency

## Priority
Medium

## Summary
Make direct MCP validation match Agent validation, model scheduler conflicts by database identity, and define structured read consistency during indexing.

## Background
Source: consolidated MDQ MCP backlog (`memo-issue.md`, Issue 8).

Evidence (`Explicit in code`, by `rg`): `mdq_tools.py:148,174` declares `resource_scope_kind: "mdq_store"` for `index_paths` and `refresh_index`; whether the scope key is derived from the stringified `paths` array (the backlog claim, `resource_scope_keys=["paths"]`) was not read and is `Needs confirmation`. The direct-call unknown-field discard, read inconsistency during refresh, and warning-string dependence are backlog claims and `Needs confirmation`.

## Problem
Agent and direct calls may accept different inputs; scheduler conflicts may not match the single database; reads during refresh may mix generations with only a warning string.

## Reason for Change
Contract consistency after the core integrity work; no data-loss risk of its own.

## Implementation Intent
Agent and direct calls accept and reject the same inputs; conflict identity matches the actual store; reads declare a machine-readable consistency state during refresh.

## Target Files or Areas
- `scripts/mcp_servers/mdq/mdq_models.py`, `mdq_tools.py`, `mdq_server.py`
- `scripts/shared/resource_scope.py`; runtime tool registry and Agent scheduler; MDQ read result models
- `tests/mcp_servers/mdq/test_mdq_tool_schema.py`, `test_mdq_tool_layer_consistency.py`, `test_mdq_get_chunk_behavior.py`

## Required Changes
- Apply the shared strict request base model and schema generator of `issues/20261119-140510_mcpai003_github-pydantic-schema-source.md` (`extra="forbid"`, `model_validate(args)`, strict booleans) to the MDQ models; the MDQ-specific parts are non-empty string, array, and context bounds, the `with_neighbors` decision (implement or remove from model, schema, description), and structured truncation metadata from `get_chunk` using the truncation fields of `issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md` and the result metadata of `issues/20261119-140512_mcpai005_structured-execution-context.md` instead of parsing output markers.
- Replace path-derived scope keys with one stable `mdq_store:<db-identity>` scope following the scope-key convention of `issues/20261119-140520_mcpai013_github-resource-scope-refine.md`; same write scope for index and refresh; decide whether reads share it; path order and duplication do not affect scope; distinguish multiple stores if supported.
- Define old-generation, snapshot, blocking, or mixed-generation semantics during refresh; add `refresh_in_progress` and index-generation metadata applied to search, outline, chunk retrieval, and stats; consider atomic generation switching; remove warning-string dependence.

## Constraints
- Use the final availability, store identity, and error contracts of `issues/20261119-142123_mdqmcp001_mdq-server-boundary.md`, `issues/20261119-142127_mdqmcp005_mdq-transaction-atomicity.md`, `issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md`.

## Acceptance Criteria
- [ ] Agent and direct calls reject the same invalid arguments; unknown and removed fields are errors.
- [ ] Index and refresh always conflict on the same database identity; conflict behavior is testable from discovery through the scheduler.
- [ ] Every read during refresh declares its consistency state; formatter wording cannot change consistency or truncation metadata.

## Testing Expectations
- Agent and direct parity for unknown, empty, wrong-type, and boundary inputs; discovery-to-ToolSpec scope integration; same-store and different-store scheduler tests.
- Batch-refresh search, outline, get-chunk, and stats tests; `with_neighbors` behavior or removal tests.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. Request-validation parity, store identity, and read consistency.

## Out of Scope
- Other servers' schemas and scope refinement (`issues/20261119-140520_mcpai013_github-resource-scope-refine.md` covers GitHub).

## Dependencies
- Depends on `issues/20261119-142123_mdqmcp001_mdq-server-boundary.md`, `issues/20261119-142127_mdqmcp005_mdq-transaction-atomicity.md`, `issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md`, and `issues/20261119-142129_mdqmcp007_mdq-approval-dry-run.md`. Blocks `issues/20261119-142132_mdqmcp010_mdq-release-readiness.md`.
- Also depends on `issues/20261119-140510_mcpai003_github-pydantic-schema-source.md` (shared schema generator), `issues/20261119-140509_mcpai002_github-read-security-boundary.md` (shared strict configuration helpers), and `issues/20261119-140520_mcpai013_github-resource-scope-refine.md` (scope-key convention).

## Unresolved Questions
- `不明`: read semantics during refresh (old generation, snapshot, blocking, or mixed).
- `不明`: whether `with_neighbors` is wanted.
- `不明`: current derivation of the scope key.

## AI Implementation Instruction
Confirm the current scope-key derivation before editing. Keep changes within MDQ metadata, models, and scope. Stop and report if the owner has not decided read semantics.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-142130
- **Related target files**: `scripts/mcp_servers/mdq/mdq_models.py`, `scripts/mcp_servers/mdq/mdq_tools.py`, `scripts/mcp_servers/mdq/mdq_server.py`, `scripts/shared/resource_scope.py`
