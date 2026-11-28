# Enforce the MDQ/RAG boundary with import rules and AST checks

## Goal
- Move the MDQ, RAG, and Agent boundary from filename and substring scanning to import-linter contracts and AST checks, so alias imports, wrapper connection creation, and comment text cannot change the result, and so every exception is an interface-level record with a rule, a reason, an owner, and an expiry that fails CI when it lapses.

## Priority
Medium

## Scope
- **In-Scope**:
  - New import-linter contracts for the boundary directions that are currently unenforced: `mcp_servers.mdq` must not import `rag` or `mcp_servers.rag_pipeline`; `mcp_servers.rag_pipeline` must not import `mcp_servers.mdq`; `agent` must not import `mcp_servers.mdq`.
  - AST-based checks in the boundary test: prohibited imports detected from the parsed tree (including `import x as y` and `from x import y`), and direct SQLite connection creation detected as a call, not as a substring, outside the set of modules that own a database.
  - Exceptions become interface-level records (rule, module, reason, owner, expiry) following the Exception Record Fields convention; an expired exception fails the test; an exception naming a module that no longer exists fails the test.
  - The stale allowlist entry `db_migrations.py` is removed.
  - The boundary test carries the `repo_scan` marker, because it scans the whole repository.
  - Documentation states which boundaries import-linter enforces, which remain conventions, and the exception policy.
- **Out-of-Scope**:
  - The existing six contracts (`shared-is-leaf`, `db-only-uses-shared`, `rag-no-agent-or-mcp_servers`, `mcp_servers-no-agent`, `eventbus-is-isolated`, `agent-mcp-config-models`): unchanged, and `lint-imports` must stay green.
  - MDQ runtime behavior.
  - `agent → rag`: the documented hierarchy permits it (`docs/40_shared/shared_01_overview.md` section 3, `.importlinter` line 13), so this Plan does not add a contract for it; the decision is recorded as an Unknown.
  - Detecting dynamic access through `importlib`, `getattr`, or a runtime string: out of practical AST scope, and the documentation must not claim it.
  - Any ADR decision change (an ADR change needs a maintainer approval record; this Plan does not write or simulate one).
- **Dependencies**: none blocking; independent of the other MDQ issues. Should land before the mdqmcp010 plan, which reclassifies production readiness against this boundary.

## Background
Source issue: `issues/20261119-142131_mdqmcp009_mdq-rag-boundary-rules.md` (consolidated MDQ MCP backlog, Issue 9).

`.importlinter` holds six contracts, none named for MDQ. `tests/mcp_servers/mdq/test_mdq_rag_boundary.py` enforces the boundary by reading source files as text: substring checks for `rag.sqlite`, `mdq.sqlite`, `from mcp_servers.mdq`, and `sqlite3.connect`, plus a filename allowlist.

