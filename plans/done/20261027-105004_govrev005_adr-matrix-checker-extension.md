## Goal
- Extend `tools/check_adr_invariant_matrix.py` so that an empty verification-evidence cell in an ADR body, and a disagreement between an ADR body and the ADR index for the same invariant, are reported, while the existing index-path rule, its JSON output, its exit codes and the names consumed by `.github/run_cited_adr_tests.py` stay unchanged.

## Priority
Medium

## Scope
- **In-Scope**:
  - Rule 1: an ADR body Automated Tests row whose Implementation cell is empty and carries no explicit not-verified marker is reported.
  - Rule 2: for an invariant that appears in both an ADR body and the index matrix, the cited test file paths must agree, otherwise a finding is reported.
  - Severity decision after a corpus survey (warning first), documented in the tool.
  - Tests for the new rules, and updates of the checker docstring, help text and the `tools/TOOL_DESCRIPTIONS.md` entries.
- **Out-of-Scope**:
  - Fixing the empty cells in ADR-001, ADR-002 or ADR-003 (ADR-001 and ADR-002 are in the dependency plan; ADR-003 is untracked).
  - Making the index matrix machine-generated.
  - Running the cited tests to confirm they pass (a documented sub-step of GV-012).
  - Defining the Verification Status vocabulary.
- **Dependencies**: `plans/20261027-104411_govrev003_partial-verification-gate-rules.md` (`depends on`): it defines the not-verified marker used by Rule 1. `plans/20261027-104705_govrev004_adr-verification-evidence-sync.md` (`depends on`): its ADR-001 and ADR-002 cleanup must land before a blocking severity is considered; with warning severity the order only affects the number of findings. Both are implemented first.

## Background
- The checker reads only the index matrix: it extracts backtick-quoted `path::test` references from the matrix rows and reports a missing file as an `ERROR`. It does not read ADR bodies.
- Parsing the `### Automated Tests` tables of all ADR bodies found 13 empty Implementation cells in exactly three ADRs: ADR-001 (5), ADR-002 (2) and ADR-003 (6).
- `report_and_exit` returns exit code 1 only for an `ERROR`, so a `WARNING` finding does not fail pre-commit or CI.
- `.github/run_cited_adr_tests.py` loads the checker by file path and reads the private names `_TEST_PATH_RE` and `ADR_INDEX`. The pre-commit hook `adr-invariant-matrix` runs `python -m tools.check_adr_invariant_matrix`. The test module `tests/tools/test_check_adr_invariant_matrix.py` imports `check_invariant_matrix_test_paths`.
- The index `ADR List` table maps each ADR ID to its file path, which allows an ADR-number to file mapping.

## Problem
The gap that the dependency plan removes for ADR-001 and ADR-002 can reappear unnoticed because no automated check reads the ADR body evidence, and a body and the index can diverge for the same invariant without any signal.

## Reason for Change
Without a guard, the evidence cleanup is a one-time fix. Sequencing matters: enabling a blocking rule before the corpus is clean would fail pre-commit and CI for unrelated changes, so the rules start as warnings.

## Implementation Intent
Add the two rules to the existing checker, keeping its structure and exit-code contract. Resolve the ADR file of an invariant through the index `ADR List` table. Report Rule 1 and Rule 2 as `WARNING` until the corpus is clean, with the promotion condition stated in the tool. Keep `_TEST_PATH_RE`, `ADR_INDEX`, the JSON keys and the existing rule unchanged, and keep the checker read-only.

## Requirements
- `REQ-001`: Report an ADR body Automated Tests row whose Implementation cell is empty and has no explicit not-verified marker defined by the dependency plan, naming the ADR file and the invariant.
- `REQ-002`: For an invariant present in both an ADR body and the index matrix, report a disagreement between the cited test file paths.
- `REQ-003`: Report both rules as `WARNING` severity after the corpus survey, and document in the tool the condition for promoting them to `ERROR`.
- `REQ-004`: Keep the existing rule, the JSON output keys, the exit codes of the existing rule, `_TEST_PATH_RE` and `ADR_INDEX` unchanged, and update the module docstring and help text.
- `REQ-005`: Add tests for an empty cell without a marker, an empty cell with a marker, matching and disagreeing citations, and the first and last rows of a table.
- `REQ-006`: Update the `check_adr_invariant_matrix.py` entries of `tools/TOOL_DESCRIPTIONS.md` and keep `check_tool_descriptions_sync.py` passing.

