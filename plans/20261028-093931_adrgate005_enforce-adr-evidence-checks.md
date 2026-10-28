## Goal
- Make the ADR evidence checks blocking and accurate: clean the 14 current findings and the stale citations the checks do not yet see, validate that cited pytest nodes exist, promote the body-evidence rules to errors, and repair `check_adr_reference.py`, which currently verifies nothing.

## Priority
Medium

## Scope
- **In-Scope**:
  - Resolve the 14 current warnings: 6 empty `Implementation` cells in the ADR-003 body and 8 body/index citation differences in `docs/10_adr/adr_01_index.md`.
  - Fix the stale citations that node validation will expose in ADR bodies (ADR-004, ADR-006, ADR-012).
  - Validate by AST that every cited `file.py::node` exists, for the index and for ADR bodies.
  - Promote the two body rules from `WARNING` to `ERROR` after the corpus is clean.
  - Repair the matrix parser in `tools/check_adr_reference.py` for the current six-column table and replace the ADR-ID substring match with a structured comment marker.
  - Add the marker comments to the four source files the matrix names.
  - Update tests, tool descriptions and the governance description.
- **Out-of-Scope**: the Verification Status vocabulary (govrev003); running the cited tests in CI beyond what `.github/run_cited_adr_tests.py` already does; Known Issue and ADR reverse-reference severity (`check_known_deviation_sync.py`); changing any ADR Decision, Invariant or Blocking Gate; writing new product tests.
- **Dependencies**: N/A: none open. Builds on the completed `issues/done/20261027-102002_govrev005_adr-matrix-checker-extension.md`. `plans/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md` and `plans/20261028-093155_ebdurable003_define-publish-dlq-durability.md` do not touch the ADR files listed here (ADR-006 is read-only in ebdurable003); `plans/20261028-094441_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md` edits the ADR-006 Implementation Notes only, so no ordering is required.

## Background
`tools/check_adr_invariant_matrix.py` extracts backticked `path.py::node` citations from the index matrix and fails only when the file is missing; two body rules (empty `Implementation` cell, body/index disagreement) report `WARNING` through `_BODY_RULE_SEVERITY`. `.github/run_cited_adr_tests.py` runs in the CI `lint` job and executes each node cited in the index with pytest, failing when a citation collects zero tests. `tools/check_adr_reference.py` requires a source file named by a matrix row to contain its ADR ID.

## Problem
- Node existence is verified for index citations only through the CI pytest runner, and not at all for ADR bodies. A scan of the ADR corpus found five body citations that do not resolve: `fetch_tools()` in ADR-004, two renamed test methods in ADR-006, and two path-less test files in ADR-012.
- The body rules still warn, so empty evidence cells (six in ADR-003, all marked Blocking) and body/index disagreements (eight rows) do not fail CI.
- `check_adr_reference.py` reads a seven-column table with an `ADR-NNN`-only ID cell; the matrix is now six columns with IDs like `ADR-001 INV-01`, so the parser returns no references and the check passes without checking anything. Its tests use the obsolete table shape.
- Under the current table, four `scripts/` files are named. One (`scripts/agent/workflow_engine_adapter.py`) does not contain `ADR-014` at all, and three contain it only as prose, not as a marker.

## Reason for Change
The checker was shipped with warnings until the corpus was clean. The corpus is now a finite, known list, and the reference check has silently lapsed, so the gate must be repaired before it can be trusted.

## Implementation Intent
Clean the corpus first, then tighten the rules. Use an AST check for node existence because it needs no test imports and is fast; keep the CI pytest runner as the behavioral gate. Define one narrow marker form (a comment line that starts with the ADR ID) so a source file self-identifies deliberately.