Adversarial verification against current source (evidence revision in Traceability):
- Confirmed: no contract names MDQ. `mcp_servers-no-agent` (line 50) covers `mcp_servers` as a whole, so `mcp_servers.mdq` importing `agent` is already forbidden; the `mdq` to `rag` direction, the `rag_pipeline` to `mdq` direction, and the `agent` to `mcp_servers.mdq` direction are not covered by any contract.
- Confirmed: the issue's `Needs confirmation` claim that the tests acknowledge string scans are not runtime guarantees holds — `test_mdq_rag_boundary.py:57` states "static string/import scan, not a runtime guarantee", and `docs/22_mcp/mcp_05_04_mdq-rag-boundary.md:79` repeats it.
- Confirmed: the substring scan cannot see alias imports. `test_agent_layer_has_no_direct_mdq_sqlite_access` matches the literal `from mcp_servers.mdq` (line 62), so `import mcp_servers.mdq as mdq`, `from mcp_servers import mdq`, and `import mcp_servers.mdq.mdq_service` are not detected.
- Confirmed: the substring scan reports text, not calls. `sqlite3.connect` is matched anywhere in the file, so a comment or docstring that writes the call is a violation, while a connection created through an alias (`import sqlite3 as s3`, `from sqlite3 import connect`) is not. `scripts/agent/services/workflow_schema.py:69` is a comment that contains `sqlite3.connect()`; it passes only because the agent rule does not scan for that pattern.
- Confirmed: the shared allowlist has a stale entry. `db_migrations.py` (line 79) was removed in commit `70391b306` ("refactor(db): remove migration framework, enforce current-schema gate"); no `scripts/shared/db_migrations.py` exists. The two remaining entries name modules that exist and create connections to their own stores, not to an MDQ or RAG database: `schema_fingerprint.py` (line 75, in-memory at `scripts/shared/schema_fingerprint.py:217`) and `mcp_dedup.py` (line 83, `mcp_dedup.sqlite` at lines 172, 418, 489).
- Confirmed: connection creation today happens in `scripts/db/helper.py` (lines 224, 254), `scripts/db/recovery_drill.py:85`, `scripts/db/rotation.py:56-57`, `scripts/eventbus/db_conn.py:92` and `scripts/eventbus/db_tools.py` (lines 75, 110-111), `scripts/mcp_servers/mdq/mdq_service.py` (lines 115, 128), `scripts/mcp_servers/mdq/health_check.py:155`, and `scripts/shared/schema_fingerprint.py:217` and `scripts/shared/mcp_dedup.py` (lines 172, 418, 489). `agent` and `rag` create no connection; `agent` imports `sqlite3` in 21 modules for `Row` and exception types, so a blanket "agent must not import sqlite3" contract is not satisfiable and the rule has to be about connection creation.
- Confirmed: the three new contracts are satisfiable against current source. `grimp` reports no import from `mcp_servers.mdq` to `rag`, from `rag` or `mcp_servers.rag_pipeline` to `mcp_servers.mdq`, and from `agent` to `mcp_servers.mdq`; `PYTHONPATH=scripts uv run lint-imports` reports 6 kept, 0 broken at the evidence revision.
- Confirmed: the boundary test scans source files under selected `scripts/` subdirectories (`_py_files()` at line 12, called for `mcp_servers/mdq`, `mcp_servers/rag_pipeline`, `agent`, `shared`) but carries no `repo_scan` marker, while `pyproject.toml:147` defines `repo_scan` as tests that scan the whole repository and `tests/agent/workflow/test_no_workflow_bypass.py:117` marks its `scripts/`-wide AST scan with it.
- Confirmed: `tools/_validation_gate_toolchain.py:117` names `tests/mcp_servers/mdq/test_mdq_rag_boundary.py` as a gate, and `rules/toolchain.md:169` runs it, so the file name must not change.
- Confirmed: CI runs `PYTHONPATH=scripts uv run lint-imports` (`.github/workflows/ci.yml:31`) and runs all tests including `repo_scan` (`.github/workflows/ci.yml:93`), so both a broken contract and a failing boundary test fail CI.
- Corrected: the issue's Unknown about the design document is resolved. `docs/22_mcp/mcp_05_04_mdq-rag-boundary.md` states the boundary guarantee (lines 69, 79, 86), and `docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md` states the enforcement mechanism and the exception procedure (lines 16, 38). Both are target rows.
- Corrected: the exception-record fields the issue asks for already have a project convention — `docs/00_governance/governance_03_issue-and-uncertainty-management.md:741` requires rule, reason, owner, and expiration date, and an expired exception is treated as an unexplained finding. The Plan applies that convention to the boundary exceptions rather than inventing a new one.

## Problem
The boundary is enforced by text matching, so an alias import, a wrapper that creates a connection, or a comment can change the result; the exception list is a set of filenames with no owner or expiry and already contains a stale entry; and the documentation states a guarantee the tests cannot deliver for the directions import-linter does not cover.

## Reason for Change
Architecture-boundary enforcement is weak, and the reclassification in the mdqmcp010 plan would rest on a guarantee that a substring scan cannot provide. No data-loss risk.

