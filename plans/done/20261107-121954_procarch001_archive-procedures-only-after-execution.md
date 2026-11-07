# Plan Output Template (Canonical)

## Goal
Prevent unexecuted implementation procedures from being silently archived to
`implementations/done/`, where they hide open work from `plan_dependency_order.py`, the
dependency order, and reviewers, by stating an explicit archive-order rule in the
workflow files and `routing.md`, adding a read-only detector for recently-archived-but-not
executed procedures, and deciding whether `plan_dependency_order.py` should report Plans
whose procedures are not all completed.

## Priority
Medium

## Scope
- **In-Scope**:
  - State, in `skills/plan-to-implementation-procedure/workflow.md` and
    `skills/code-implementation/workflow.md`, that only `code-implementation` Step 7 moves a
    procedure to `implementations/done/` and that `plan-to-implementation-procedure`
    archives the Plan only; reference this from the `routing.md` "Document workflow
    directories" table. (`REQ-001`)
  - Add a read-only, report-only detector that flags every implementation procedure whose
    archive date (first commit into `implementations/done/`) is within the last N days and
    whose `### Execution Status` table still contains a `Pending`, `In Progress`, or
    `Blocked` row; older procedures are never reported. (`REQ-002`)
  - Decide whether `plan_dependency_order.py` should report a Plan whose procedures are not
    all archived-and-completed as not finished, and implement that decision without changing
    the existing dependency-driven `ready`/`gated` classification. (`REQ-003`)
- **Out-of-Scope**:
  - Rewriting git history.
  - Changing the status of the historical `done/` procedures (the detector must not report
    them).
  - Changing the archive tools' refusal conditions beyond what `REQ-002` needs.
  - Any runtime `scripts/` change or database/schema change.
- **Dependencies**: `N/A: none`

## Background
Nine implementation procedures were moved to `implementations/done/` without being
executed, and nothing detected it until the code was found missing. Commit
`f0dff11a8` archived the `toolcli001` and `tracecompanion001` Plans' procedures while every
Execution Status row was still `Pending` and the code did not exist. `routing.md` defines
`implementations/done/` as procedures consumed by `prompts/03_implementation.md`, and
`tools/plan_dependency_order.py` treats an archived Plan as complete, so dependent Plans
were reported `ready`. `tools/manage_workitem_stage.py close-implementation` refuses only
when no row is `Pending`; many older procedures under `implementations/done/` also keep
stale `Pending` rows, so row status alone cannot show whether a procedure ran.

## Problem
An unexecuted procedure can be archived without any check, and the archive then hides open
work from `plan_dependency_order.py`, the dependency order, and reviewers.

## Reason for Change
The mistake cost a restore, a re-verification, and an out-of-order execution of nine
procedures, and it can recur on any batch archive.

## Implementation Intent
State the archive-order rule once, in the two workflow files that archive procedures and in
the `routing.md` directory table. Add a cheap, read-only detector keyed on the procedure's
archive date (first commit into `implementations/done/`) rather than file mtime, so it
reports only recent mistakes and never the historical `done/` files that already carry
stale rows. Optionally extend `plan_dependency_order.py` with a non-blocking note for Plans
whose procedures are not all completed, without altering its dependency-driven readiness.

## Requirements
- `REQ-001`: The rule that only `code-implementation` Step 7 moves a procedure to
  `implementations/done/` (and that `plan-to-implementation-procedure` archives the Plan
  only) is stated in `skills/plan-to-implementation-procedure/workflow.md`,
  `skills/code-implementation/workflow.md`, and referenced from the `routing.md` "Document
  workflow directories" table.
- `REQ-002`: A read-only, report-only detector warns when an implementation procedure
  archived within the last N days (by first commit into `implementations/done/`) still has a
  `Pending`, `In Progress`, or `Blocked` Execution Status row; procedures archived longer ago
  are never reported, and the detector never moves or edits a work item.
- `REQ-003`: `plan_dependency_order.py` reports, without changing its dependency-driven
  `ready`/`gated` classification, whether a Plan's procedures are not all archived-and
  completed — or the decision not to change it is recorded with rationale.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `skills/plan-to-implementation-procedure/workflow.md` | Modify | Add the archive-order rule: this workflow archives the Plan only, never the procedures. | `REQ-001` | Exists; archives the Plan in its own Step 4 (verified in Step 3) | None | Verified |
