## Goal

Decide the boundary from the parsed tree and from exception records, so an alias import, a wrapper connection, or comment text cannot change the result, and so an expired or incomplete exception fails CI (`REQ-002`, `REQ-003`, `REQ-005`, `AC-2`, `AC-3`, `AC-5`).

## Scope
**Release unit**: N/A: not part of a release unit

- The five existing guarantees keep their names, which is what `docs/22_mcp/mcp_05_04_mdq-rag-boundary.md` cites, and each decision is taken through the helper instead of through substring matching.
- New cases: aliased import, `from x import y`, a wrapper that returns a connection, comment text, exception-record completeness, expired record, record naming a missing module.
- The stale `db_migrations.py` entry (line 79) is removed; `schema_fingerprint.py` and `mcp_dedup.py` become exception records.
- The module gains `pytestmark = pytest.mark.repo_scan`.

## Assumptions

- The file name must not change: `tools/_validation_gate_toolchain.py:117` and `rules/toolchain.md:169` run it by name.
- `repo_scan` is defined at `pyproject.toml:147` as tests that scan the whole repository, local runs deselect them, CI runs them; `tests/agent/workflow/test_no_workflow_bypass.py:117` is the precedent for marking an AST scan with it. This module scans `scripts/` through `_py_files()`, which is the same shape.
- `repo_scan` is a functional deselection marker, not a taxonomy classification: `tools/check_test_taxonomy.py` classifies only `tests/agent` and `tests/shared`, so adding it creates no classification finding. Plan `UNK-01` is resolved by the plan default — the test itself asserts expiry, so no new `tools/` checker is added and `tools/TOOL_DESCRIPTIONS.md` does not change.
- Overlap with the mdqmcp010 plan on this module is a sequencing dependency, not a conflict: that plan adds `pytestmark = pytest.mark.contract` with the `REQ-003` citation, and this plan rewrites the body and adds `repo_scan`. Both markers coexist as `pytestmark = [pytest.mark.contract, pytest.mark.repo_scan]`, and the plan states this one lands first. Recorded in the `.importlinter` document as well.
- The database-owning set is `db`, `eventbus`, `mcp_servers.mdq`, `mcp_servers.rag_pipeline` (Plan Assumptions, matching the Allowed Access Paths table in `docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md`). `shared` is outside it, so its two connection-creating modules need exception records rather than an allowlist entry.
- The negative-fixture clause of `AC-1` is asserted through the helper's decision on fixture sources, since import-linter analyzes the real `scripts/` tree and a fixture import there would break CI. Needs confirmation, recorded in the `.importlinter` document.
- Phase 1 pins the four gaps as failing cases and Phase 4 replaces the pins with the AST decisions; the pins and the final assertions are in the same module, so the pins are written as cases that fail until the helper decisions land.
- `db_migrations.py` was removed in commit `70391b306` and no `scripts/shared/db_migrations.py` exists, so the missing-module check is what makes the stale entry fail before it is removed.

## Design decisions

- Assert decisions, not text: comment and docstring text cannot produce a violation once the decision comes from parsed nodes, which is the change `REQ-002` asks for and the reason the substring patterns at lines 22, 34, 44, 62, and 85 are dropped.
- Exception records replace the filename set. Each record names rule, module, reason, owner, and expiry, and the test asserts the record is complete, the module exists, and the expiry has not passed (`AC-3`).
- A connection to a store the module owns is not a violation; a connection to `mdq.sqlite` or `rag.sqlite` is, so the check resolves the target through the call rather than through the module name.

## Alternatives considered

- Keep the filename allowlist and add fields to it: rejected, a set of filenames cannot be checked for expiry or for a module that no longer exists, which is the failure the plan reports.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_rag_boundary.py`

### Procedure
1. Phase 1: add the failing fixtures — an aliased import of a forbidden package, a connection created inside a wrapper, comment text that a substring scan would flag, and the stale `db_migrations.py` entry.
2. Replace the substring decisions with helper decisions: forbidden import directions resolved from the parsed tree, and connection-creation call sites resolved through the module name, an alias, or a `from sqlite3 import connect` binding.
3. Replace the `ALLOWED` set (lines 71-84) with exception records for `schema_fingerprint.py` and `mcp_dedup.py`, each with rule, module, reason, owner, and expiry.
4. Add the expiry check and the missing-module check.
5. Add `pytestmark = pytest.mark.repo_scan` and keep the existing test names.

### Method

- Keep `_py_files()` as the scan entry point and the same scanned subdirectories (`mcp_servers/mdq`, `mcp_servers/rag_pipeline`, `agent`, `shared`), so only the decision changes, not the coverage.
- Fixture sources are parsed from strings or a temporary file, not placed under `scripts/`, so a negative fixture cannot itself break a contract.

### Details

- Failure messages name the rule, the module, the owner, and the expiry, which is the mitigation the plan records for a contributor who did not author the exception.
- The `agent` rule stays about connection creation, not about importing `sqlite3`: `agent` legitimately imports `sqlite3` in 21 modules for `Row` and exception types, so a blanket import rule is not satisfiable.

## Compatibility considerations

- Marking the module `repo_scan` removes it from local full runs; `rules/toolchain.md:169` runs it by name as an explicit gate and CI runs all tests, so it still executes.
- The docs rows cite this module's test names, so the names stay; the docs documents update the citations, not the names.

## Security considerations

- `N/A: test-only change.`

## Rollback considerations

- `N/A: revert the commit.`

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_rag_boundary.py -m repo_scan`
- `uv run pytest tests/mcp_servers/mdq/test_mdq_rag_boundary.py -m "not repo_scan"` — the module is deselected, which is `AC-5`
- `uv run ruff check tests/mcp_servers/mdq/test_mdq_rag_boundary.py && uv run mypy tests/mcp_servers/mdq/test_mdq_rag_boundary.py`
- Full sequence per `rules/toolchain.md`, including the full suite with `repo_scan`.

## Completion criteria

- Alias imports and wrapper connections are detected, comment text is not (`AC-2`); an expired, incomplete, or missing-module record fails (`AC-3`); the module is deselected by `-m "not repo_scan"` and runs in CI (`AC-5`).

## Out of Scope

- The parsing helper (`tests/mcp_servers/mdq/_boundary_ast.py`, row 2).
- The contracts themselves (`.importlinter`, row 1).
- The documentation of the enforced directions and the exception policy (rows 4, 5).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 1 (pins) and Phase 4 (rewrite, records, marker) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-003, REQ-005, AC-2, AC-3, AC-5
- **Source issue**: `issues/20261119-142131_mdqmcp009_mdq-rag-boundary-rules.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-192529_mdqmcp009_mdq-rag-boundary-rules.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-093131
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_rag_boundary.py`