## Implementation Intent
Import direction is enforced by import-linter contracts, which see alias imports; connection creation is enforced by an AST check that looks at calls, not text; exceptions name a module and a rule with an owner and an expiry; and the documentation states what each mechanism actually proves.

## Requirements
- `REQ-001`: `.importlinter` gains three contracts: `mdq-no-rag` (`mcp_servers.mdq` must not import `rag` or `mcp_servers.rag_pipeline`), `rag_pipeline-no-mdq` (`mcp_servers.rag_pipeline` must not import `mcp_servers.mdq`), and `agent-no-mdq` (`agent` must not import `mcp_servers.mdq`). The existing six contracts are unchanged and `lint-imports` stays green.
- `REQ-002`: the boundary test decides from the parsed AST: an import is prohibited when the parsed module resolves to a forbidden package, including `import x as y` and `from x import y`; a connection is created when a call resolves to `sqlite3.connect` through the module name or an alias, including a call inside a wrapper function; comment and docstring text cannot produce a violation.
- `REQ-003`: exceptions are interface-level records with rule id, module, reason, owner, and expiry, following `docs/00_governance/governance_03_issue-and-uncertainty-management.md`'s Exception Record Fields. An expired exception fails the test, an exception naming a module that does not exist fails the test, and the stale `db_migrations.py` entry is removed.
- `REQ-004`: the documentation states the actual capability: which directions the import-linter contracts enforce, that connection creation is enforced by an AST call check outside the database-owning modules, that `agent → rag` remains a convention, and that dynamic access through `importlib` or `getattr` is not detected.
- `REQ-005`: the boundary test carries the `repo_scan` marker, consistent with `pyproject.toml:147`, while keeping the file name the toolchain gate runs.

