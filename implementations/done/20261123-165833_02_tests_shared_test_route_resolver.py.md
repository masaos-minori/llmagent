## Goal

Add the missing tests for ADR-003 INV-04: routing never falls back to the static `ToolRegistry` (AAL-034).

## Scope
**Release unit**: N/A: not part of a release unit

Test-only change in one existing file. No production change.

## Assumptions

- The existing `test_resolve_rejects_ToolRegistry_fallback_when_runtime_registry_available` resolves a name absent from both registries, so it is weak (`tests/shared/test_route_resolver.py:183`, re-read in Step 3a).
- No routing module imports `shared.tool_registry` today (`scripts/shared/route_resolver.py`, `tool_executor.py`, `tool_transport_invoker.py`, `runtime_tool_registry.py`; rg in Step 3a).

## Design decisions

- Two tests in `TestRoutingSourceIsolation`: a behavioral test with a name registered only in the static registry, and an AST import scan marked `repo_scan`.
- The scan asserts it parsed all four module files, so it cannot pass vacuously.

## Alternatives considered

Patch `ToolRegistry` only: rejected, it does not catch a new import.

## Implementation
### Target file
`tests/shared/test_route_resolver.py`

### Procedure
1. Read `TestRoutingSourceIsolation` and `ToolRoutingError` kinds (`unknown_tool`, `not_ready`).
2. Add a test: pick a tool name present in the static `ToolRegistry` but absent from the runtime registry; assert `resolve()` raises `ToolRoutingError` with kind `unknown_tool`.
3. Add a test: an unwired `ToolRouteResolver()` raises kind `not_ready` for the same name.
4. Add a `repo_scan` test that parses the four routing modules with `ast` and asserts none imports `shared.tool_registry`.

### Method
- Find a static name with `ToolRegistry` public accessors (read `scripts/shared/tool_registry.py` in Step 3a of code-implementation).
- Walk `ast.Import` and `ast.ImportFrom` nodes, including imports under `TYPE_CHECKING`.

### Details
- Mutation check: add `from shared.tool_registry import ToolRegistry` to `scripts/shared/route_resolver.py` temporarily, confirm the scan fails, revert.
- Cite the three tests in ADR-003's INV-04 row in procedure 07.

## Compatibility considerations

N/A: adds a test only; no production behavior changes.

## Security considerations

N/A: no secret, permission, or input handling is touched; test fixtures use dummy tokens only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_route_resolver.py -q`
- ruff and mypy on the file

## Completion criteria

- Both behavioral tests and the scan pass and fail under the mutations.
- No file other than the target changed.

## Out of Scope

- Any file other than the target file (and its companions, if any); any change under `scripts/` or `config/`.
- Approval text: no approver, date, or approval sentence is written.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-23 | 2026-11-23 | Three tests added to `TestRoutingSourceIsolation`: name registered only in the static registry (kind `unknown_tool`), unwired resolver (kind `not_ready`), and the `repo_scan` AST import scan over the four routing modules. |
| 2 | Mutation-check the new test: break the invariant temporarily, confirm the test fails, revert the break | Completed | 2026-11-23 | 2026-11-23 | `from shared.tool_registry import ToolRegistry` added to `scripts/shared/route_resolver.py`; the scan failed, then the file was reverted with `git checkout`. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-23 | 2026-11-23 | Targeted run passes; ruff check and format clean. Per-file mypy reports 4 errors in this file, all pre-existing (the same count at HEAD before the tests were added); `tests/shared/` is outside the CI mypy scope in pyproject `[tool.mypy] files`, so this is not a gate failure, and no new type error was introduced. |

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
- **Requirement ID**: `REQ-002` (no fallback to the static ToolRegistry (ADR-003 INV-04)), `REQ-008` (no production change, every test mutation-checked)
- **Source issue**: issues/20261123-164658_gov006_restore-blocking-verification-rows.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-165432_gov006_restore-blocking-verification-rows.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-165833
- **Related target files**: `tests/shared/test_route_resolver.py`