## Requirements
- `REQ-001`: The 14 current warnings are resolved: each ADR-003 empty cell cites an existing test or records `Not verified`; each of the 8 index rows is corrected to match its ADR body (the index mirrors the body); ADR Decisions, Invariants and Blocking Gates are unchanged.
- `REQ-002`: The stale body citations are corrected: ADR-004 `fetch_tools()`, the two ADR-006 test method names, and the two ADR-012 path-less test files.
- `REQ-003`: `check_adr_invariant_matrix.py` verifies by AST that each cited node exists in its file for index and body citations (class and function names, `()` suffix and parameter ids `[...]` handled) and reports `ERROR` when it does not.
- `REQ-004`: `_BODY_RULE_SEVERITY` becomes `ERROR` only after REQ-001 leaves no finding; the exit code is non-zero on an empty evidence cell, a body/index disagreement or a missing node; `_TEST_PATH_RE` and the JSON output shape stay as they are.
- `REQ-005`: `check_adr_reference.py` parses the current six-column matrix (ID and Verification Status taken by position from the header) and requires a structured marker, a comment line `# ADR-NNN ...` found with `tokenize`, instead of a substring match; it reports `ERROR` when no row can be parsed.
- `REQ-006`: The marker comment is added to the four matrix-named source files (comment-only change).
- `REQ-007`: Tests cover each new failure mode (missing node, missing file, empty cell, disagreement, parameterized id, no marker, substring-only mention, unparseable matrix) and use the current table shape; the existing tests pass.
- `REQ-008`: `tools/TOOL_DESCRIPTIONS.md`, the two tool docstrings and the governance description state the current checks and severities.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/check_adr_invariant_matrix.py` | Matrix checker | Add AST node validation for index and body citations; promote `_BODY_RULE_SEVERITY` to `ERROR`; update the docstring | REQ-003, REQ-004 / AC-2, AC-3 | `check_invariant_matrix_test_paths` checks only the file component; `_BODY_RULE_SEVERITY = "WARNING"` (checked in Step 3) | `tests/tools/test_check_adr_invariant_matrix.py` | Verified |
| `tests/tools/test_check_adr_invariant_matrix.py` | Matrix checker tests | Add node, parameterized id, body-citation and severity tests | REQ-007 / AC-5 | Existing file with 350 lines of fixtures for the current rules (checked in Step 3) | itself | Verified |
| `tools/check_adr_reference.py` | Reference checker | Fix `parse_matrix_source_refs` for the six-column table; replace the substring match with the `tokenize` marker rule; fail on zero parsed rows | REQ-005 / AC-4 | `parse_matrix_source_refs` requires 7 cells and an `^ADR-\d+$` ID cell and returns 0 references on the live matrix; `check_adr_reference` tests `ref.adr_id not in content` (checked in Step 3) | `tests/tools/test_check_adr_reference.py` | Verified |
| `tests/tools/test_check_adr_reference.py` | Reference checker tests | Replace the obsolete seven-column fixtures; add marker and unparseable-matrix tests | REQ-007 / AC-4, AC-5 | Fixtures use `\| INV-011 \| ADR-004 \| x \| ...` rows (checked in Step 3) | itself | Verified |
| `docs/10_adr/adr_01_index.md` | ADR index matrix | Correct the 8 rows whose cited test files differ from the ADR body | REQ-001 / AC-1 | Warnings for ADR-002 INV-01 and INV-02, ADR-005 INV-02, ADR-006 INV-09, ADR-007 INV-09, ADR-008 INV-01, ADR-009 INV-10, ADR-010 INV-04; the index states a mismatch is resolved by correcting the matrix to the ADR body (checked in Step 3) | `tools/check_adr_invariant_matrix.py` | Verified |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | ADR-003 body | Fill the 6 empty `Implementation` cells (INV-01, 02, 03, 04, 06, 07) with existing tests or `Not verified` | REQ-001 / AC-1 | Six `-` cells in `### Automated Tests`; candidate tests exist for INV-01 (`tests/agent/services/test_mcp_tool_discovery.py`), INV-02 (`tests/shared/test_tool_executor_routing.py`) and INV-06 (`tests/shared/test_runtime_tool_registry.py`); none was found for INV-04 and INV-07 (checked in Step 3) | `tools/check_adr_invariant_matrix.py` | Verified |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | ADR-006 body | Rename two stale cited test methods to the current names | REQ-002 / AC-1 | The body cites `test_nack_increments_delivery_failure_count` and `test_dlq_requeue_increments_dlq_requeue_count_not_delivery_failure_count`; the test file defines the `consumer_delivery_failure_count` names (checked in Step 3) | `tools/check_adr_invariant_matrix.py` | Verified |
| `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | ADR-012 body | Replace the two path-less test file citations with repository-relative paths | REQ-002 / AC-1 | `test_repository_state.py::TestStage3DestinationProtection` and `test_git_service_dispatch.py::TestDestinationBasedProtection` resolve to no file at the repository root (checked in Step 3) | `tools/check_adr_invariant_matrix.py` | Verified |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | ADR-004 body | Replace the stale code reference `fetch_tools()` with a symbol that exists | REQ-002 / AC-1 | The body cites `scripts/agent/services/mcp_tool_discovery.py::fetch_tools()` and the file defines no `fetch_tools` (checked in Step 3) | `tools/check_adr_invariant_matrix.py` | Verified |
| `scripts/agent/orchestrator.py` | Marker comment | Add a `# ADR-014` marker comment; no behavior change | REQ-006 / AC-4 | Named by the ADR-014 INV-01 row; contains `ADR-014` only in prose (checked in Step 3) | `tools/check_adr_reference.py` | Verified |
| `scripts/agent/workflow_engine_adapter.py` | Marker comment | Add a `# ADR-014` marker comment; no behavior change | REQ-006 / AC-4 | Named by the ADR-014 INV-01 row; contains no `ADR-014` text (checked in Step 3) | `tools/check_adr_reference.py` | Verified |
| `scripts/mcp_servers/tool_validators.py` | Marker comment | Add a `# ADR-014` marker comment; no behavior change | REQ-006 / AC-4 | Named by the ADR-014 INV-03 row; contains `ADR-014` only in prose (checked in Step 3) | `tools/check_adr_reference.py` | Verified |
| `scripts/mcp_servers/shell/shell_service.py` | Marker comment | Add a `# ADR-014` marker comment; no behavior change | REQ-006 / AC-4 | Named by the ADR-014 INV-03 row; contains `ADR-014` only in prose (checked in Step 3) | `tools/check_adr_reference.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Tool descriptions | Update the two checker descriptions | REQ-008 / AC-6 | Rows for both checkers describe node IDs and source references (checked in Step 3) | `tools/check_tool_descriptions_sync.py` | Verified |
| `docs/00_governance/governance_04_documentation-checks.md` | Governance check description | Replace the "warns" wording with the error behavior and describe the marker | REQ-008 / AC-6 | Section 12 says the body rules warn with the exit code unchanged and that cited source files carry an `ADR-XXX` comment (checked in Step 3) | `tools/check_docs_quality.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `.github/run_cited_adr_tests.py` | Imports the node-id regex from the matrix checker and runs each index citation in CI; must keep working | REQ-003, REQ-004 |
| `.github/workflows/ci.yml` | Shows the CI `lint` job step that runs the cited-test runner | REQ-003 |
| `.pre-commit-config.yaml` | Hooks `adr-invariant-matrix` and `adr-reference-scoped` invoke both tools by module | REQ-004, REQ-005 |
| `tools/_docs_consistency_lib.py` | `Issue` and `report_and_exit` used by both tools | REQ-004, REQ-005 |
| `tools/check_adr_preservation.py` | Confirms the ADR edits change only verification text | REQ-001, REQ-002 |
| `tests/tools/test_check_adr_preservation.py` | Not edited; shows how ADR text changes are asserted | REQ-001 |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-002): `uv run python tools/check_adr_invariant_matrix.py` reports no finding on the live corpus, and `tools/check_adr_preservation.py` reports no unintended ERROR.
- AC-2 (REQ-003): A missing cited file or node, in the index or in an ADR body, is reported as `ERROR` and fails the run.
- AC-3 (REQ-004): An empty evidence cell and a body/index disagreement are reported as `ERROR`; the JSON output shape and the `.github/run_cited_adr_tests.py` import still work.
- AC-4 (REQ-005, REQ-006): `uv run python tools/check_adr_reference.py` parses the four matrix-named files, passes with the marker present, fails for a file that only mentions the ID in prose, and fails when no row parses.
- AC-5 (REQ-007): New tests cover each new failure mode and the existing checker tests pass.
- AC-6 (REQ-008): `tools/check_tool_descriptions_sync.py` passes and the governance text matches the checks.