| `skills/code-implementation/workflow.md` | Modify | State that only Step 7 (archival move) moves a procedure to `implementations/done/`. | `REQ-001` | Exists; Step 7 performs the archival move (verified in Step 3) | None | Verified |
| `routing.md` | Modify | Add to the "Document workflow directories" table a note that `implementations/done/` holds only executed procedures and who archives them. | `REQ-001` | Line 171 documents `implementations/done/` as consumed by `prompts/03_implementation.md` (verified in Step 3) | None | Verified |
| `tools/manage_workitem_stage.py` | Modify | Add a read-only `detect-unexecuted-archive` subcommand (or equivalent) implementing `REQ-002`. | `REQ-002` | Exists; already owns `detect-stale` (mtime-based, lines 786-799) and the `close-implementation` refusal (lines 401-435); no archive-date detector exists (verified in Step 3) | `tests/tools/test_manage_workitem_stage.py` | Verified |
| `tests/tools/test_manage_workitem_stage.py` | Modify | Add detector tests over a temporary repository (recent archive with stale rows, recent archive completed, old archive with stale rows). | `REQ-002` | Existing test module for this tool (verified in Step 3) | `tests/tools/test_manage_workitem_stage.py` | Verified |
| `tools/plan_dependency_order.py` | Modify | Implement the `REQ-003` decision without changing the dependency-driven `ready`/`gated` classification. | `REQ-003` | Treats an archived Plan as CLOSED and removes it from the order (lines 223-240, 366-368); verified in Step 3 | None | Verified |

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
| `tools/check_workitem_traceability.py` | Decide whether the detector integrates here (workitem traceability) or stays in `manage_workitem_stage.py`; read its workitem-discovery helpers. | `REQ-002` detector ownership |
| `templates/execution-status.md` | Exact `### Execution Status` table format the detector must parse for `Pending`/`In Progress`/`Blocked` rows. | `REQ-002` |
| `rules/toolchain.md` | Validation sequence (format → lint → type → security → test) for the tool change. | All |
| `skills/DESIGN.md` | Output language, Change-impact table, Tool availability guard. | All |

## Acceptance Criteria
- `REQ-001`: Reading the two workflow files states that only `code-implementation` moves a
  procedure to `implementations/done/`; `routing.md`'s directory table references this.
- `REQ-002`: Running the detector on a temporary repository reports a recently archived
  procedure with a stale row, reports nothing for a recently archived completed procedure,
  and reports nothing for an old procedure with a stale row; the detector exits 0 and moves
  no file.
- `REQ-003`: The decision is recorded; if implemented, a Plan with an uncompleted procedure
  is surfaced without its dependents changing `ready`/`gated` status.

## Tests
- Detector unit tests over a temporary repository (tempdir + `git init`/commit to simulate
  archive dates): recent archive with a `Pending`/`In Progress`/`Blocked` row is reported;
  recent archive with all rows completed is not; old archive (outside the window) with a
  stale row is not; the detector never writes or moves a file. (`REQ-002`)
- Regression: existing `manage_workitem_stage.py` behavior (refusal on `Pending`, batch
  archive) is unchanged. (`REQ-002`)
- If `REQ-003` is implemented: a plan-dependency-order test asserting the readiness
  classification is unchanged for the same Plan. (`REQ-003`)

## Documentation Impact
`docs/*.md` does not require updating for this Plan: the affected files are skill workflow
files and `routing.md`, which are not in the `docs/` task-scope mapping. `tools/TOOL_DESCRIPTIONS.md`
requires a row only if the detector is added as a standalone new tool rather than a
subcommand of `manage_workitem_stage.py` (`REQ-002`); the recommended design uses a
subcommand and needs no `TOOL_DESCRIPTIONS.md` change.

## Assumptions
- The procedure's archive date is recoverable as the first commit that added the file at its
  `implementations/done/` path via `git log --diff-filter=A`; procedures committed before
  git tracking are skipped, not reported.
- The detector reuses the existing Execution Status parser shape already present in
  `manage_workitem_stage.py`.
- The window N defaults to 7 days (matching the existing `detect-stale` default) and is
  configurable via a CLI flag.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Window length N for "recently archived". | No precedent fixes N; the issue left it open. | Default 7 days (matches `detect-stale`), configurable via CLI flag. | False |
