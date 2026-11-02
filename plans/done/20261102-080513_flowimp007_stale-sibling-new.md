## Goal
- Teach `tools/stale_detector.py` to treat a name as declared when an earlier sibling procedure of the same Plan marks it `(new)`, and to report where it was declared, so false "stale" findings and the boilerplate Assumptions sentence disappear while unmarked missing names stay stale.

## Priority
Medium

## Scope
- **In-Scope**:
  - Sibling resolution in `tools/stale_detector.py`, keyed on the procedure's Traceability `Source plan`, over `implementations/` and `implementations/done/`, with an option to disable it and an informational output line per name resolved from a sibling.
  - An order rule: only an earlier sibling's declaration counts (earlier by the `seq` in the sibling's file name), reported in the output, with an option to accept any sibling.
  - Simplifying the two skill texts and the template note so the boilerplate Assumptions sentence is no longer required when the detector reports the declaration.
  - Registering the changed behavior in `tools/TOOL_DESCRIPTIONS.md`.
- **Out-of-Scope**:
  - Changing how `(new)` is written or how target files are declared.
  - Checking that a declared name is actually created when the sibling runs.
  - Generating the procedures themselves, and the one-off marking scripts under `tools/` that consume the detector.
- **Dependencies**: Sequencing only. The Issue linked the order rule to the Plan phase order view of `plans/20261102-080134_flowimp003_plan-dependency-gate.md`; this Plan removes that dependency by using the `seq` order, which `skills/plan-to-implementation-procedure/workflow.md` Step 3c item (2) and `skills/code-implementation/workflow.md` Multi-file processing already define as the Plan's implementation order (Assumption A2). If that Plan's order view lands first, it MAY later replace the `seq` source in a separate change. Overlap judgments are in Assumptions A5 to A7.

## Background
- `Explicit in code` (checked in Step 3): `tools/stale_detector.py` decides per document. `_check_symbol_refs` reports `symbol_missing` and `_check_import_refs` reports import mismatches; a name or import written followed by `(new)` is declared and skipped (`_is_marked_new`). A name created by another procedure is reported.
- `Explicit in code` (checked in Step 3): `skills/plan-to-implementation-procedure/workflow.md` Step 3c item (2) prescribes the workaround: a name that only an earlier-`seq` row's procedure creates is acceptable and is noted in the document's Assumptions. `skills/code-implementation/workflow.md` Step 2 aborts the cycle on any detector mismatch, so the note cannot be skipped.
- `Explicit in code` (checked in Step 3): `StaleResult` has `is_stale`, `target_file`, and `mismatches`; `is_stale` drives `abort_execution`. Importers of the detector are `tools/mark_procedure_new_symbols.py`, `tools/mark_new_112317.py`, `tools/mark_new_115752.py`, `tools/fix_procedure_new_markers.py`, and `tests/tools/test_stale_detector.py`, `tests/tools/test_mark_procedure_new_symbols.py`; the one-off marking scripts are themselves workarounds for the same problem.
- Verified in Step 2 (2026-11-02): the Issue reports 28 archived procedure documents carrying the boilerplate sentence. A search of `implementations/done/` for the quoted wording finds none, so the count and the exact wording are `Needs confirmation`; the baseline MUST be re-measured at implementation by running the detector over the archived procedures of the three Plans and counting documents with mismatches that a sibling declaration would resolve.
- `Explicit in code` (checked in Step 3): `templates/implementation-procedure.md` Notes already describe `(new)` for names, imports, and target files.
- `Operationally observed` (2026-10-30, from the Issue): a later row routinely uses names that an earlier row creates; up to 12 flagged names appeared in a single document.

## Problem
The detector cannot tell "this name does not exist and nobody will create it" from "an earlier procedure of this Plan creates it before this one runs". Authors compensate with boilerplate that carries no checkable claim, and a real stale reference hidden among the flagged names is easy to miss.

## Reason for Change
Plans with many rows are the normal case for schema and API work. The boilerplate grows with Plan size, and the cost is paid again in `code-implementation` Step 2 when the same findings are read at execution time.

## Implementation Intent
Resolve names across the procedures of one Plan. The detector reads the procedure's `Source plan`, finds sibling procedures citing the same Plan, and treats a name marked `(new)` in an earlier sibling as declared there. Such a name is reported as an informational line naming the declaring document and is not a mismatch. A name declared nowhere, or only by a later sibling, stays stale with the reason.