## Tests
- Matrix checker: missing node in a present file, class-qualified node, parameterized id, `()` suffix, body citation, severity `ERROR` exit code, JSON shape (REQ-003, REQ-004, REQ-007).
- Reference checker: six-column fixture, marker present, prose-only mention rejected, missing file, zero parsed rows (REQ-005, REQ-007).
- Live runs: both checkers on the repository, `uv run python .github/run_cited_adr_tests.py` import smoke, and `uv run pre-commit run adr-invariant-matrix --all-files` (REQ-004).
- Run `uv run pytest tests/tools -k adr`; ruff, mypy and bandit on both changed tools (REQ-007).

## Documentation Impact
Yes, small (REQ-001, REQ-002, REQ-008): the index matrix and four ADR verification tables under `docs/10_adr/`, plus the governance description under `docs/00_governance/`, found through `docs/00_index.md` "Document References by Task". State the gate severity as current behavior only.

## Assumptions
- The index is corrected to the ADR body (`adr_01_index.md` states the body is the canonical evidence record); where a body cites a file that does not exist the body is corrected instead.
- AST scanning of class and function names is sufficient for existence; it does not prove the test passes, which `.github/run_cited_adr_tests.py` covers for index citations.
- A comment-only marker line in the four source files has no runtime effect.
- Overlap judgment (compatible): `plans/20261028-094441_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md` also targets the ADR-006 file; it edits Implementation Notes only, while this Plan renames two stale test citations in the Verification table.
- The ADR edits touch only Verification tables and cited names, so ADR Decisions and Invariants stay unchanged.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Marker form for source files | Design decision recorded as `Needs confirmation` in the Issue | Plan default: a comment line starting `# ADR-NNN`, detected with `tokenize`; the owner may change the form before `plan-to-implementation-procedure` | False |
| UNK-02 | Pytest collection versus AST for node validation | Issue lists it as `Needs confirmation` | Plan default: AST in the checker (no imports, fast); pytest collection stays in the CI runner for index citations | False |
| UNK-03 | ADR-003 INV-04 and INV-07 have no existing test; recording `Not verified` conflicts with their Blocking column because the index says a `Not verified` row is Non-Blocking | Owner decision on adding tests or adjusting the gate | Record `Not verified` without touching the Blocking column and file a follow-up Issue for the two tests; the Constraint forbids lowering a gate here | False |
| UNK-04 | Whether further stale citations exist in ADR bodies beyond the five found | The scan used the same `.py::node` form as the checker | The new node validation reports any remaining finding in Step 2; fix each before promoting the severity | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/check_adr_invariant_matrix.py` | Modify | Medium | 4 | N/A | not applicable (rsynced) |
| `tests/tools/test_check_adr_invariant_matrix.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tools/check_adr_reference.py` | Modify | Medium | 4 | N/A | not applicable (rsynced) |
| `tests/tools/test_check_adr_reference.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_01_index.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `scripts/agent/orchestrator.py` | Modify | Low | 8 | N/A | not applicable (rsynced) |
| `scripts/agent/workflow_engine_adapter.py` | Modify | Low | 6 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/tool_validators.py` | Modify | Low | 0 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/shell/shell_service.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/00_governance/governance_04_documentation-checks.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
- Path B (more than 3 files; changes CI-facing gate behavior). The tools live in `tools/` outside the `lint-imports` contracts; `tools.check_adr_invariant_matrix` is imported only by `.github/run_cited_adr_tests.py` (its node-id regex), so `_TEST_PATH_RE` keeps its name and shape. `radon cc` reports no function at C or above in either tool.
- Decision 1, order: corpus cleanup before severity promotion, so no commit leaves the checker failing; the node validation lands as `ERROR` from the start because the corpus fix (REQ-001, REQ-002) precedes it.
- Decision 2, node validation: parse the cited file with `ast`, collect class and function names, strip `()` and `[...]`, require each `::` segment to exist. Existence of the file keeps its current message.
- Decision 3, reference parser: locate the `Invariant` and `Verification Status` columns from the matrix header row instead of fixed positions, take every `ADR-NNN` token from the invariant cell, and report an error when the matrix yields no row, so the check can no longer pass vacuously.
- Decision 4, marker: a comment token matching `#\s*ADR-NNN\b`, found with `tokenize` so a string or docstring never counts. The four source files get a one-line marker comment at the top of the module.
- Compatibility: JSON output keys, hook entry points (`python -m tools.check_adr_invariant_matrix`, `python -m tools.check_adr_reference`) and the CI runner import stay unchanged.