## Implementation Target Files
**Freeze status**: Frozen — `issue-to-plan` Step 8's Implementation Target Files Validation passes (backtick and structure checks, `tools/audit_plan_target_paths.py`, `tools/check_plan_target_overlaps.py`).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `.importlinter` | Modify | Add `mdq-no-rag`, `rag_pipeline-no-mdq`, and `agent-no-mdq` forbidden contracts; the hierarchy comment gains the MDQ exception the `agent-no-mdq` contract states | REQ-001, AC-1 | Six contracts at lines 20, 31, 41, 50, 58, 69; none names MDQ; the hierarchy comment at line 13 states `agent → rag, db, shared, mcp_servers (installer only)` (checked in Step 3) | `PYTHONPATH=scripts uv run lint-imports` | Verified |
| `tests/mcp_servers/mdq/_boundary_ast.py` | Create | New helper: parse each scanned module and return the imported packages as resolved names (alias-aware) and the call sites that create a SQLite connection (alias-aware, wrapper-aware); expose the exception record shape used by the boundary test | REQ-002, REQ-003, AC-2 | Does not exist; `tests/mcp_servers/mdq/` holds 36 entries and the only AST boundary precedent is `tests/rag/test_maintenance_boundaries.py:13-23`, which resolves imports but not calls (checked in Step 3) | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_rag_boundary.py` | Modify | Replace the substring scans with AST decisions; replace the filename allowlist with exception records carrying rule, module, reason, owner, and expiry; add positive and negative fixtures for alias imports and wrapper connection creation; add the expiry and missing-module checks; remove the stale `db_migrations.py` entry; add the `repo_scan` marker | REQ-002, REQ-003, REQ-005, AC-2, AC-3, AC-5 | `_py_files()` at line 12 scans `scripts/`; substring checks at lines 22, 34, 44, 62, 85; `ALLOWED` set at lines 71-84 with the stale `db_migrations.py` entry at line 79; no `repo_scan` marker (checked in Step 3) | itself | Verified |
| `docs/22_mcp/mcp_05_04_mdq-rag-boundary.md` | Modify | State which directions the new contracts enforce, that connection creation is enforced by an AST call check outside the database-owning modules, that `agent → rag` remains a convention, and that dynamic access is not detected; update the test citations to the new tests | REQ-004, AC-4 | Lines 69, 78, 79, 86 cite the boundary test and state the scan is a source-level guard; line 86 states `agent -> rag` is currently permitted (checked in Step 3) | `uv run python tools/check_docs_content_policy.py` | Verified |
| `docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md` | Modify | Replace the filename-allowlist exception procedure with the exception-record policy (rule, module, reason, owner, expiry, fails CI when expired) and state the enforcement mechanism as import-linter plus the AST call check | REQ-003, REQ-004, AC-3, AC-4 | Lines 16 and 38 describe substring scanning and adding a filename to the `ALLOWED` set with a PR review comment (checked in Step 3) | `uv run python tools/check_docs_content_policy.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Exception Record Fields (line 741): rule, reason, owner, expiration date; an expired exception is an unexplained finding | REQ-003 |
| `pyproject.toml` | `repo_scan` marker definition (line 147); CI runs all tests, local runs deselect it | REQ-005 |
| `rules/toolchain.md` | Gate line 169 runs the boundary test by name; the file name must not change | REQ-005 |
| `tools/_validation_gate_toolchain.py` | Line 117 registers the boundary test as a gate | REQ-005 |
| `.github/workflows/ci.yml` | Lines 31 and 93: `lint-imports` and the full test run are CI gates, so a broken contract or an expired exception fails CI | REQ-001, REQ-003, AC-1, AC-3 |
| `tests/rag/test_maintenance_boundaries.py` | Existing AST boundary-test pattern to follow (lines 13-23) | REQ-002 |
| `tests/agent/workflow/test_no_workflow_bypass.py` | Existing `repo_scan` usage precedent (line 117) | REQ-005 |
| `scripts/db/helper.py` | The sanctioned connection factory (lines 224, 254); the AST rule must not flag it | REQ-002 |
| `scripts/shared/schema_fingerprint.py` | A `shared` module that creates a connection today, in-memory (line 217); becomes an exception record | REQ-003 |
| `scripts/shared/mcp_dedup.py` | The other `shared` module that creates connections, to its own store file (lines 172, 418, 489); becomes an exception record | REQ-003 |
| `scripts/eventbus/db_conn.py` | `eventbus` owns its store and creates a connection (line 92); it is in the database-owning set, not an exception | REQ-002 |
| `scripts/mcp_servers/mdq/mdq_service.py` | MDQ owns `mdq.sqlite` and creates connections (lines 115, 128); it is in the database-owning set | REQ-002 |
| `docs/40_shared/shared_01_overview.md` | Section 3 states `agent/` depends on all layers, which is why `agent → rag` is not made a contract here | REQ-004, Unknown |

## Acceptance Criteria
- `AC-1` (REQ-001): `PYTHONPATH=scripts uv run lint-imports` reports nine contracts, all kept, and a test fixture that imports `rag` from an `mcp_servers.mdq` module, `mcp_servers.mdq` from `mcp_servers.rag_pipeline`, or `mcp_servers.mdq` from `agent` breaks the matching contract.
- `AC-2` (REQ-002): an aliased import of a forbidden package and a connection created inside a wrapper function are detected; the same names written in a comment or docstring are not.
- `AC-3` (REQ-003): an exception whose expiry date has passed fails the test; an exception naming a module that does not exist fails the test; no exception record is missing rule, reason, or owner.
- `AC-4` (REQ-004): the two documents name the mechanism that proves each claim, and each claim matches what the test or contract actually enforces.
- `AC-5` (REQ-005): the boundary test is deselected by `-m "not repo_scan"` and runs in CI.

## Tests
- `REQ-001`: `lint-imports` run plus negative fixtures for the three new contracts.
- `REQ-002`: positive and negative AST fixtures for direct imports, aliased imports, `from x import y`, a wrapper that returns a connection, and comment text; run against the helper.
- `REQ-003`: exception-record tests for a valid record, an expired record, a record missing owner or reason, and a record naming a missing module.
- `REQ-005`: the marker is asserted by running the test with `-m "not repo_scan"` and confirming it is deselected.
- Full sequence: `ruff`, `mypy`, `PYTHONPATH=scripts uv run lint-imports`, and the full test suite including `repo_scan`.