| UNK-02 | Which tool owns the detector: a new subcommand of `manage_workitem_stage.py` (recommended) or a standalone tool (which would need a `TOOL_DESCRIPTIONS.md` row). | The issue lists both tools and cites "Adding a new tool" validation. | Recommend the subcommand: co-located with `detect-stale` and the `close-implementation` refusal it complements, reuses the existing parser, avoids `TOOL_DESCRIPTIONS.md` churn. Recorded as a Design decision, not a blocker. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `skills/plan-to-implementation-procedure/workflow.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `skills/code-implementation/workflow.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `routing.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tools/manage_workitem_stage.py` | Modify | Medium | N/A | N/A | not applicable (rsynced) |
| `tests/tools/test_manage_workitem_stage.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tools/plan_dependency_order.py` | Modify | Medium | N/A | N/A | not applicable (rsynced) |

## Design
**Detector ownership (`UNK-02`)** — recommended decision: add the detector as a new
subcommand of `tools/manage_workitem_stage.py`, not a standalone tool. Rationale: it
co-locates with the existing `detect-stale` command and the `close-implementation`
`Pending` refusal it complements; it can reuse the file's Execution Status parsing; and it
avoids the `TOOL_DESCRIPTIONS.md` registration and `check_tool_descriptions_sync.py` gate a
new tool would trigger. Alternative (standalone tool under `tools/`) is acceptable if the
implementation phase prefers isolation, but then it needs a `TOOL_DESCRIPTIONS.md` row and
the "Adding a new tool" validation in `routing.md`.

**Detector basis** — keyed on archive date, not file mtime. The existing `detect-stale`
(786-799) flags any workitem whose mtime is older than `--days` and whose status is stale,
so it cannot distinguish a mistake made today from the ~dozens of historical `done/`
procedures that already carry stale rows. The new detector computes each procedure's archive
date as the first commit that added the file at its `implementations/done/` path
(`git log --diff-filter=A -- <done-path>`), and reports only procedures whose archive date is
within the last N days. This satisfies the constraint that historical `done/` files produce
no finding.

**`REQ-003` decision** — recommended: implement it as a supplementary, non-blocking note.
`plan_dependency_order.py` currently treats an archived Plan as CLOSED and removes it from
the order (223-240, 366-368); changing that to `gated` whenever a procedure is uncompleted
would ripple through dependent Plans. Instead, add a separate report line that flags a Plan
whose procedures are not all archived-and-completed while leaving the dependency-driven
`ready`/`gated` classification untouched. If the implementation phase judges the ripple
risk unacceptable, record the decision not to change `plan_dependency_order.py` with this
rationale.

## Implementation steps
1. **Phase 1: State the archive-order rule (`REQ-001`)**
   - [ ] Add to `skills/plan-to-implementation-procedure/workflow.md` that this workflow
     archives the Plan only, never the procedures. (`skills/plan-to-implementation-procedure/workflow.md`)
   - [ ] Add to `skills/code-implementation/workflow.md` that only Step 7 moves a procedure
     to `implementations/done/`. (`skills/code-implementation/workflow.md`)
   - [ ] Add a note to the `routing.md` "Document workflow directories" table that
     `implementations/done/` holds executed procedures and who archives them. (`routing.md`)
2. **Phase 2: Add the detector (`REQ-002`)**
   - [ ] Add a `detect-unexecuted-archive` subcommand to `tools/manage_workitem_stage.py`
     that enumerates `implementations/done/*.md`, computes each archive date
     (`git log --diff-filter=A`), parses the `### Execution Status` rows, and reports
     procedures archived within N days that still have a `Pending`/`In Progress`/`Blocked`
     row; older procedures are skipped; the command never moves or edits a work item and
     exits 0. (`tools/manage_workitem_stage.py`, `templates/execution-status.md`)
   - [ ] Make the window N configurable via a CLI flag (default 7). (`tools/manage_workitem_stage.py`)
   - [ ] Add detector tests over a temporary repository to
     `tests/tools/test_manage_workitem_stage.py`: recent archive with a stale row is
     reported; recent archive completed is not; old archive with a stale row is not; no
     file is moved. (`tests/tools/test_manage_workitem_stage.py`)
