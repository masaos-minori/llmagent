## Goal
- Allow one implementation procedure to carry the test files of its single code row as companion sections, keeping the one-document-per-file rule for everything else, so test changes that follow a code change no longer need a separate low-information document each, while the Plan's `Implementation Target Files` table still lists every file and every row stays covered.

## Priority
Medium

## Scope
- **In-Scope**:
  - A companion section in `templates/implementation-procedure.md`, and the conditions under which a test file may be a companion, in `skills/plan-to-implementation-procedure/SKILL.md` and `workflow.md` (the one-file rule, Step 3c, and the Step 4 coverage and uniqueness checklist).
  - A per-row coverage and uniqueness check for a Plan that counts a companion as covering its row and never double-counts it, as a new opt-in check in `tools/check_workitem_traceability.py`.
  - The tools that assume one file per document and that this Plan found: `tools/check_workitem_traceability.py` (target-file equality), `tools/stale_detector.py` (single target file for `(new)` and line citations), and `tools/generate_workitem.py` (a companion option).
  - `skills/code-implementation/workflow.md`: companions are in the document's scope, are stale-checked with it, and are archived with it.
- **Out-of-Scope**:
  - Merging documents for source files or docs, and any change to Plan Freeze or the table structure.
  - Removing the stale check or the status table from any document.
  - Automatic grouping of rows by `--all-rows` (the generator option is explicit).
- **Dependencies**: Sequencing only, in either order, with `plans/20261102-080336_flowimp002_plan-release-units.md` and `plans/20261102-080513_flowimp007_stale-sibling-new.md`: they also change `templates/implementation-procedure.md`, the two workflows, and (007) `tools/stale_detector.py`; this Plan is created after them so its stale-detector change builds on the sibling resolution, and whichever lands later rebases. It also changes how a procedure lists `Related target files`, which `plans/20261102-080631_flowimp008_workitem-bulk-close.md` reads (Assumption A6). Overlap judgments are in Assumptions A7 to A10.

## Background
- `Operationally observed` (2026-10-30, from the Issue): three Plans produced 59 procedure documents, 24 of them (41%) describing a test file; most restate what the code row's document already says. For `wfrecovery001`, 12 documents were generated after the code and tests were written only so that every Plan row had a document before the move. The counts are from the Issue and were not re-measured here.
- `Explicit in code` (checked in Step 3): `skills/plan-to-implementation-procedure/SKILL.md` Core Execution Rules ("One target file = one procedure document") say a document "MUST NOT contain modification instructions for more than one file". `workflow.md` Step 3c ("each row maps to exactly one document") and the Step 4 pre-move checklist (rows equal rows covered, at most one document per row, "no procedure document modifies more than one file (its `Implementation > Target file` names exactly one path)") state the same rule, and `templates/implementation-procedure.md` states it twice in its own text. The template's "lightweight fill" shortens the body but not the count.
- `Explicit in code` (checked in Step 3): `templates/plan.md` already has a `Related Tests` column per `Implementation Target Files` row, so the pairing of a code row with its tests is recorded in the Plan.
- `Explicit in code` (checked in Step 3): tools that assume one file per document are `tools/check_workitem_traceability.py` (`find_target_file_mismatches` requires the Traceability `Related target files` value to equal the single body `### Target file` value) and `tools/stale_detector.py` (`_TARGET_FILE_SECTION_RE` takes the first backtick path after `### Target file`; line citations and `(new)` marks are scoped to that one file). `tools/audit_plan_target_paths.py` reads Plans only and does not assume one file per document, so it needs no change. `tools/check_workitem_structure.py` checks `## ` headings only.
- `Explicit in code` (checked in Step 3): no tool checks that every `Implementation Target Files` row has a procedure document; the Step 4 coverage check is a manual checklist. The Issue's coverage acceptance criterion therefore needs a new check.
- `Explicit in code` (checked in Step 3): `tools/generate_workitem.py` scaffolds one document per `--target-file-path` and derives the name from that path.
- `Explicit in code` (corrected in plan-to-implementation-procedure Step 3a, 2026-11-02): `tools/check_workitem_traceability.py` `_clean_field_value` keeps only the first whitespace-delimited token of a field value, so `extract_related_target_files_value` already truncates a comma-separated list to its first path. A document listing a target and companions would therefore be compared on its first path alone and a differing tail would go unreported; REQ-003 needs a list-aware reader, not only a changed comparison. The one-file text in `templates/implementation-procedure.md` is in three places (the intro "Exactly one document per `Implementation Target Files` row", the lightweight-fill note "the one-document-per-row invariant is unchanged", and the Notes "Target file" bullet), not two.
- `Explicit in code` (checked in plan-to-implementation-procedure Step 2, 2026-11-02): a repository search for `Related target files` and `### Target file` consumers finds only `tools/check_workitem_traceability.py`, `tools/stale_detector.py`, `tools/generate_workitem.py`, the one-off generators `tools/gen_wf*_procedures.py` (they write documents, not read them), and `tools/mark_procedure_new_symbols.py` (calls `stale_detector.py`; covered by the Phase 3 consumer regression run). `tools/TOOL_DESCRIPTIONS.md` rows for the three changed tools describe their behavior and options but `TOOL_DESCRIPTIONS.md` is not a row of this Plan (UNK-03).