## Documentation Impact
Yes. `REQ-004` drives it. Per `docs/00_index.md`'s "Document References by Task" table, the MDQ vs RAG boundary mapping names `docs/22_mcp/mcp_05_04_mdq-rag-boundary.md`; the enforcement and exception procedure lives in `docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md`. Both are rows in `Implementation Target Files`.

## Assumptions
- The three new contracts are satisfiable at the evidence revision: `grimp` reports no import in any of the three directions, so adding them does not require a source change and does not break an existing contract.
- The database-owning set is `db`, `eventbus`, `mcp_servers.mdq`, and `mcp_servers.rag_pipeline`; connection creation outside that set is prohibited. This matches `docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md`'s Allowed Access Paths table.
- `agent → rag` stays a convention, because `docs/40_shared/shared_01_overview.md` section 3 and `.importlinter` line 13 state the agent may depend on all layers; making it a contract is an owner decision recorded as an Unknown.
- Exception expiry is enforced by the test itself, which is the CI check; no new `tools/` checker is added, so `tools/TOOL_DESCRIPTIONS.md` does not change. The alternative is recorded as an Unknown.
- The boundary test keeps its file name, because `tools/_validation_gate_toolchain.py:117` and `rules/toolchain.md:169` name it.
- No `scripts/` file changes, so the module-size gate and the diff-scoped coverage gate have no production lines to measure; the coverage gate passes trivially and the plan's value is the guard itself.
- Bus factor is 1 for the boundary test and the two docs (single author across all commits).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | How exception expiry is enforced: asserted inside the boundary test or by a separate CI checker | No existing checker reads exception records; `docs/00_governance/governance_03_issue-and-uncertainty-management.md:741` defines the fields but not the enforcement point | Plan default: the boundary test asserts expiry, so CI fails on an expired exception. A separate `tools/` checker would need registration in `tools/TOOL_DESCRIPTIONS.md` and a CI step; ask the governance owner before adding one | False |
| UNK-02 | Whether `agent → rag` should become an enforced contract | The documented hierarchy permits it (`docs/40_shared/shared_01_overview.md` section 3, `.importlinter` line 13); no current violation exists, so a contract would be satisfiable | Ask the architecture owner. Plan default: keep it a convention and state that in the documentation; the issue's Unknown about the design document is resolved by the two target docs | False |
| UNK-03 | Whether `mcp_servers.mdq` may import `rag` for a shared helper in the future | No requirement states a future need; the current guarantee is that neither system accesses the other's database | Confirm with the boundary owner before implementing; if a shared helper is needed, the exception record for `mdq-no-rag` must name the module, rule, reason, owner, and expiry | False |
| UNK-04 | How far alias detection must go: static aliases only, or dynamic import through `importlib` and `getattr` | No current use of dynamic import for these packages was found in `scripts/` | Plan default: static alias detection only, and the documentation states that dynamic access is not detected. Extending it needs a runtime check, which is out of this Plan's scope | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `.importlinter` | Modify | CI and every developer's architecture check; no runtime behavior change | 0 | High (100% single author) | not applicable (not rsynced) |
| `tests/mcp_servers/mdq/_boundary_ast.py` | Create | Test only; imported by the boundary test | N/A (new) | N/A (new) | not applicable (rsynced) |
| `tests/mcp_servers/mdq/test_mdq_rag_boundary.py` | Modify | Test only; the toolchain gate and CI run it by name | 5 | High (100% single author) | not applicable (rsynced) |
| `docs/22_mcp/mcp_05_04_mdq-rag-boundary.md` | Modify | Documentation only; cited by the enforcement doc and the consumer scan | 2 | High (100% single author) | not applicable (rsynced) |
| `docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md` | Modify | Documentation only; states the exception procedure that the test enforces | 2 | High (100% single author) | not applicable (rsynced) |