## Requirements
- `REQ-001`: The detector MUST resolve a flagged name or import against `(new)` declarations in sibling procedures that cite the same `Source plan`, MUST print one informational line per resolved name naming the declaring document, and MUST NOT count a resolved name as a mismatch; an option MUST disable the resolution.
- `REQ-002`: The detector MUST apply an order rule: by default only a sibling with an earlier `seq` counts; a name declared only by a later sibling MUST be reported stale with that reason; an option MUST accept any sibling; the active rule MUST be printed in the output.
- `REQ-003`: A name declared by no document MUST remain a mismatch, a document without a `Source plan` or without siblings MUST behave exactly as before, and a sibling that cannot be read MUST be reported without failing the run.
- `REQ-004`: `skills/plan-to-implementation-procedure/workflow.md` Step 3c item (2), `skills/code-implementation/workflow.md` Step 2, and `templates/implementation-procedure.md` MUST state that sibling declarations are resolved and reported by the tool and no longer need a manual Assumptions note.
- `REQ-005`: `tools/TOOL_DESCRIPTIONS.md` MUST describe the sibling resolution and its options.

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8b, 2026-11-02; all rows `Verified`)

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/stale_detector.py` | Sibling resolution, order rule, options, informational output | Detection is per document; `StaleResult.from_procedure`, `_check_symbol_refs`, `_check_import_refs`, and `_is_marked_new` have no sibling logic | REQ-001, REQ-002, REQ-003 / AC-1, AC-2, AC-3 | `StaleResult`, `from_procedure`, `_check_symbol_refs`, `_check_import_refs`, `main` (checked in Step 3) | `tests/tools/test_stale_detector.py` | Verified |
| `tests/tools/test_stale_detector.py` | Tests for sibling cases | Existing tests cover single-document behavior | REQ-001, REQ-002, REQ-003 / AC-1, AC-2, AC-3 | existing test module (checked in Step 3) | itself | Verified |
| `skills/plan-to-implementation-procedure/workflow.md` | Simplify Step 3c item (2) | Item (2) requires a manual Assumptions note | REQ-004 / AC-5 | "Step 3c" text on `stale_detector.py` mismatches (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |
| `skills/code-implementation/workflow.md` | Step 2 result handling | Step 2 aborts on any mismatch and does not mention informational lines | REQ-004 / AC-5 | "Pre-execution stale detection (part of Step 2)" (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |
| `templates/implementation-procedure.md` | Note on sibling-declared names | The `(new)` notes cover only names created by the document itself | REQ-004 / AC-5 | Notes on `(new)` (checked in Step 3) | `check_workitem_structure.py` on a fixture procedure | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Update the `stale_detector.py` entry | The entry does not describe sibling resolution | REQ-005 / AC-4 | `stale_detector.py` row (checked in Step 3) | `tools/check_tool_descriptions_sync.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/mark_procedure_new_symbols.py` | Consumes the detector result; the result type must stay compatible | REQ-003 |
| `tests/tools/test_mark_procedure_new_symbols.py` | Pins the consumer behavior | REQ-003 |
| `tools/fix_procedure_new_markers.py` | Another consumer of detector output | REQ-003 |
| `templates/traceability.md` | `Source plan` is a required procedure field | REQ-001 |
| `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md` | Archived Plan whose procedures form one baseline set | REQ-001, REQ-002 |
| `plans/done/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` | Archived Plan whose procedures form one baseline set | REQ-001, REQ-002 |
| `plans/done/20261029-214108_dbmig001_forward-only-db-migrations.md` | Archived Plan whose procedures form one baseline set | REQ-001, REQ-002 |

## Acceptance Criteria
- AC-1 (`REQ-001`): On fixture procedures where document B uses a name that document A marks `(new)`, the detector reports B as not stale, names A as the declaring document, and prints the informational line; a name marked nowhere is still reported stale.
- AC-2 (`REQ-002`): With the default order rule, a name declared only by a later sibling is reported stale with the reason; with the accept-any option it is resolved; the active rule is printed.
- AC-3 (`REQ-003`): A document without a `Source plan` or without siblings behaves exactly as before; an unreadable sibling is reported without failing the run; a cycle of declarations (A uses a name B declares and B uses a name A declares) is resolved only in the earlier-to-later direction.
- AC-4 (`REQ-005`): `check_tool_descriptions_sync.py` passes with the updated entry.
- AC-5 (`REQ-004`): The two skills and the template state the new behavior; `check_skills_references.py` and `check_skills_heading_cycles.py` pass.
- AC-6 (`REQ-001`): The detector is run over the archived procedures of `dbmig001`, `wftaskapi001`, and `wfrecovery001` before and after, and the count of documents with sibling-resolvable mismatches is recorded in the implementing change (the baseline replaces the unreproducible "28" count).

## Tests
- `REQ-001`, `REQ-002`, `REQ-003`: unit tests for resolved name, unresolved name, later-sibling-only, accept-any option, disable option, no `Source plan`, no siblings, unreadable sibling, declaration cycle, and archived sibling.
- `REQ-003`: the existing `tests/tools/test_mark_procedure_new_symbols.py` and `tests/tools/test_stale_detector.py` suites run unchanged.
- `REQ-001`: a before and after run over the three archived procedure sets.

## Documentation Impact
- Yes. The two skills and the template state that sibling declarations are resolved by the tool and no longer need a manual note (REQ-004); `tools/TOOL_DESCRIPTIONS.md` describes the options (REQ-005). No `docs/*.md` change: workflow tooling.

## Assumptions
- A1: `Source plan` is present and accurate in every generated procedure (a required template field, `templates/traceability.md`). Siblings are matched by the Plan file name (basename), so a Plan moved to `plans/done/` after generation still matches its siblings. Falsifiable by procedures whose `Source plan` basename differs.
- A2: Decision: the order source is the `seq` in the sibling's file name `{timestamp}_{seq}_{slug}.md`, because `skills/plan-to-implementation-procedure/workflow.md` Step 3c item (2) and `skills/code-implementation/workflow.md` Multi-file processing define `seq` order as the Plan's implementation order. The Plan phase order is not used in this version (the Issue linked it to a sibling Plan's order view). Falsifiable by a Plan whose phase order differs from `seq`.
- A3: A sibling archived as `Blocked` still has its declarations counted (from the Issue); the tool does not read statuses.
- A4: `git-fame` is not used; Bus Factor is `N/A` (single-owner repository).
- A5: Overlap judgment (Step 8b): `skills/plan-to-implementation-procedure/workflow.md` and `skills/code-implementation/workflow.md` are also targets of `plans/20261102-080134_flowimp003_plan-dependency-gate.md` and `plans/20261102-080336_flowimp002_plan-release-units.md`. Judged compatible: this Plan edits Step 3c item (2) and the Step 2 stale-detection paragraph; the others edit Step 1, Step 2 start conditions, Step 4, Step 7, and Multi-file processing.
- A6: Overlap judgment (Step 8b): `templates/implementation-procedure.md` is also a target of `plans/20261102-080336_flowimp002_plan-release-units.md`. Judged compatible: that Plan edits the `## Scope` block; this Plan edits the Notes on `(new)`.
- A7: Overlap judgment (Step 8b): `tools/TOOL_DESCRIPTIONS.md` is also a target of several Plans. Judged compatible: each updates its own row.
- A8: Overlap judgment (Step 2, 2026-11-02): `tools/stale_detector.py` and `tests/tools/test_stale_detector.py` are also targets of `plans/20261102-080828_flowimp009_test-row-grouping.md` (its A9). Judged a sequencing dependency, not a conflict: this Plan adds a sibling pass after the per-document checks; that Plan changes how the document's own target and companions are read first; whichever lands second rebases. `skills/plan-to-implementation-procedure/workflow.md` and `skills/code-implementation/workflow.md` are also targets of `plans/20261102-080631_flowimp008_workitem-bulk-close.md` and `plans/20261102-081027_flowimp011_plan-amend-tool.md`. Judged compatible: those edit Step 4 (`Work Items Created`), Step 3c's additional-discovery paragraph, Step 7, and the scope rules, not Step 3c item (2) or the stale-detection result handling. `templates/implementation-procedure.md` is also a target of `plans/20261102-080828_flowimp009_test-row-grouping.md`; judged compatible (companion section and one-file statements versus the `(new)` notes).
- A9: Decision (Step 3a, 2026-11-02): `tools/mark_procedure_new_symbols.py` runs `tools/stale_detector.py` as a subprocess and parses stdout with `Symbol '<name>' not found in source`. Therefore (a) a mismatch kept stale because only a later sibling declares the name MUST keep the original `Symbol '<name>' not found in source` text as the start of its detail, with the sibling and rule appended; (b) the informational "resolved from sibling" lines MUST NOT contain that phrase. Falsifiable by the consumer test suite run unchanged.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | The true baseline count of archived procedures needing the boilerplate | The quoted sentence is not found in `implementations/done/`; the Issue's wording or count may differ | Re-measure at implementation by running the detector over the three archived sets and counting resolvable mismatches (AC-6) | False |
| UNK-02 | Whether "any sibling" is enough for a first version | The default chosen here is earlier-only; the cost of that choice is unmeasured | Ship earlier-only as the default with accept-any as an option; revisit after use | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/stale_detector.py` | Modify | Medium (run in every procedure generation and execution; four marking scripts import it) | 4 | N/A | not applicable (rsynced) |
| `tests/tools/test_stale_detector.py` | Modify | Low | 5 | N/A | not applicable (rsynced) |
| `skills/plan-to-implementation-procedure/workflow.md` | Modify | Medium | 8 | N/A | not applicable (rsynced) |
| `skills/code-implementation/workflow.md` | Modify | High (executes every procedure) | 13 | N/A | not applicable (rsynced) |
| `templates/implementation-procedure.md` | Modify | Medium (every procedure follows it) | 4 | N/A | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low | 82 | N/A | not applicable (rsynced) |

## Design
- Resolution flow: after the existing per-document checks produce mismatches, a sibling pass runs for each `symbol_missing` or import mismatch. The pass reads the procedure's Traceability `Source plan`, lists `implementations/*.md` and `implementations/done/*.md`, keeps documents whose `Source plan` has the same Plan file name (excluding the document itself), and collects the names and imports each marks `(new)` using the same marker rule as `_is_marked_new`. A mismatch whose name is in an eligible sibling's set is removed from `mismatches` and recorded in a separate list of resolved names (document, name, declaring sibling).
- Order rule: a sibling is eligible when its `seq` is smaller than the document's. The `--sibling-order any` option makes every sibling eligible. `--no-siblings` disables the pass. A name found only in an ineligible later sibling stays a mismatch with the detail naming that sibling and the rule.
- Output: the summary prints the active rule, one line per resolved name (`resolved from sibling: {name} declared (new) in {document}`), then the remaining mismatches. `is_stale` and `abort_execution` depend only on the remaining mismatches. The new result field has a default, so `StaleResult.from_dict`, `to_dict`, and the marking scripts keep working.
- Failure handling: a sibling that cannot be read, or whose `Source plan` cannot be parsed, is reported as a warning and skipped; it never turns a clean result stale.
- Text-only: no AST parsing and no network; sibling documents are read once per run, and the number of siblings per Plan is small.
- Compatibility: a document without a `Source plan` or without siblings produces the same output as before.
- Consumer output contract (A9): mismatch details keep the `Symbol '<name>' not found in source` / `Import '...' not found in source` prefix; resolved lines use different wording, so `tools/mark_procedure_new_symbols.py` never reads a resolved name as missing.

## Implementation steps
1. **Phase 1: Detector and its tests**
   - [ ] Add sibling discovery, declaration extraction, the order rule, the two options, and the informational output (`REQ-001`, `REQ-002`, `REQ-003`; `tools/stale_detector.py`)
   - [ ] Write tests for each case in the Tests section and run the existing consumer tests unchanged (`REQ-001`, `REQ-002`, `REQ-003`; `tests/tools/test_stale_detector.py`)
2. **Phase 2: Baseline measurement**
   - [ ] Run the detector over the archived procedures of the three Plans with `--no-siblings` and with the default, and record the counts (`REQ-001`; `tools/stale_detector.py`)
3. **Phase 3: Skill, template, and tool text**
   - [ ] Simplify Step 3c item (2) (`REQ-004`; `skills/plan-to-implementation-procedure/workflow.md`)
   - [ ] Update the Step 2 result handling (`REQ-004`; `skills/code-implementation/workflow.md`)
   - [ ] Add the sibling note to the `(new)` notes (`REQ-004`; `templates/implementation-procedure.md`)
   - [ ] Update the `stale_detector.py` entry (`REQ-005`; `tools/TOOL_DESCRIPTIONS.md`)
4. **Phase 4: Verification** (no `scripts/` or `config/` change, so no deploy step is required)
   - [ ] Run the tool lint sequence on `tools/stale_detector.py` and the checkers named in the Validation plan (`REQ-001` to `REQ-005`; all rows)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/stale_detector.py` | Unit and consumer regression | `uv run pytest tests/tools/test_stale_detector.py tests/tools/test_mark_procedure_new_symbols.py -v` | all pass |
| `tools/stale_detector.py` | Lint, type, security | `uv run ruff format tools/stale_detector.py`; `uv run ruff check tools/stale_detector.py`; `uv run mypy tools/stale_detector.py`; `uv run bandit tools/stale_detector.py` | clean |
| `tools/stale_detector.py` | Baseline over archived procedures (AC-6) | `uv run python tools/stale_detector.py <procedure>` over the three archived sets, with and without `--no-siblings` | counts recorded; resolvable mismatches drop to zero |
| `tools/TOOL_DESCRIPTIONS.md` | Sync check | `uv run python tools/check_tool_descriptions_sync.py` | passes |
| The two skills, the template | Reference, heading, and structure checks | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | no findings |

## Risks
- **Risk**: A name is accepted from an earlier sibling that never actually creates it. → **Mitigation**: checking the creation is out of scope; the informational line names the declaring document so the reader can confirm, and `code-implementation` still validates at execution.
- **Risk**: Matching siblings by Plan file name collides across two Plans with the same file name in `plans/` and `plans/done/`. → **Mitigation**: Plan file names carry a timestamp and id, so collisions do not occur in practice; a same-name case is reported as a warning.
- **Risk**: The result type change breaks the marking scripts. → **Mitigation**: the new field has a default and the consumer test suites run unchanged in Phase 1.
- **Risk**: `seq` order differs from the Plan phase order for some Plan. → **Mitigation**: Assumption A2 is falsifiable; the accept-any option is the fallback, and the implementing change records the baseline.
- **Risk**: `skills/code-implementation/workflow.md` is shared with sibling Plans. → **Mitigation**: A5 records that the edits touch different steps.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see `templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Detector and tests: `tools/stale_detector.py`, `tests/tools/test_stale_detector.py` | In Progress | — | — |  |
| 2 | Baseline measurement over the archived procedure sets: `tools/stale_detector.py` | Pending | — | — |  |
| 3 | Skill, template, and tool text: `skills/plan-to-implementation-procedure/workflow.md`, `skills/code-implementation/workflow.md`, `templates/implementation-procedure.md`, `tools/TOOL_DESCRIPTIONS.md` | In Progress | — | — |  |
| 4 | Verification: lint sequence and checkers | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261102-085029_01_tools_stale_detector.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261102-085029_02_tests_tools_test_stale_detector.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261102-085029_03_skills_plan-to-implementation-procedure_workflow.md.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261102-085029_04_skills_code-implementation_workflow.md.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261102-085029_05_templates_implementation-procedure.md.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261102-085029_06_tools_TOOL_DESCRIPTIONS.md.md` | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261030-191457_flowimp007_stale-sibling-new.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261102-080513
- **Related target files**: `tools/stale_detector.py`, `tests/tools/test_stale_detector.py`, `skills/plan-to-implementation-procedure/workflow.md`, `skills/code-implementation/workflow.md`, `templates/implementation-procedure.md`, `tools/TOOL_DESCRIPTIONS.md` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (sibling resolution keyed on `Source plan`, option, informational line) | `tools/stale_detector.py` | Phase 1, Phase 2 | AC-1, AC-6 | sibling unit tests; baseline run | Explicit in issue |
| REQ-001 | Testing Expectations (unit tests) | `tests/tools/test_stale_detector.py` | Phase 1 | AC-1 | sibling unit tests | Explicit in issue |
| REQ-002 | Required Changes (order rule); Dependencies (seq versus phase order); Step 3 | `tools/stale_detector.py` | Phase 1 | AC-2 | order-rule tests | Derived from confirmed evidence |
| REQ-002 | Acceptance Criteria (later sibling reported stale) | `tests/tools/test_stale_detector.py` | Phase 1 | AC-2 | order-rule tests | Explicit in issue |
| REQ-003 | Constraints (unmarked names stay stale; no-sibling unchanged) | `tools/stale_detector.py` | Phase 1 | AC-3 | regression and edge-case tests | Explicit in issue |
| REQ-003 | Testing Expectations (cycle, missing sibling) | `tests/tools/test_stale_detector.py` | Phase 1 | AC-3 | cycle and unreadable-sibling tests | Explicit in issue |
| REQ-004 | Required Changes (simplify the two skill texts) | `skills/plan-to-implementation-procedure/workflow.md` | Phase 3 | AC-5 | reference and heading checkers | Explicit in issue |
| REQ-004 | Required Changes (Step 2 result handling) | `skills/code-implementation/workflow.md` | Phase 3 | AC-5 | reference and heading checkers | Explicit in issue |
| REQ-004 | Target Files (`(new)` notes) | `templates/implementation-procedure.md` | Phase 3 | AC-5 | `check_workitem_structure.py` | Explicit in issue |
| REQ-005 | Target Files (`tools/TOOL_DESCRIPTIONS.md`); Acceptance Criteria | `tools/TOOL_DESCRIPTIONS.md` | Phase 3 | AC-4 | `check_tool_descriptions_sync.py` | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261102-085029 -->