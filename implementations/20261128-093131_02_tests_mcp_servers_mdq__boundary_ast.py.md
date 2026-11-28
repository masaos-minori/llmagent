## Goal

Provide the AST decisions the boundary test needs — alias-aware import resolution, connection-creation call sites, and the exception record shape — so the test decides from the parsed tree instead of from text (`REQ-002`, `REQ-003`, `AC-2`).

## Scope
**Release unit**: N/A: not part of a release unit

- New helper module with three responsibilities: resolve imported packages per module, report the call sites that create a SQLite connection, and define the exception record shape the boundary test uses.
- No test cases in this module: the cases live in `tests/mcp_servers/mdq/test_mdq_rag_boundary.py` (row 3), which is the module `rules/toolchain.md:169` and `tools/_validation_gate_toolchain.py:117` run.

## Assumptions

- The helper is imported as `tests.mcp_servers.mdq._boundary_ast`. `tests/__init__.py` exists and `tests/mcp_servers/mdq/` has no `__init__.py`, so the subpackage resolves as a namespace package, the same way `tests.shared.runtime_tool_factory` and `tests.agent._producer_registry` are imported today.
- Module classification stays as it is: `tools/check_test_taxonomy.py` classifies only `tests/agent` and `tests/shared`; a module outside those areas is checked only when it carries a marker, and a helper module carries none.
- The helper must keep the boundary test's recorded profile: `radon cc -s` rank A for every function, no `vulture` finding at `--min-confidence 80`, no `bandit -c pyproject.toml -ll` finding (Plan Step 5 baseline).
- The AST pattern to follow is `tests/rag/test_maintenance_boundaries.py:13-23`, which resolves imports but not calls; this module adds the call resolution.
- Comment and docstring text cannot produce a violation because the decision is taken from parsed nodes, which is the difference `REQ-002` asks for.
- Dynamic access through `importlib` or `getattr` is not detected (`UNK-04`, plan default: static aliases only), and the documentation states that limit in row 4.

## Design decisions

- The helper returns decisions (resolved names, call sites), not verdicts. The rule sets — which package pairs are forbidden, which modules own a database — stay in the boundary test, so one module holds the policy and the other the parsing.
- Call resolution covers three bindings: the module name `sqlite3`, an alias bound to it (`import sqlite3 as s3`), and a `from sqlite3 import connect` binding. A call inside a function body is found by walking the tree, which is what makes the wrapper case detectable.
- Import resolution covers `import x as y` and `from x import y`, and resolves to the forbidden package by the dotted name the parser sees, not by the alias.

## Alternatives considered

- Put the parsing inside the boundary test: rejected, the test would then mix the rule sets with the parsing and the record shape, and the helper is what the plan names as the target row.

## Implementation
### Target file
`tests/mcp_servers/mdq/_boundary_ast.py` (new)

### Procedure
1. Add `resolve_imports(path)`: parse the file and return the resolved dotted names for `Import` and `ImportFrom` nodes.
2. Add `connection_call_sites(path)` (new): return the call sites whose function resolves to `sqlite3.connect` through the module name, an alias, or a `from sqlite3 import connect` binding, including calls inside function bodies, and the string-constant argument when the target is statically resolvable.
3. Add the exception record `ExceptionRecord` (new) with the fields `rule`, `module`, `reason`, `owner`, `expiry` (`docs/00_governance/governance_03_issue-and-uncertainty-management.md` Exception Record Fields, line 741).

### Method

- Parse once per file and keep the module read in the test's existing scan entry point (`_py_files()`), so the helper does not change which directories are scanned.

### Details

- The record is a plain value object; the expiry comparison is done by the test, which is the CI check (`UNK-01`, plan default), so the helper does not add a checker and `tools/TOOL_DESCRIPTIONS.md` does not change.

## Compatibility considerations

- No `scripts/` module changes, so the module-size gate and the diff-scoped coverage gate have no production lines to measure.
- `ruff` and `mypy` run over `tests/` in the full sequence, so the helper is held to the same typing standard as the test.

## Security considerations

- `N/A: test-only change.`

## Rollback considerations

- `N/A: revert the commit.`

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_rag_boundary.py -m repo_scan` (the cases that exercise the helper)
- `uv run ruff check tests/mcp_servers/mdq/_boundary_ast.py && uv run mypy tests/mcp_servers/mdq/_boundary_ast.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- Alias imports and wrapper connection creation are resolved from the parsed tree, comment text is not, and the record shape carries the five governance fields (`AC-2`).

## Out of Scope

- The rule sets, the exception records, the expiry and missing-module checks, and the `repo_scan` marker (`tests/mcp_servers/mdq/test_mdq_rag_boundary.py`, row 3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 3 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | The "Add or update tests" step does not apply: this row has no test module of its own; the cases are in row 3 |

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
- **Requirement ID**: REQ-002, REQ-003, AC-2
- **Source issue**: `issues/20261119-142131_mdqmcp009_mdq-rag-boundary-rules.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-192529_mdqmcp009_mdq-rag-boundary-rules.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-093131
- **Related target files**: `tests/mcp_servers/mdq/_boundary_ast.py`