## Design
- Import direction is enforced by import-linter, which resolves imports from the AST, so alias imports are covered by the contracts themselves. The three new contracts are `forbidden` type with `source_modules` naming one package and `forbidden_modules` naming the other, matching the existing contract style (`.importlinter` lines 20-77). `include_external_packages = True` is already set, so the graph is unchanged.
- The `agent-no-mdq` contract narrows the general statement in the hierarchy comment (line 13), so the comment gains the MDQ exception. It does not change any existing contract, satisfying the issue's constraint.
- A contract cannot express "must not create a connection", and `agent` legitimately imports `sqlite3` in 20 modules for `Row` and exception types, so connection creation stays an AST check. The helper resolves two things per module: the imported package names as the parser sees them (alias-aware), and call sites whose function resolves to `sqlite3.connect` through the module name, an alias, or a `from sqlite3 import connect` binding, including a call inside a function body.
- The database-owning set is derived from the Allowed Access Paths table in `docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md`: `db`, `eventbus`, `mcp_servers.mdq`, `mcp_servers.rag_pipeline`. Modules outside it are scanned for connection creation; `shared` is outside it, so the two `shared` modules that create connections to their own stores become exception records rather than filenames in an allowlist: `schema_fingerprint.py` (in-memory) and `mcp_dedup.py` (`mcp_dedup.sqlite`).
- Exception records replace the filename allowlist. Each record carries rule id, module, reason, owner, and expiry, the fields `docs/00_governance/governance_03_issue-and-uncertainty-management.md` requires, and the test asserts the record is complete, the module exists, and the expiry has not passed. This turns the current "add a filename with an inline comment" procedure into a checkable record.
- Predictable fallout check: no `scripts/` module changes, so the module-size gate has nothing to measure; `tools/_validation_gate_toolchain.py:117` and `rules/toolchain.md:169` keep the test file name; `tests/mcp_servers/mdq/` has no `__init__.py`, so the helper is imported as `tests.mcp_servers.mdq._boundary_ast`, the same way `tests.shared.runtime_tool_factory` and `tests.agent._producer_registry` are imported today. Pinned counts: `tests/shared/test_tool_metadata.py:53` pins the closed `ResourceKeyKind` set and is not affected; no test pins the number of import-linter contracts, so adding three does not break a count assertion.
- Validation quality baseline (Step 5): `radon cc -s` reports rank A for every function in the boundary test (highest A(5)); `vulture --min-confidence 80` reports no findings for it; `bandit -c pyproject.toml -ll` reports no Medium or High finding. The new helper must keep the same profile.
- Consumer scan candidates (`tools/scan_change_consumers.py --seed test_mdq_rag_boundary`): `docs/22_mcp/mcp_05_04_mdq-rag-boundary.md` (lines 69, 78, 79, 108) and `docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md` (lines 16, 38) are target rows because they cite the test and its test names; `tools/_validation_gate_toolchain.py:117` is a reference row that must keep resolving, which is why the file name is unchanged. No Python module imports the test, so no code consumer changes.

## Implementation steps
1. **Phase 1: Characterization pins**
   - [ ] Pin the current gaps as failing fixtures: an aliased import of a forbidden package, a connection created inside a wrapper, and comment text that a substring scan would flag (REQ-002, AC-2; `tests/mcp_servers/mdq/test_mdq_rag_boundary.py`)
   - [ ] Pin the stale allowlist entry as a failing case: `db_migrations.py` is recorded in the allowlist while no such module exists (REQ-003, AC-3; `tests/mcp_servers/mdq/test_mdq_rag_boundary.py`)
2. **Phase 2: Import-linter contracts**
   - [ ] Add `mdq-no-rag`, `rag_pipeline-no-mdq`, and `agent-no-mdq`; update the hierarchy comment with the MDQ exception (REQ-001, AC-1; `.importlinter`)
   - [ ] Run `PYTHONPATH=scripts uv run lint-imports` and confirm nine contracts, all kept (REQ-001, AC-1)