## Implementation steps
1. **Phase 1: Corpus cleanup**
   - [ ] Align the 8 index rows to their ADR bodies (REQ-001; `docs/10_adr/adr_01_index.md`)
   - [ ] Fill the 6 ADR-003 cells with existing tests or `Not verified` (REQ-001; `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`)
   - [ ] Fix the stale citations (REQ-002; `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`)
   - [ ] Run `tools/check_adr_preservation.py` and the matrix checker to confirm only the node findings remain
2. **Phase 2: Matrix checker**
   - [ ] Add AST node validation for index and body citations and the tests (REQ-003, REQ-007; `tools/check_adr_invariant_matrix.py`, `tests/tools/test_check_adr_invariant_matrix.py`)
   - [ ] Promote `_BODY_RULE_SEVERITY` to `ERROR` once the live run is clean (REQ-004; `tools/check_adr_invariant_matrix.py`)
3. **Phase 3: Reference checker and markers**
   - [ ] Fix the parser, add the marker rule and update the tests (REQ-005, REQ-007; `tools/check_adr_reference.py`, `tests/tools/test_check_adr_reference.py`)
   - [ ] Add the marker comments (REQ-006; `scripts/agent/orchestrator.py`, `scripts/agent/workflow_engine_adapter.py`, `scripts/mcp_servers/tool_validators.py`, `scripts/mcp_servers/shell/shell_service.py`)