## Implementation Target Files
**Freeze status**: Frozen (validated by `issue-to-plan` Step 8's
Implementation Target Files Validation — see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/check_adr_invariant_matrix.py` | Matrix checker | Add Rule 1 and Rule 2, severity decision, docstring and help text | REQ-001, REQ-002, REQ-003, REQ-004; AC-1 to AC-4 | Module reads only `ADR_INDEX` through `_matrix_rows` and `check_invariant_matrix_test_paths`; `collect_issues` returns only that rule's issues; `_TEST_PATH_RE` and `ADR_INDEX` are module names (checked in Step 3) | `tests/tools/test_check_adr_invariant_matrix.py` | Verified |
| `tests/tools/test_check_adr_invariant_matrix.py` | Checker tests | Add tests for the new rules | REQ-005; AC-5 | The module has six test classes that call `check_invariant_matrix_test_paths` with a built matrix fixture (checked in Step 3) | `tests/tools/test_check_adr_invariant_matrix.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Tool catalog | Update the two `check_adr_invariant_matrix.py` rows | REQ-006; AC-6 | The catalog lists the tool in its summary table and in its detail table, both describing only the index status column (checked in Step 3) | `tools/check_tool_descriptions_sync.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `.github/run_cited_adr_tests.py` | Consumer of `_TEST_PATH_RE` and `ADR_INDEX`; must keep working | REQ-004 |
| `.pre-commit-config.yaml` | Hook `adr-invariant-matrix` that runs the checker | REQ-004 |
| `tools/_docs_consistency_lib.py` | Defines `Issue` and `report_and_exit` (warning versus error exit code) | REQ-003 |
| `tools/check_tool_descriptions_sync.py` | Validates the catalog update | REQ-006 |
| `docs/10_adr/adr_01_index.md` | Matrix, `ADR List` table (ADR ID to file) and the not-verified marker after the dependency plans | REQ-001, REQ-002 |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Body table that Rule 1 and Rule 2 read | REQ-001, REQ-002 |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Body table that Rule 1 reads | REQ-001 |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Body table with the remaining empty cells | REQ-001, REQ-003 |

## Acceptance Criteria
- AC-1 (REQ-001): The checker reports an empty ADR body Implementation cell that lacks a not-verified marker, and reports nothing for a cell that has the marker or a cited test.
- AC-2 (REQ-002): The checker reports a body/index disagreement of cited test file paths for an invariant present in both, and nothing when they agree.
- AC-3 (REQ-003): Both rules report `WARNING`, the live repository run exits 0, and the tool documents the promotion condition to `ERROR`.
- AC-4 (REQ-004): The existing rule, the JSON keys, the exit code of the existing rule, `_TEST_PATH_RE` and `ADR_INDEX` are unchanged, and `.github/run_cited_adr_tests.py` still loads the module.
- AC-5 (REQ-005): The new tests cover the five cases of REQ-005 and all existing tests still pass.
- AC-6 (REQ-006): `tools/TOOL_DESCRIPTIONS.md` describes the new rules and `check_tool_descriptions_sync.py` passes.

## Tests
- `uv run pytest tests/tools/test_check_adr_invariant_matrix.py -v` (REQ-001 to REQ-005).
- `uv run ruff format tools/check_adr_invariant_matrix.py tests/tools/test_check_adr_invariant_matrix.py` and `uv run ruff check` on both (REQ-004, REQ-005).
- `uv run mypy tools/check_adr_invariant_matrix.py` (path passed explicitly) and `uv run bandit tools/check_adr_invariant_matrix.py` (REQ-004).
- Smoke test on live data: `uv run python tools/check_adr_invariant_matrix.py` and with `--format json` (REQ-003).
- `uv run python .github/run_cited_adr_tests.py --help` or an equivalent import check of the consumer (REQ-004).
- `uv run python tools/check_tool_descriptions_sync.py` (REQ-006) and `uv run pre-commit run adr-invariant-matrix --all-files` (REQ-004).

## Documentation Impact
Yes, limited to `tools/TOOL_DESCRIPTIONS.md` (what the checker verifies and its new rules); REQ-006 drives it. No `docs/*.md` file changes. If the severity stays a warning, the corpus-wide ADR-003 gap is a candidate Known Issue or Accepted Limit entry decided by the repository owner, outside this Plan.

## Assumptions
- The not-verified marker form that Rule 1 accepts is the one defined by the dependency plans (UNK-01).
- Warning severity is the starting point because ADR-003 still has empty cells (UNK-02).
- The ADR file of an invariant can be resolved through the index `ADR List` table, which lists every ADR (UNK-03).
- Step 8b overlap judgments, corrected in `plan-to-implementation-procedure` Step 2: `tools/TOOL_DESCRIPTIONS.md` is also targeted by `plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md`, which was filed later. The two edit different catalog rows (`check_adr_invariant_matrix.py` here, `check_compat_shims.py` there), so they are compatible and only need rebasing in turn. The other two target files overlap no other Frozen Plan.
- Step 3a survey of the live corpus (13 empty cells in ADR-001 (5), ADR-002 (2) and ADR-003 (6) confirmed; the index `ADR List` resolves every ADR ID of the matrix to an existing file, which resolves UNK-03). Comparing cited test file paths per invariant as a union over all body rows, 24 invariants appear in both an ADR body and the index, 11 of them disagree, and for 7 the index cites a path absent from the body. A row-by-row comparison disagrees far more often. Rule 2 therefore compares the union per invariant, parses index rows that name several ADRs or invariants (for example `ADR-002 INV-01, INV-02 and ADR-004 INV-07, INV-10`), and supports the `WARNING` severity of REQ-003: with `ERROR` the live run would fail.
- Marker for Rule 1: `plans/20261027-104705_govrev004_adr-verification-evidence-sync.md` writes the marker as a cell that begins with `Not verified`; Rule 1 accepts a cell whose text begins with `Not verified` (case-insensitive). If the implemented govrev003/govrev004 text differs, match the implemented text (UNK-01).
- The issue file was reverted on disk to its pre-verification text by an external change during this cycle; the verified facts (13 empty cells in three ADRs, the warning exit code, the consumer's private names) are recorded in this Plan's Background, not in the issue.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | What exact marker text records "not verified" in an ADR body Implementation cell? | Defined by the dependency plans, which are not yet implemented | Read the implemented result of `plans/20261027-104411_govrev003_partial-verification-gate-rules.md` and `plans/20261027-104705_govrev004_adr-verification-evidence-sync.md` in Phase 1 and match it | False |
| UNK-02 | Warning or error severity for Rule 1? | No owner decision; ADR-003 still has empty cells | Start with `WARNING`; promote when the corpus survey reports no finding, with the repository owner's approval per the sign-off channel of `rules/coding.md` Explicit sign-off gates | False |
| UNK-03 | Is the index `ADR List` table a reliable ADR-number to file mapping for every ADR? | Only the first rows were read | Check that every `ADR-NNN` in the matrix resolves to an existing file in Phase 1; report an unresolvable ID as a finding | False |
| UNK-04 | Should ADR-003's empty cells be tracked in a separate issue? | Outside the review that produced this Plan | The repository owner decides; this Plan only reports the warnings | False |
| UNK-05 | Implementation order: the dependency plans' Execution Status rows are still `Pending` | Dependencies not yet implemented | Implement the two dependency plans first; the implementation-procedure phase reads this Plan's Scope Dependencies | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/check_adr_invariant_matrix.py` | Modify | Medium | 3 | 2 authors (1y), share not measured | not applicable (rsynced) |
| `tests/tools/test_check_adr_invariant_matrix.py` | Modify | Low | 2 | 1 author (1y), flagged as high | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low | 66 | 2 authors (1y), share not measured | not applicable (rsynced) |

## Design
- Path A: three files; the change is additive, no existing interface changes (the consumed names, JSON keys and exit-code behavior stay), and there is no schema change. The consumer `.github/run_cited_adr_tests.py` and the hook are checked, not modified.
- Validation baseline (this cycle): `radon cc` rates `_matrix_rows` B (10) and every other function A; `vulture scripts/ --min-confidence 80` reports 17 findings in `scripts/`, none in the target files and all unrelated to this change; `bandit` on the tool reports no issue. The diff-cover baseline was not run in planning because a full coverage run is too costly here (`Not available` as evidence); the implementation phase runs it and must reach the threshold of `rules/toolchain.md` Completion checklist.
- Decision: warning severity first, as `report_and_exit` already exits 0 for warnings. Alternative rejected: an immediate `ERROR`, which would fail pre-commit and CI because ADR-003 has six empty cells.
- Decision: resolve the ADR file through the index `ADR List` table rather than a filename pattern, which is stable under renames.
- Blast radius: the checker is referenced by six files; `TOOL_DESCRIPTIONS.md` had 66 commits in 30 days, so its edit is small and rebased carefully.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Confirm preconditions and survey**
   - [ ] Confirm the dependency plans are implemented and read the marker form (UNK-01, UNK-05) (REQ-001; read-only)
   - [ ] Re-run the corpus survey of empty cells and body/index disagreements, and check the ADR List mapping (UNK-02, UNK-03) (REQ-002, REQ-003; read-only)
2. **Phase 2: Implement the rules**
   - [ ] Add Rule 1, Rule 2 and the severity constant, and update the module docstring and help text (REQ-001, REQ-002, REQ-003, REQ-004; `tools/check_adr_invariant_matrix.py`)
3. **Phase 3: Add tests**
   - [ ] Add tests for the five cases of REQ-005 (REQ-005; `tests/tools/test_check_adr_invariant_matrix.py`)
4. **Phase 4: Catalog and verification (no deployment)**
   - [ ] Update the two catalog rows (REQ-006; `tools/TOOL_DESCRIPTIONS.md`)
   - [ ] Run ruff, mypy with an explicit path, bandit, pytest, the live smoke test, the consumer import check, `check_tool_descriptions_sync.py` and the pre-commit hook (REQ-004, REQ-006; the three target files). Files under `tools/` and `tests/` are not deployed, so no deploy step applies.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_adr_invariant_matrix.py` | Unit tests of both rules and of the unchanged rule | `uv run pytest tests/tools/test_check_adr_invariant_matrix.py -v` | All pass |
| `tools/check_adr_invariant_matrix.py` | Lint, types, security | `uv run ruff check`; `uv run mypy tools/check_adr_invariant_matrix.py`; `uv run bandit tools/check_adr_invariant_matrix.py` | No finding |
| `tools/check_adr_invariant_matrix.py` | Live smoke test and JSON output | `uv run python tools/check_adr_invariant_matrix.py`; `--format json` | Exit 0; warnings only for the remaining empty cells |
| `.github/run_cited_adr_tests.py` | Consumer still loads the checker | Import check of the consumer | Loads without error |
| `tools/TOOL_DESCRIPTIONS.md` | Catalog sync | `uv run python tools/check_tool_descriptions_sync.py`; `uv run pre-commit run adr-invariant-matrix --all-files` | Pass |

## Risks
- **Risk**: A blocking severity fails pre-commit and CI for unrelated changes because ADR-003 still has empty cells → **Mitigation**: Start with `WARNING`, promote only after a clean corpus survey and owner approval.
- **Risk**: A change to `_TEST_PATH_RE` or `ADR_INDEX` breaks `.github/run_cited_adr_tests.py` → **Mitigation**: Keep both unchanged and run the consumer import check.
- **Risk**: The ADR-number to file mapping fails for an ADR → **Mitigation**: Check every ADR ID in Phase 1 and report an unresolvable ID as a finding.
- **Risk**: The rules mis-parse a table whose Implementation column differs → **Mitigation**: Parse by header name, skip tables without an Implementation column, and test the first and last rows.
- **Risk**: `TOOL_DESCRIPTIONS.md` is edited by other work (66 commits in 30 days) → **Mitigation**: Make one small commit and re-run the sync check after any sync.
- **Risk**: Implementing before the dependency plans leaves the marker undefined → **Mitigation**: Scope Dependencies and UNK-05 fix the order; Phase 1 confirms it first.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm preconditions and survey the corpus | Pending | — | — | |
| 2 | Implement Rule 1, Rule 2 and the severity decision | Pending | — | — | |
| 3 | Add tests | Pending | — | — | |
| 4 | Update the catalog and run the verification (no deployment) | Pending | — | — | |

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
- **Source issue**: issues/20261027-102002_govrev005_adr-matrix-checker-extension.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261027-105004
- **Related target files**: `tools/check_adr_invariant_matrix.py`, `tests/tools/test_check_adr_invariant_matrix.py`, `tools/TOOL_DESCRIPTIONS.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Implementation Intent; Required Changes (Rule 1) | `tools/check_adr_invariant_matrix.py` | Phase 1, Phase 2 | AC-1 | `uv run pytest tests/tools/test_check_adr_invariant_matrix.py -v` | Confirmed by repository evidence |
| REQ-002 | Implementation Intent; Required Changes (Rule 2) | `tools/check_adr_invariant_matrix.py` | Phase 1, Phase 2 | AC-2 | `uv run pytest tests/tools/test_check_adr_invariant_matrix.py -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes (survey; severity); Unresolved Questions | `tools/check_adr_invariant_matrix.py` | Phase 1, Phase 2 | AC-3 | Live smoke test of the checker | Confirmed by repository evidence |
| REQ-004 | Constraints (do not break the existing rule, JSON, consumer) | `tools/check_adr_invariant_matrix.py` | Phase 2, Phase 4 | AC-4 | Consumer import check; pre-commit hook run | Confirmed by repository evidence |
| REQ-005 | Required Changes (add tests) | `tests/tools/test_check_adr_invariant_matrix.py` | Phase 3 | AC-5 | `uv run pytest tests/tools/test_check_adr_invariant_matrix.py -v` | Explicit in issue |
| REQ-006 | Required Changes (update the descriptions entry) | `tools/TOOL_DESCRIPTIONS.md` | Phase 4 | AC-6 | `uv run python tools/check_tool_descriptions_sync.py` | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261027-112226 -->