3. **Phase 3: AST helper**
   - [ ] Implement alias-aware import resolution and call-site detection for `sqlite3.connect`, including calls inside function bodies (REQ-002, AC-2; `tests/mcp_servers/mdq/_boundary_ast.py`)
   - [ ] Define the exception record shape with rule, module, reason, owner, and expiry (REQ-003; `tests/mcp_servers/mdq/_boundary_ast.py`)
4. **Phase 4: Boundary test rewrite**
   - [ ] Replace the substring scans with helper decisions; keep the existing guarantees for the cross-DB and agent-import rules (REQ-002, AC-2; `tests/mcp_servers/mdq/test_mdq_rag_boundary.py`)
   - [ ] Replace the filename allowlist with exception records; remove the stale entry; add the expiry and missing-module checks (REQ-003, AC-3)
   - [ ] Add the `repo_scan` marker (REQ-005, AC-5)
5. **Phase 5: Documentation**
   - [ ] State the enforced directions, the AST call check, the remaining convention, and the limits of static detection; update the test citations (REQ-004, AC-4; `docs/22_mcp/mcp_05_04_mdq-rag-boundary.md`)
   - [ ] Replace the filename-allowlist procedure with the exception-record policy (REQ-003, REQ-004, AC-3, AC-4; `docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md`)
6. **Phase 6: Verification**
   - [ ] Run `ruff`, `mypy`, `PYTHONPATH=scripts uv run lint-imports`, and the full test suite including `repo_scan` (REQ-001, REQ-002, REQ-003, REQ-005)
   - [ ] Confirm the docs gates: `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, and `uv run python tools/check_docs_consistency.py --domain mcp` (REQ-004, AC-4)

### Release units
N/A: no release unit — every phase changes its own pins and passes validation alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `.importlinter` | Architecture gate plus negative fixtures for the three new directions | `PYTHONPATH=scripts uv run lint-imports` | Nine contracts, all kept; a fixture import in a new direction breaks the matching contract |
| `tests/mcp_servers/mdq/_boundary_ast.py` | Unit: alias resolution, `from x import y`, wrapper call, comment text | `uv run pytest tests/mcp_servers/mdq/test_mdq_rag_boundary.py -m repo_scan` | Aliased and wrapper cases detected; comment text not flagged |
| `tests/mcp_servers/mdq/test_mdq_rag_boundary.py` | Unit: exception records complete, module exists, expiry not passed | `uv run pytest tests/mcp_servers/mdq/test_mdq_rag_boundary.py` | Stale entry removed; an expired or incomplete record fails |
| Docs rows | Content policy, structure, quality, and domain consistency | `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_consistency.py --domain mcp` | Pass |
| Changed lines | Diff-scoped coverage | `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"`, then `uv run coverage xml` and `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | No `scripts/` lines change, so the gate has no production lines to measure; the guard itself is the deliverable |
| Whole module | Lint, types, security | `uv run python tools/run_validation_gates.py` | Pass |