4. **Phase 4: Documentation**
   - [ ] Update the descriptions (REQ-008; `tools/TOOL_DESCRIPTIONS.md`, `docs/00_governance/governance_04_documentation-checks.md`)
5. **Phase 5: Deployment & Verification**
   - [ ] Run the validation plan; after commit and push, hand off to `skills/deploy/SKILL.md` (the user decides to deploy) because four files under `scripts/` change; the edits are comments only (REQ-006; `scripts/agent/orchestrator.py`)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_adr_invariant_matrix.py` | Unit and live run | `uv run pytest tests/tools/test_check_adr_invariant_matrix.py -q`; `uv run python tools/check_adr_invariant_matrix.py` | Tests pass; no finding, exit 0 |
| `tools/check_adr_reference.py` | Unit and live run | `uv run pytest tests/tools/test_check_adr_reference.py -q`; `uv run python tools/check_adr_reference.py` | Tests pass; 4 files checked, no finding |
| ADR edits | Preservation | `uv run python tools/check_adr_preservation.py` | No unintended ERROR |
| CI runner | Import smoke | `uv run python .github/run_cited_adr_tests.py` | Still imports the regex and runs |
| Hooks | Pre-commit | `uv run pre-commit run adr-invariant-matrix --all-files`; `uv run pre-commit run adr-reference-scoped --all-files` | Pass |
| Tool hygiene | Format, lint, types, security | `uv run ruff check tools/check_adr_invariant_matrix.py tools/check_adr_reference.py`; `uv run mypy tools/check_adr_invariant_matrix.py tools/check_adr_reference.py`; `uv run bandit tools/check_adr_invariant_matrix.py tools/check_adr_reference.py` | Clean |
| Docs | Checkers | `uv run python tools/check_tool_descriptions_sync.py`; `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py` | No errors |

Baseline recorded in Step 5: `radon cc` reports no function at C or above in either tool; `vulture` and `bandit` results for `scripts/` earlier in this batch show no finding in the four marker files; the live runs showed 14 matrix warnings and `check_adr_reference.py` reporting no issues while parsing zero references.

## Risks
- **Risk**: A fixed `check_adr_reference.py` now reports errors on files that passed vacuously → **Mitigation**: add the marker comments in the same phase and run the tool on the live matrix before committing.
- **Risk**: Promoting the severity breaks CI on a stale citation not yet found → **Mitigation**: promote only after the live run is clean and re-run the CI runner (UNK-04).
- **Risk**: `Not verified` on ADR-003 INV-04 and INV-07 contradicts their Blocking column → **Mitigation**: do not change the column; record the gap and file a follow-up Issue for the missing tests (UNK-03).
- **Risk**: AST matching misses a node generated dynamically → **Mitigation**: cited nodes are plain classes and functions; the CI runner executes the index citations with pytest.
- **Risk**: ADR edits drift from the Decisions → **Mitigation**: edit verification text only and run `tools/check_adr_preservation.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Corpus cleanup in the index and four ADR bodies | Pending | — | — | |
| 2 | Node validation and severity promotion in the matrix checker | Pending | — | — | |
| 3 | Reference checker repair, marker rule and four marker comments | Pending | — | — | |
| 4 | Tool and governance descriptions | Pending | — | — | |
| 5 | Deployment and verification hand-off | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261027-155848_adrgate005_enforce-adr-evidence-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261028-093931
- **Related target files**: `tools/check_adr_invariant_matrix.py`, `tests/tools/test_check_adr_invariant_matrix.py`, `tools/check_adr_reference.py`, `tests/tools/test_check_adr_reference.py`, `docs/10_adr/adr_01_index.md`, `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `scripts/agent/orchestrator.py`, `scripts/agent/workflow_engine_adapter.py`, `scripts/mcp_servers/tool_validators.py`, `scripts/mcp_servers/shell/shell_service.py`, `tools/TOOL_DESCRIPTIONS.md`, `docs/00_governance/governance_04_documentation-checks.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; 14 warnings reproduced | `docs/10_adr/adr_01_index.md` | Step 1 | AC-1 | `tools/check_adr_invariant_matrix.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1; six empty ADR-003 cells | `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Step 1 | AC-1 | `tools/check_adr_invariant_matrix.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes 3; five stale body citations found by scan | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Step 1 | AC-1 | `tools/check_adr_invariant_matrix.py` | Derived from confirmed evidence |
| REQ-002 | Required Changes 3 | `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | Step 1 | AC-1 | `tools/check_adr_invariant_matrix.py` | Derived from confirmed evidence |
| REQ-002 | Required Changes 3 | `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Step 1 | AC-1 | `tools/check_adr_invariant_matrix.py` | Derived from confirmed evidence |
| REQ-003 | Required Changes 3; checker validates only the file component | `tools/check_adr_invariant_matrix.py` | Step 2 | AC-2 | `tests/tools/test_check_adr_invariant_matrix.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes 3 | `tests/tools/test_check_adr_invariant_matrix.py` | Step 2 | AC-2 | `uv run pytest tests/tools -k adr` | Confirmed by repository evidence |
| REQ-004 | Required Changes 2; `_BODY_RULE_SEVERITY = "WARNING"` | `tools/check_adr_invariant_matrix.py` | Step 2 | AC-3 | `tests/tools/test_check_adr_invariant_matrix.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes 4; parser returns 0 references on the live matrix | `tools/check_adr_reference.py` | Step 3 | AC-4 | `tests/tools/test_check_adr_reference.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes 4 | `tests/tools/test_check_adr_reference.py` | Step 3 | AC-4 | `uv run pytest tests/tools -k adr` | Confirmed by repository evidence |
| REQ-006 | Required Changes 4; four named source files lack a marker | `scripts/agent/orchestrator.py` | Step 3 | AC-4 | `tools/check_adr_reference.py` | Derived from confirmed evidence |
| REQ-006 | Required Changes 4 | `scripts/agent/workflow_engine_adapter.py` | Step 3 | AC-4 | `tools/check_adr_reference.py` | Derived from confirmed evidence |
| REQ-006 | Required Changes 4 | `scripts/mcp_servers/tool_validators.py` | Step 3 | AC-4 | `tools/check_adr_reference.py` | Derived from confirmed evidence |
| REQ-006 | Required Changes 4 | `scripts/mcp_servers/shell/shell_service.py` | Step 3 | AC-4 | `tools/check_adr_reference.py` | Derived from confirmed evidence |
| REQ-007 | Acceptance Criteria 3; Testing Expectations | `tests/tools/test_check_adr_invariant_matrix.py` | Step 2 | AC-5 | `uv run pytest tests/tools -k adr` | Explicit in issue |
| REQ-007 | Acceptance Criteria 3; Testing Expectations | `tests/tools/test_check_adr_reference.py` | Step 3 | AC-5 | `uv run pytest tests/tools -k adr` | Explicit in issue |
| REQ-008 | Required Changes 5; Documentation Impact | `tools/TOOL_DESCRIPTIONS.md` | Step 4 | AC-6 | `tools/check_tool_descriptions_sync.py` | Explicit in issue |
| REQ-008 | Documentation Impact | `docs/00_governance/governance_04_documentation-checks.md` | Step 4 | AC-6 | `tools/check_docs_quality.py` | Explicit in issue |