3. **Phase 3: `REQ-003` decision and verification**
   - [ ] Implement the recorded `REQ-003` decision in `tools/plan_dependency_order.py`
     without changing the dependency-driven `ready`/`gated` classification, plus its test.
     (`tools/plan_dependency_order.py`)
   - [ ] Run the `tools/` validation sequence (format, lint, mypy, bandit), the detector
     smoke-test on live `implementations/done/`, `check_tool_descriptions_sync.py` if a new
     tool was added, and confirm the historical `done/` files produce no finding.
     (`tools/manage_workitem_stage.py`, `tools/plan_dependency_order.py`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/manage_workitem_stage.py` | Unit: detector over a temporary repository; regression: existing commands unchanged. | `uv run pytest tests/tools/test_manage_workitem_stage.py` | All pass; detector reports only recent stale archives. |
| `tools/manage_workitem_stage.py` | Static: format, lint, type, security. | `uv run ruff format/check`, `uv run mypy tools/manage_workitem_stage.py`, `uv run bandit tools/manage_workitem_stage.py` | Clean. |
| `tools/manage_workitem_stage.py` | Smoke: run detector on live `implementations/done/`. | `uv run python tools/manage_workitem_stage.py detect-unexecuted-archive` | Exits 0; historical `done/` files produce no finding. |
| `tools/plan_dependency_order.py` | Unit: readiness classification unchanged. | `uv run pytest` (plan-dependency-order tests) | Pass. |
| `routing.md`, skill workflow files | Structure/consistency. | `uv run python tools/check_skills_references.py`, `uv run python tools/check_docs_quality.py` | Clean. |

## Risks
- **Risk**: The `REQ-003` change to `plan_dependency_order.py` alters the readiness of
  dependent Plans and disrupts the recommended order. → **Mitigation**: implement it as a
  separate, non-blocking report line that never changes the dependency-driven
  `ready`/`gated` classification; if the ripple risk cannot be contained, record the
  decision not to modify `plan_dependency_order.py`.
- **Risk**: The detector reports a legitimately still-in-progress archived procedure that a
  team intentionally keeps open. → **Mitigation**: the detector is report-only and the
  window is narrow (default 7 days); it flags candidates for human review, never blocks.
- **Risk**: Archive-date resolution fails for procedures committed before git tracking or
  after a history rewrite. → **Mitigation**: skip such procedures (do not report them) and
  document the limitation in the detector's help text.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | State the archive-order rule in the two workflow files and `routing.md` (`REQ-001`) | In Progress | — | — | Procedures generated this cycle (docs 01-03); awaiting code-implementation |
| 2 | Add the read-only archive-date detector to `manage_workitem_stage.py` and test it (`REQ-002`) | In Progress | — | — | Procedures generated this cycle (docs 04-05); awaiting code-implementation |
| 3 | Implement the `REQ-003` decision and run the full tool validation sequence | In Progress | — | — | Procedure generated this cycle (doc 06); awaiting code-implementation |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261107-125900_01_skills_plan-to-implementation-procedure_workflow.md | 1 | Procedure | Pending | — | — |
| implementations/20261107-125900_02_skills_code-implementation_workflow.md | 1 | Procedure | Pending | — | — |
| implementations/20261107-125900_03_routing.md.md | 1 | Procedure | Pending | — | — |
| implementations/20261107-125900_04_tools_manage_workitem_stage_py.md | 2 | Procedure | Pending | — | — |
| implementations/20261107-125900_05_tests_tools_test_manage_workitem_stage_py.md | 2 | Procedure | Pending | — | — |
| implementations/20261107-125900_06_tools_plan_dependency_order_py.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261106-123521_procarch001_archive-procedures-only-after-execution.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261107-121954
- **Related target files**: `skills/plan-to-implementation-procedure/workflow.md`,
  `skills/code-implementation/workflow.md`, `routing.md`, `tools/manage_workitem_stage.py`,
  `tests/tools/test_manage_workitem_stage.py`, `tools/plan_dependency_order.py`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; Background/Problem | `skills/plan-to-implementation-procedure/workflow.md` | 1 | REQ-001 | Structure/read; `check_skills_references.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes; Background/Problem | `skills/code-implementation/workflow.md` | 1 | REQ-001 | Structure/read; `check_skills_references.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes; routing.md directory table | `routing.md` | 1 | REQ-001 | Structure/read; `check_docs_quality.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes; Unresolved Questions | `tools/manage_workitem_stage.py` | 2 | REQ-002 | Detector temp-repo test; regression; smoke on live `done/` | Confirmed by repository evidence |
| REQ-002 | Required Changes; Unresolved Questions | `tests/tools/test_manage_workitem_stage.py` | 2 | REQ-002 | Detector temp-repo test | Confirmed by repository evidence |
| REQ-003 | Required Changes | `tools/plan_dependency_order.py` | 3 | REQ-003 | plan-dependency-order readiness test | Derived from confirmed evidence |
<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261107-125900 -->