## Risks
- **Risk**: the three new contracts are satisfiable today but a future shared helper between MDQ and RAG would break `mdq-no-rag` → **Mitigation**: the boundary owner confirms the direction before implementation (UNK-03); if a shared helper is needed, it must be recorded as an exception with rule, reason, owner, and expiry rather than by relaxing the contract.
- **Risk**: an AST check that resolves calls can miss dynamic access, so the documentation must not claim more than it proves → **Mitigation**: the documentation states the limit explicitly, and the plan does not extend detection to `importlib` or `getattr` (UNK-04).
- **Risk**: marking the test `repo_scan` removes it from local full runs, so a boundary violation could be introduced and missed until CI → **Mitigation**: `rules/toolchain.md:169` runs the test by name as an explicit gate, and CI runs all tests; the marker matches the definition in `pyproject.toml:147`.
- **Risk**: exception records with expiry dates fail CI on a date, which can surprise a contributor who did not author the exception → **Mitigation**: the record names the owner, and `docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md` states the policy; the failure message names the rule, the module, the owner, and the expiry.
- **Risk**: the stale `db_migrations.py` entry removal changes the allowlist semantics from filenames to modules, so a module that legitimately creates an in-memory connection could start failing → **Mitigation**: `schema_fingerprint.py` and `mcp_dedup.py` become exception records with their reasons (in-memory, and its own `mcp_dedup.sqlite` store), and the check resolves the connection target so a connection to a store the module owns is not a violation, while a connection to `mdq.sqlite` or `rag.sqlite` is.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: characterization pins for alias imports, wrapper connections, comment text, and the stale allowlist entry | In Progress | — | — | Pins the current gaps as failing fixtures before the change |
| 2 | Phase 2: import-linter contracts for the three unenforced directions | In Progress | — | — | `lint-imports` must stay green |
| 3 | Phase 3: AST helper | In Progress | — | — | Alias-aware import resolution and call-site detection; exception record shape |
| 4 | Phase 4: boundary test rewrite and exception records | In Progress | — | — | Substring scans replaced; stale entry removed; `repo_scan` marker added |
| 5 | Phase 5: documentation | In Progress | — | — | Enforced directions, AST call check, remaining convention, exception policy |
| 6 | Phase 6: verification | Pending | — | — | Lint, types, `lint-imports`, full suite, docs gates |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261128-093131_01_.importlinter.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261128-093131_02_tests_mcp_servers_mdq__boundary_ast.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261128-093131_03_tests_mcp_servers_mdq_test_mdq_rag_boundary.py.md` | 1, 4 | Procedure | Pending | — | — |
| `implementations/20261128-093131_04_docs_22_mcp_mcp_05_04_mdq-rag-boundary.md.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261128-093131_05_docs_22_mcp_mcp_05_05_mdq-enforcement-and-lockdown.md.md` | 5 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261119-142131_mdqmcp009_mdq-rag-boundary-rules.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261127-192529
- **Evidence revision**: 4504b4fd6b2a7ec7ccc08109911a975387b7a8b5
- **Related target files**: `.importlinter`, `tests/mcp_servers/mdq/_boundary_ast.py`, `tests/mcp_servers/mdq/test_mdq_rag_boundary.py`, `docs/22_mcp/mcp_05_04_mdq-rag-boundary.md`, `docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes item 1; `.importlinter:20,31,41,50,58,69`, `grimp` import graph at the evidence revision | `.importlinter` | Phase 2 | AC-1 | `PYTHONPATH=scripts uv run lint-imports`, negative fixtures | Confirmed |
| REQ-002 | Required Changes item 2; `tests/mcp_servers/mdq/test_mdq_rag_boundary.py:12,22,34,44,62,85`, `scripts/agent/services/workflow_schema.py:69` | `tests/mcp_servers/mdq/_boundary_ast.py`, `tests/mcp_servers/mdq/test_mdq_rag_boundary.py` | Phase 3, Phase 4 | AC-2 | positive and negative AST fixtures | Confirmed |
| REQ-003 | Required Changes item 3; `tests/mcp_servers/mdq/test_mdq_rag_boundary.py:71-84` (stale entry at line 78, removed in commit `70391b306`), `docs/00_governance/governance_03_issue-and-uncertainty-management.md:741` | `tests/mcp_servers/mdq/test_mdq_rag_boundary.py`, `tests/mcp_servers/mdq/_boundary_ast.py` | Phase 3, Phase 4 | AC-3 | exception-record tests, expiry and missing-module checks | Confirmed |
| REQ-004 | Documentation Impact; `docs/22_mcp/mcp_05_04_mdq-rag-boundary.md:69,79,86`, `docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md:16,38` | `docs/22_mcp/mcp_05_04_mdq-rag-boundary.md`, `docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md` | Phase 5 | AC-4 | `uv run python tools/check_docs_content_policy.py` | Confirmed |
| REQ-005 | Testing Expectations; `pyproject.toml:147`, `tests/agent/workflow/test_no_workflow_bypass.py:117`, `tools/_validation_gate_toolchain.py:117` | `tests/mcp_servers/mdq/test_mdq_rag_boundary.py` | Phase 4 | AC-5 | deselection run with `-m "not repo_scan"` | Confirmed |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261128-093131 -->