## Problem
The one-file-per-document rule is correct for review scope and rollback, but for test files that exist only to prove a code row it multiplies documents, status tables, and archive steps without adding independent decisions.

## Reason for Change
Test rows are about two out of five documents in a typical persisted-schema Plan. Each carries a full structure, a stale check, a status table, and an archive step, and the retroactive ones show the structure being filled for the checker rather than for the reader.

## Implementation Intent
Keep the file-level scope boundary but declare it per document rather than per file: a procedure for a code row may list companion test files (rows of the same Plan whose `Related Tests` ties them to that code row) with their own short procedure and validation lines. The Plan table is unchanged; the document's `Related target files` lists every covered file; the coverage check counts a row as covered when its file appears as a target or companion. A test file tied to more than one code row, or needing its own design decisions, keeps a separate document. `code-implementation` treats companions as in scope of that document and archives it once.

## Requirements
- `REQ-001`: `templates/implementation-procedure.md`, `skills/plan-to-implementation-procedure/SKILL.md`, and `skills/plan-to-implementation-procedure/workflow.md` MUST define the companion section and the conditions (a test file of the same Plan, tied to exactly one code row by its `Related Tests` entry), and MUST keep the one-file rule for source files, docs, config, and standalone test files.
- `REQ-002`: A per-row coverage and uniqueness check MUST count a row as covered when its file is a target or a companion of a document of that Plan, MUST fail when a row is uncovered, and MUST reject a companion that is also a target or a companion of another document or is tied to two code rows; it MUST be opt-in so the existing pre-commit hook behavior is unchanged.
- `REQ-003`: `tools/check_workitem_traceability.py` MUST accept a document whose `Related target files` lists the target and its companions, and MUST still report a mismatch when the list differs from the body's target and companions.
- `REQ-004`: `tools/stale_detector.py` MUST check companions with the document: `(new)` marks and line citations scoped to a companion file resolve against that companion, and a document without companions behaves exactly as before.
- `REQ-005`: `tools/generate_workitem.py` MUST offer a companion option that scaffolds a document listing the target and its companions with their own procedure and validation lines.
- `REQ-006`: `skills/code-implementation/workflow.md` MUST state that companions are in the document's scope, are stale-checked with it, and are archived with it, including the Step 7 Plan update that matches procedures to rows.

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8b, 2026-11-02; all rows `Verified`)

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `skills/plan-to-implementation-procedure/SKILL.md` | Exception to the one-file rule | Core Execution Rules forbid more than one file per document | REQ-001 / AC-1 | "One target file = one procedure document" rule (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |
| `skills/plan-to-implementation-procedure/workflow.md` | Companion conditions, Step 3c, Step 4 coverage and uniqueness checklist | Step 3c and the Step 4 checklist assume exactly one file and one document per row | REQ-001, REQ-002 / AC-1, AC-2 | Step 3c "exactly one document"; Step 4 pre-move checklist (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |
| `templates/implementation-procedure.md` | Companion section; adjust the two one-file statements | The template states one document per file in its own text | REQ-001, REQ-005 / AC-1 | one-file statements near the top and in the Implementation notes (checked in Step 3) | `check_workitem_structure.py` on a fixture procedure | Verified |
| `skills/code-implementation/workflow.md` | Companions in scope, stale check, archive, Step 7 mapping | The workflow assumes one target file per document | REQ-006 / AC-5 | Step 2 stale detection, Step 3d, Step 7 "Plan Execution Status update" (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |
| `tools/check_workitem_traceability.py` | Accept companions in the equality check; add the opt-in coverage and uniqueness check | `find_target_file_mismatches` requires equality with one path; no coverage tool exists | REQ-002, REQ-003 / AC-2, AC-3 | `find_target_file_mismatches`, `extract_related_target_files_value`, `extract_target_file_value`, `find_no_procedure_yet` (checked in Step 3) | `tests/tools/test_check_workitem_traceability.py` | Verified |
| `tests/tools/test_check_workitem_traceability.py` | Tests for companions and the coverage check | Existing tests cover single-target documents | REQ-002, REQ-003 / AC-2, AC-3 | existing test module (checked in Step 3) | itself | Verified |
| `tools/stale_detector.py` | Scope `(new)` and line citations per companion | `_TARGET_FILE_SECTION_RE` and `from_procedure` use the first path only | REQ-004 / AC-4 | `_TARGET_FILE_SECTION_RE`, `StaleResult.from_procedure` (checked in Step 3) | `tests/tools/test_stale_detector.py` | Verified |
| `tests/tools/test_stale_detector.py` | Tests for companion documents | Existing tests cover single-target documents | REQ-004 / AC-4 | existing test module (checked in Step 3) | itself | Verified |
| `tools/generate_workitem.py` | Companion option for the procedure kind | The generator scaffolds one document per `--target-file-path` | REQ-005 / AC-6 | `render_implementation_procedure`, `generate_all_rows`, `--target-file-path` (checked in Step 3) | `tests/tools/test_generate_workitem.py` | Verified |
| `tests/tools/test_generate_workitem.py` | Tests for the companion option | Existing tests cover single-target scaffolds | REQ-005 / AC-6 | existing test module (checked in Step 3) | itself | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/audit_plan_target_paths.py` | Confirms it reads Plans only and needs no change | REQ-002 |
| `tools/check_workitem_structure.py` | Confirms it checks `## ` headings only, so a companion `###` section needs no change | REQ-001 |
| `tools/manage_workitem_stage.py` | Status and archival tools read the Execution Status table, not the target file; confirms no change is needed | REQ-006 |
| `templates/plan.md` | `Related Tests` column that ties a test file to a code row | REQ-001, REQ-002 |
| `templates/traceability.md` | `Related target files` field the companion list extends | REQ-003 |
| `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md` | Archived Plan used for the before and after document-count walk-through | REQ-001, REQ-002 |
| `rules/workflow-lifecycle.md` | Plan Freeze and additional-target-file rules that the exception must not weaken | REQ-001 |

## Acceptance Criteria
- AC-1 (`REQ-001`): The template and the two skill files define the companion section and its conditions, keep the one-file rule for non-test files, and `check_skills_references.py` and `check_skills_heading_cycles.py` pass.
- AC-2 (`REQ-002`): On a fixture Plan with a code row and two test rows, one document listing the code file as target and the two test files as companions passes the coverage check; removing a companion makes it fail; a test file tied to two code rows, or listed by two documents, is rejected.
- AC-3 (`REQ-003`): The traceability checker passes a document whose `Related target files` lists the target and companions and still reports a differing list.
- AC-4 (`REQ-004`): `tools/stale_detector.py` checks a document with companions, resolving `(new)` marks and line citations per companion, and a document without companions produces the same output as before.
- AC-5 (`REQ-006`): `skills/code-implementation/workflow.md` states the companion scope, stale check, and archival, and the Step 7 mapping counts a companion's archive.
- AC-6 (`REQ-005`): The generator scaffolds a document with a target and companions, and the existing single-target scaffold is unchanged.
- AC-7 (`REQ-001`, `REQ-002`): Re-deriving the three archived Plans' document counts under the rule is recorded in the implementing change (expected: the count of test documents falls to those needing their own).

## Tests
- `REQ-002`: unit tests for covered, missing, duplicate, and multi-row companion cases in the coverage check.
- `REQ-003`: tests for the equality check with and without companions.
- `REQ-004`: tests for companion `(new)` marks, companion line citations, and a no-companion regression.
- `REQ-005`: tests for the companion option and the unchanged single-target scaffold.
- `REQ-001`, `REQ-006`: skill checkers; a walk-through on the archived `wftaskapi001` Plan comparing the document set before and after.

## Documentation Impact
- Yes. The skill, workflow, and template state the exception, its conditions, and how coverage is counted (REQ-001, REQ-006). No `docs/*.md` change: workflow rules and tooling.

## Assumptions
- A1: A test file's tie to its code row can be read from the Plan's `Related Tests` column (from the Issue). Falsifiable by a Plan whose `Related Tests` cells are prose rather than paths.
- A2: Decision: the companion section is a `### Companion test files` heading under `## Implementation` in the procedure template, so `check_workitem_structure.py` (`## ` headings only) and `check_metadata_field_policy.py` (top-level sections only) are unaffected. Falsifiable by those checkers reporting the new heading.
- A3: Decision: the coverage and uniqueness check is a new opt-in mode of `tools/check_workitem_traceability.py` that takes a Plan path; it is not part of the default scan or of the pre-commit hook, because a Plan mid-batch legitimately has uncovered rows. Falsifiable by the owner wanting it in the hook.
- A4: The owner accepts a narrow exception to the one-file rule for test files of a single code row (the Issue assumes the rule exists for review scope and rollback, not as an end in itself). Falsifiable by the owner declining; then this Plan is not implemented.
- A5: `Related target files` for a document with companions is a comma-separated list with the primary target first; the body's `### Target file` names the primary and the companion section names the rest.
- A6: `plans/20261102-080631_flowimp008_workitem-bulk-close.md` matches procedures to Plan files through `Related target files`; its tool MUST read that value as a list. This Plan records the requirement; no edit to that Plan's target files is made here, and the check is part of this Plan's walk-through.
- A7: Overlap judgment (Step 8b): `templates/implementation-procedure.md` is also a target of `plans/20261102-080336_flowimp002_plan-release-units.md` and `plans/20261102-080513_flowimp007_stale-sibling-new.md`. Judged compatible: those Plans edit the `## Scope` block and the `(new)` notes; this Plan edits the one-file statements and adds the companion section.
- A8: Overlap judgment (Step 8b): `skills/plan-to-implementation-procedure/workflow.md` and `skills/code-implementation/workflow.md` are also targets of Plans 002, 003, 007, and 008. Judged compatible: this Plan edits Step 3c, the Step 4 checklist, Step 2 and Step 7 text on target files; the others edit unit, gated, stale-note, and close-command text in different steps.
- A9: Overlap judgment (Step 8b): `tools/stale_detector.py` and `tests/tools/test_stale_detector.py` are also targets of `plans/20261102-080513_flowimp007_stale-sibling-new.md`. Judged a sequencing dependency: that Plan adds sibling resolution after the per-document checks; this Plan changes how the document's own target and companions are read first; whichever lands second rebases.
- A10: `git-fame` is not used; Bus Factor is `N/A` (single-owner repository).
- A11: Overlap judgment (plan-to-implementation-procedure Step 2, 2026-11-02): `skills/plan-to-implementation-procedure/workflow.md` and `skills/code-implementation/workflow.md` are also targets of `plans/20261102-081027_flowimp011_plan-amend-tool.md` (not recorded in A8). Judged a sequencing dependency, compatible in content: that Plan rewrites the Step 3c additional-target-file-discovery bullet and adds a stop rule in `code-implementation`; this Plan edits the Step 3c one-document and classification bullets, the Step 4 checklist, and the scope and Step 7 mapping text. Whichever lands later rebases. Plans 002, 003, and 007 named in A7 to A9 now have procedures (`implementations/20261102-085047_*`, `-085056_*`, `-085029_*`) and are archived; their code has not landed, so the same rebase rule applies. Plan 008 (A6, A8) also rewrites the Step 7 Plan update in `code-implementation`; judged a sequencing dependency: this Plan's Step 7 text is the companion rule for the file-to-row mapping that the 008 command documents.
- A12: The Step 3a finding on `_clean_field_value` (Background) means the new list reader in `tools/check_workitem_traceability.py` parses `Related target files` as a comma-separated list of backticked or bare paths, keeping the existing first-token behavior for every caller that does not ask for the list. Falsifiable by a caller that needs the list through `extract_related_target_files_value` itself.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which tools beyond the ones found here assume one file per document | A full search was bounded to `tools/`, `skills/`, and `templates/` | Re-run the search at implementation start (`rg` for `Target file` and `Related target files` consumers) and report any further consumer as an additional target file discovery | False |
| UNK-02 | Whether the owner accepts the exception to the one-file rule | The Issue assumes it; no owner statement exists | Treated as Assumption A4; confirmed when the owner approves this Plan | False |
| UNK-03 | Whether `tools/TOOL_DESCRIPTIONS.md` (rows for `check_workitem_traceability.py`, `stale_detector.py`, `generate_workitem.py`, which document options and finding types) must describe the coverage mode, companion scoping, and `--companion` | The Plan's table has no `tools/TOOL_DESCRIPTIONS.md` row; sibling Plans 003 and 007 list it for option changes, and `check_tool_descriptions_sync.py` checks only the file list | Raised in plan-to-implementation-procedure Step 3a: if the owner wants the descriptions updated, append a `tools/TOOL_DESCRIPTIONS.md` row (a new `seq` after the last row) before `code-implementation` runs Phase 2 to 4; until then it is out of scope | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `skills/plan-to-implementation-procedure/SKILL.md` | Modify | Medium | 6 | N/A | not applicable (rsynced) |
| `skills/plan-to-implementation-procedure/workflow.md` | Modify | Medium | 8 | N/A | not applicable (rsynced) |
| `templates/implementation-procedure.md` | Modify | Medium (every procedure follows it; the generator copies it) | 4 | N/A | not applicable (rsynced) |
| `skills/code-implementation/workflow.md` | Modify | High (executes every procedure) | 13 | N/A | not applicable (rsynced) |
| `tools/check_workitem_traceability.py` | Modify | Medium (pre-commit hook) | 6 | N/A | not applicable (rsynced) |
| `tests/tools/test_check_workitem_traceability.py` | Modify | Low | 3 | N/A | not applicable (rsynced) |
| `tools/stale_detector.py` | Modify | Medium (run in every generation and execution) | 4 | N/A | not applicable (rsynced) |
| `tests/tools/test_stale_detector.py` | Modify | Low | 5 | N/A | not applicable (rsynced) |
| `tools/generate_workitem.py` | Modify | Medium (scaffolds every work item) | 2 | N/A | not applicable (rsynced) |
| `tests/tools/test_generate_workitem.py` | Modify | Low | 2 | N/A | not applicable (rsynced) |

## Design
- Companion eligibility: a test path (under `tests/`) that is a row of the same Plan, appears in the `Related Tests` cell of exactly one code row, and needs no design decision of its own. A test file tied to more than one code row, or needing its own decisions, keeps a separate document.
- Document shape: `### Target file` names the code file; a new `### Companion test files` section lists each companion with a short procedure line and a validation line, using `(new)` for a companion that does not exist yet. The Traceability `Related target files` lists the target first and then each companion.
- Coverage and uniqueness check: `tools/check_workitem_traceability.py` gains an opt-in mode taking a Plan path. It reads the Plan's `Implementation Target Files` rows and the documents (`implementations/` and `implementations/done/`) whose `Source plan` is that Plan, collects each document's target and companions, and reports uncovered rows, a path covered twice, and a companion tied to more than one code row. Report-only by default, like the other categories.
- Equality check: `find_target_file_mismatches` compares `Related target files` with the set of the body's target and companions, so a document without companions behaves as before.
- Stale detection: `StaleResult.from_procedure` reads the target and the companions; a `(new)` mark after a companion path declares that companion created; line citations scoped to a companion path resolve against that file; the single-target path is unchanged.
- Generator: an explicit `--companion {path}` option (repeatable) with `--target-file-path`; `--all-rows` is unchanged (out of scope).
- `code-implementation`: companions are in the document's scope for the working-tree baseline check, stale check, and Step 7 archival; the Step 7 Plan update treats a companion's archive as covering its row.
- Alternatives rejected: a Plan table change (forbidden by the Issue); hook-level coverage enforcement (A3).
- Compatibility: Plan Freeze rules and the Plan table are untouched; single-file documents are unchanged.

## Implementation steps
1. **Phase 1: Rule and template**
   - [ ] Add the exception and conditions to the Core Execution Rules (`REQ-001`; `skills/plan-to-implementation-procedure/SKILL.md`)
   - [ ] Update Step 3c and the Step 4 coverage and uniqueness checklist (`REQ-001`, `REQ-002`; `skills/plan-to-implementation-procedure/workflow.md`)
   - [ ] Add the companion section and adjust the one-file statements (`REQ-001`; `templates/implementation-procedure.md`)
2. **Phase 2: Traceability and coverage check**
   - [ ] Accept companions in the equality check and add the opt-in coverage and uniqueness mode (`REQ-002`, `REQ-003`; `tools/check_workitem_traceability.py`)
   - [ ] Add tests for covered, missing, duplicate, and multi-row companion cases (`REQ-002`, `REQ-003`; `tests/tools/test_check_workitem_traceability.py`)
3. **Phase 3: Stale detector**
   - [ ] Read companions and scope `(new)` marks and line citations per companion (`REQ-004`; `tools/stale_detector.py`)
   - [ ] Add companion and no-companion regression tests (`REQ-004`; `tests/tools/test_stale_detector.py`)
4. **Phase 4: Generator**
   - [ ] Add the `--companion` option (`REQ-005`; `tools/generate_workitem.py`)
   - [ ] Add tests for the option and the unchanged single-target scaffold (`REQ-005`; `tests/tools/test_generate_workitem.py`)
5. **Phase 5: Execution workflow**
   - [ ] State companion scope, stale check, archival, and the Step 7 mapping (`REQ-006`; `skills/code-implementation/workflow.md`)
6. **Phase 6: Verification** (no `scripts/` or `config/` change, so no deploy step is required)
   - [ ] Run the tool lint sequence on the four changed tools, the walk-through on the archived `wftaskapi001` Plan, and the checkers in the Validation plan (`REQ-001` to `REQ-006`; all rows)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_workitem_traceability.py` | Unit | `uv run pytest tests/tools/test_check_workitem_traceability.py -v` | all pass |
| `tools/stale_detector.py` | Unit and consumer regression | `uv run pytest tests/tools/test_stale_detector.py tests/tools/test_mark_procedure_new_symbols.py -v` | all pass |
| `tools/generate_workitem.py` | Unit | `uv run pytest tests/tools/test_generate_workitem.py -v` | all pass |
| The four changed tools | Lint, type, security | `uv run ruff format <file>`; `uv run ruff check <file>`; `uv run mypy <file>`; `uv run bandit <file>` per file | clean |
| Skills and template | Reference, heading, and structure checks | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py`; `uv run python tools/check_workitem_structure.py --file <fixture>` | no findings |
| Archived `wftaskapi001` Plan | Walk-through (AC-7) | derive the document set under the rule and compare counts | recorded in the implementing change |

## Risks
- **Risk**: A companion hides a change that needs independent review or rollback. → **Mitigation**: eligibility is limited to test files tied to one code row; companions are listed in the document's target section; a multi-row test file keeps its own document.
- **Risk**: Another consumer of one-file documents breaks. → **Mitigation**: UNK-01 re-runs the search at implementation start; any further consumer is reported as an additional target file discovery.
- **Risk**: The change to `tools/check_workitem_traceability.py` makes the pre-commit hook report false mismatches. → **Mitigation**: the equality check is extended, not relaxed (a list that differs from target plus companions still fails), and the coverage mode is opt-in (A3).
- **Risk**: `tools/stale_detector.py` is changed by two Plans. → **Mitigation**: A9 records the sequencing dependency; the later Plan rebases; consumer tests run in Phase 3.
- **Risk**: The Plan 008 batch-close tool misreads a multi-path `Related target files`. → **Mitigation**: A6 records the requirement; the walk-through checks it.
- **Risk**: Shared skills and templates are edited by several Plans. → **Mitigation**: A7 and A8 record that the edits target different steps and sections.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see `templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rule and template: `skills/plan-to-implementation-procedure/SKILL.md`, `skills/plan-to-implementation-procedure/workflow.md`, `templates/implementation-procedure.md` | Completed | — | 20261102-133710 |  |
| 2 | Traceability and coverage check: `tools/check_workitem_traceability.py`, `tests/tools/test_check_workitem_traceability.py` | Completed | — | 20261102-133948 |  |
| 3 | Stale detector: `tools/stale_detector.py`, `tests/tools/test_stale_detector.py` | Completed | — | 20261102-134150 |  |
| 4 | Generator: `tools/generate_workitem.py`, `tests/tools/test_generate_workitem.py` | Completed | — | 20261102-134321 |  |
| 5 | Execution workflow: `skills/code-implementation/workflow.md` | Completed | — | 20261102-133730 |  |
| 6 | Verification: lint sequence, walk-through, checkers | Completed | — | 20261102-135347 | Lint/type/security clean on 3 tools and 3 test files; skills checkers clean; plan-end full suite 11180 passed, 1 known pre-existing failure (mdq bind gate, /opt/llm/docs); diff-cover N/A (no scripts/ change). AC-7 walk-through with --plan-coverage logic over current Related Tests cells: wftaskapi001 12 rows -> 10 docs (2 companions), wfrecovery001 26 -> 20 (6), dbmig001 23 -> 20 (3); older Plans mostly name tests in prose so only backticked-path ties qualify. TOOL_DESCRIPTIONS rows not updated (UNK-03). |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261102-085649_01_skills_plan-to-implementation-procedure_SKILL.md.md | 1 | Procedure | Completed | — | — |
| implementations/20261102-085649_02_skills_plan-to-implementation-procedure_workflow.md.md | 1 | Procedure | Completed | — | — |
| implementations/20261102-085649_03_templates_implementation-procedure.md.md | 1 | Procedure | Completed | — | — |
| implementations/20261102-085649_04_skills_code-implementation_workflow.md.md | 5 | Procedure | Completed | — | — |
| implementations/20261102-085649_05_tools_check_workitem_traceability.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261102-085649_06_tests_tools_test_check_workitem_traceability.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261102-085649_07_tools_stale_detector.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261102-085649_08_tests_tools_test_stale_detector.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261102-085649_09_tools_generate_workitem.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261102-085649_10_tests_tools_test_generate_workitem.py.md | 4 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261030-191615_flowimp009_test-row-grouping.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261102-080828
- **Related target files**: `skills/plan-to-implementation-procedure/SKILL.md`, `skills/plan-to-implementation-procedure/workflow.md`, `templates/implementation-procedure.md`, `skills/code-implementation/workflow.md`, `tools/check_workitem_traceability.py`, `tests/tools/test_check_workitem_traceability.py`, `tools/stale_detector.py`, `tests/tools/test_stale_detector.py`, `tools/generate_workitem.py`, `tests/tools/test_generate_workitem.py` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (define the companion section and conditions); Background (one-file rule) | `skills/plan-to-implementation-procedure/SKILL.md` | Phase 1 | AC-1 | reference and heading checkers | Confirmed by repository evidence |
| REQ-001 | Required Changes; Step 3 (Step 3c and Step 4 text) | `skills/plan-to-implementation-procedure/workflow.md` | Phase 1 | AC-1 | reference and heading checkers | Confirmed by repository evidence |
| REQ-001 | Target Files (template companion section) | `templates/implementation-procedure.md` | Phase 1 | AC-1 | `check_workitem_structure.py` | Explicit in issue |
| REQ-002 | Required Changes (coverage and uniqueness checks); Step 3 (no coverage tool exists) | `tools/check_workitem_traceability.py` | Phase 2 | AC-2 | coverage unit tests | Derived from confirmed evidence |
| REQ-002 | Testing Expectations (covered, missing, duplicate, multi-row companion) | `tests/tools/test_check_workitem_traceability.py` | Phase 2 | AC-2 | coverage unit tests | Explicit in issue |
| REQ-003 | Required Changes (traceability tool on companion documents); Step 3 (`find_target_file_mismatches`) | `tools/check_workitem_traceability.py` | Phase 2 | AC-3 | equality tests | Confirmed by repository evidence |
| REQ-003 | Testing Expectations | `tests/tools/test_check_workitem_traceability.py` | Phase 2 | AC-3 | equality tests | Explicit in issue |
| REQ-004 | Acceptance Criteria (stale detector handles companions); Step 3 (`_TARGET_FILE_SECTION_RE`) | `tools/stale_detector.py` | Phase 3 | AC-4 | companion stale tests | Confirmed by repository evidence |
| REQ-004 | Acceptance Criteria | `tests/tools/test_stale_detector.py` | Phase 3 | AC-4 | companion stale tests | Explicit in issue |
| REQ-005 | Required Changes (generator companion option) | `tools/generate_workitem.py` | Phase 4 | AC-6 | generator tests | Explicit in issue |
| REQ-005 | Testing Expectations (generator option tests) | `tests/tools/test_generate_workitem.py` | Phase 4 | AC-6 | generator tests | Explicit in issue |
| REQ-006 | Required Changes (state companion scope in `code-implementation`) | `skills/code-implementation/workflow.md` | Phase 5 | AC-5 | reference and heading checkers | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261102-085649 -->