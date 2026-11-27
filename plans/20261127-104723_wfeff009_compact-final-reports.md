## Goal
- Define, for each of the four workflows (`code-implementation`, `plan-to-implementation-procedure`, `issue-to-plan`, `git-commit-and-sync`), a compact chat report used when the cycle had no deviation (a status line, a validation line, and the deviations list), keeping the existing full report for any deviation and keeping every fact recorded in its persisted place.

## Priority
Low

## Scope
- **In-Scope**: the final-report text of the four `workflow.md` files (Final Report, Final report, Step 9, Phase 9); moving each current full-form text verbatim into the matching edge file (a new edge file for `git-commit-and-sync`) so the skill size ceilings still hold.
- **Out-of-Scope**: changing what any workflow verifies or records; the persisted records themselves; `rules/ai-execution.md` Progress Reporting (Base) and `rules/workflow-lifecycle.md` Validation Reporting; the `prompts/*.md` entry points (see Assumptions); any tool.
- **Dependencies**: N/A: none

## Background
Verified in Step 3: the four reports are `skills/code-implementation/workflow.md` "Final Report" (3220 B: a one-line traceability summary, a seven-row Execution Status table, questions asked, next steps, blocker log, work items), `skills/plan-to-implementation-procedure/workflow.md` "Final report" (926 B), `skills/issue-to-plan/workflow.md` Step 9 (2030 B), and `skills/git-commit-and-sync/workflow.md` Phase 9 (858 B). Their persisted facts live in the procedure's Execution Status Notes (changed files, check results), the Plan's Execution Status and `Work Items Created`, the archived documents' Traceability sections, and the commit. `tools/check_skill_size_baseline.txt` ceilings leave almost no room: `skills/code-implementation/workflow.md` 42112 B of 42118 B, `skills/issue-to-plan/workflow.md` 42539 B of 42540 B, `skills/git-commit-and-sync/workflow.md` 22947 B of 22947 B, `skills/plan-to-implementation-procedure/workflow.md` 34756 B of 34876 B.

## Problem
Long reports add output tokens to every cycle without adding information when nothing deviated. Three Issue details need correction: no tool or skill reads the chat report text (the open question is answered), the one-line traceability summary of `code-implementation` is declared that cycle's traceability record in its workflow text, and the size ceilings make a plain addition impossible.

## Reason for Change
Token cost; no correctness risk. Not urgent.

## Implementation Intent
Per workflow, state the compact form and its condition at the report section, and keep the full form as the response to any deviation by moving its current text verbatim to the edge file, loaded only when a deviation occurred.

## Requirements
- `REQ-001`: `skills/code-implementation/workflow.md` Final Report defines the compact form for a cycle with no deviation (no `Blocked`, no Attempt Limit retry, no Rollback, no `Needs confirmation`, no question asked, no unrelated failure reported, Plan Execution Status updated): the unchanged one-line traceability summary, one validation line (stale check, validators, tests and coverage, documentation outcome), and one `Next steps` line; any deviation requires the full form.
- `REQ-002`: `skills/plan-to-implementation-procedure/workflow.md` Final report defines the compact form for a cycle with no deviation (no non-blocking `Needs confirmation`, no `Plan Gap`, no uncovered row, no Step 3a Plan edit, no unmapped step, no overlap, no gated procedure): one status line (Plan path and outcome, generated documents in `seq` order), one validation line (coverage check result, structure and stale results), and the next step.
- `REQ-003`: `skills/issue-to-plan/workflow.md` Step 9 defines the compact form for a cycle with no deviation (no unresolved item, no generated Unknown or Risk file, no overlap, not `Blocked`): one status line (Plan path, Requirement count, target-row count, Path A or B, freeze status, pending move), one validation line (information completeness, traceability), and the next steps.
- `REQ-004`: `skills/git-commit-and-sync/workflow.md` Phase 9 defines the compact form for a run with no deviation (no unrelated gate failure, no other commits published, no remaining uncommitted change, no stop condition, no warning): one status line (branch, commit SHA, message subject, sync and push results), one validation line (gate, post-sync, and pre-push recheck results).
- `REQ-005`: Each workflow states that every fact the full form requires either appears in the compact form or is a deviation that triggers the full form, and that persisted records (traceability values, Execution Status, Plan updates, commit message) are unchanged; the full-form text is moved verbatim, so no item is removed.
- `REQ-006`: Each moved full form sits in `skills/code-implementation/workflow-edge.md`, `skills/plan-to-implementation-procedure/workflow-edge.md`, `skills/issue-to-plan/workflow-edge.md`, or the new `skills/git-commit-and-sync/workflow-edge.md`, reached by the file's existing "load `...workflow-edge.md` and follow its ... section" form; `tools/check_skill_size.py`, `tools/check_skills_references.py`, and `tools/check_skills_heading_cycles.py` pass, and each `workflow.md` ends at or below its baseline ceiling.

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8b: every row `Verified`; `tools/audit_plan_target_paths.py` and the additional checks passed)

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `skills/code-implementation/workflow.md` | Replace the Final Report body with the compact form and its condition plus a pointer to the full-form section | The Issue's Target Files name it; ceiling 42118 B against 42112 B | `REQ-001`, `REQ-005`, `REQ-006`; AC-1, AC-5, AC-6 | `skills/code-implementation/workflow.md` `## Final Report` (3220 B) and its subsections; `tools/check_skill_size_baseline.txt` records 42118 (checked in Step 3) | `tools/check_skill_size.py` run | Verified |
| `skills/code-implementation/workflow-edge.md` | Add a `### Final Report: full form` section holding the moved text verbatim | Receives the moved text; 12258 B plus about 3 KB stays below the 16384 B limit; no baseline entry | `REQ-001`, `REQ-006`; AC-1, AC-6 | `skills/code-implementation/workflow-edge.md` is 12258 B; `workflow.md` already loads its sections by heading (checked in Step 3) | `tools/check_skill_size.py` run | Verified |
| `skills/plan-to-implementation-procedure/workflow.md` | Replace the Final report body with the compact form and its condition plus a pointer | The Issue's Target Files name it; ceiling 34876 B against 34756 B | `REQ-002`, `REQ-005`, `REQ-006`; AC-2, AC-5, AC-6 | `skills/plan-to-implementation-procedure/workflow.md` `### Final report` (926 B) (checked in Step 3) | `tools/check_skill_size.py` run | Verified |
| `skills/plan-to-implementation-procedure/workflow-edge.md` | Add a `### Final report: full form` section holding the moved text verbatim | Receives the moved text; 7556 B plus under 1 KB | `REQ-002`, `REQ-006`; AC-2, AC-6 | `skills/plan-to-implementation-procedure/workflow-edge.md` is 7556 B (checked in Step 3) | `tools/check_skill_size.py` run | Verified |
| `skills/issue-to-plan/workflow.md` | Replace the Step 9 report text with the compact form and its condition plus a pointer, leaving the Step 9 gate text intact | The Issue's Target Files name it; ceiling 42540 B against 42539 B | `REQ-003`, `REQ-005`, `REQ-006`; AC-3, AC-5, AC-6 | `skills/issue-to-plan/workflow.md` `## Step 9: Final Validation` (2030 B) holds both the report fields and the move gate; `tools/check_skill_size_baseline.txt` records 42540 (checked in Step 3) | `tools/check_skill_size.py` run | Verified |
| `skills/issue-to-plan/workflow-edge.md` | Add a `### Step 9: full report` section holding the moved report text verbatim | Receives the moved text; 4512 B plus under 2 KB | `REQ-003`, `REQ-006`; AC-3, AC-6 | `skills/issue-to-plan/workflow-edge.md` is 4512 B (checked in Step 3) | `tools/check_skill_size.py` run | Verified |
| `skills/git-commit-and-sync/workflow.md` | Replace the Phase 9 report list with the compact form and its condition plus a pointer | The Issue's Target Files name it; ceiling 22947 B equals the current size | `REQ-004`, `REQ-005`, `REQ-006`; AC-4, AC-5, AC-6 | `skills/git-commit-and-sync/workflow.md` `## Phase 9: Report` (858 B); `tools/check_skill_size_baseline.txt` records 22947 (checked in Step 3) | `tools/check_skill_size.py` run | Verified |
| `skills/git-commit-and-sync/workflow-edge.md` | Create the edge file with a `### Phase 9: full report` section holding the moved list verbatim | New file; the skill has no edge file, and 0 B of headroom needs the full form moved out; the directory `skills/git-commit-and-sync/` exists | `REQ-004`, `REQ-006`; AC-4, AC-6 | `skills/git-commit-and-sync/` holds `SKILL.md` and `workflow.md` only (checked in Step 3) | `tools/check_skill_size.py` run | Verified |

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
- Write every `File Path` cell, every `tests/...py` path in `Related Tests`, and every path in
  `Implementation steps` in backticks.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `rules/ai-execution.md` | Progress Reporting (Base): one-line step reports and read-back of recorded values; the compact form must stay consistent with it | `REQ-005` |
| `rules/workflow-lifecycle.md` | Validation Reporting: the five fields (Status, Output, Validation, Unresolved items, Pending move) that every pre-archival report carries | `REQ-003`, `REQ-005` |
| `skills/code-implementation/SKILL.md` | Output format names `workflow.md` Final Report as the reporting structure; its wording must stay true | `REQ-001` |
| `skills/git-commit-and-sync/SKILL.md` | Its Phase overview row 9 summarizes the report items | `REQ-004` |
| `prompts/03_implementation.md` | Line 89 "Follow ... Final Report in full." must still read correctly with a compact default | `REQ-001`, `REQ-005` |
| `prompts/01_issue-to-plan.md` | "Follow ... Step 9 in full." must still read correctly | `REQ-003`, `REQ-005` |
| `tools/check_skill_size_baseline.txt` | The four ceilings | `REQ-006` |

## Acceptance Criteria
- AC-1 (`REQ-001`): `skills/code-implementation/workflow.md` states the compact form and the deviation conditions; the full form is reachable and identical to the pre-change text.
- AC-2 (`REQ-002`): The same for `skills/plan-to-implementation-procedure/workflow.md`.
- AC-3 (`REQ-003`): The same for `skills/issue-to-plan/workflow.md` Step 9, with the Step 9 move gate text unchanged.
- AC-4 (`REQ-004`): The same for `skills/git-commit-and-sync/workflow.md` Phase 9.
- AC-5 (`REQ-005`): Each workflow states that persisted records are unchanged and that a deviation requires the full form; for each of the four workflows every item of the old full form is either in the compact form or listed as a deviation.
- AC-6 (`REQ-006`): `tools/check_skill_size.py`, `tools/check_skills_references.py`, and `tools/check_skills_heading_cycles.py` pass, each `workflow.md` is at or below its ceiling, and a whitespace-normalized comparison shows the moved full-form text unchanged.

## Tests
- `REQ-006`: `uv run python tools/check_skill_size.py`, `uv run python tools/check_skills_references.py`, `uv run python tools/check_skills_heading_cycles.py`.
- `REQ-005`: a documented review of one past report of each workflow against its compact form (the reports of this session's cycles), listing any fact that would be lost (none allowed).
- `REQ-005`: `rg` over `tools/`, `skills/`, `rules/`, `prompts/`, and `tests/` for the report line formats, recorded as the "no reader" evidence.
- Whole-file comparison: moved text compared before and after, whitespace-normalized.

## Documentation Impact
N/A: no `docs/*.md` change. The four workflow files and their edge files are target rows; their text is the procedure itself (`routing.md` Documentation row exception), not documentation of code.

## Assumptions
- No tool or skill reads the chat report text (resolves the Issue's open question): a search of `tools/`, `skills/`, `rules/`, `prompts/`, and `tests/` for the traceability line format (`Source: ... | Issue:`), `Pending move`, `Unresolved items`, and the report field names found only the workflow and rule texts that define them, no parser (checked in Step 3).
- "Follow ... in full" in `prompts/01_issue-to-plan.md` and `prompts/03_implementation.md` means executing the whole section, including its compact-or-full rule, so the prompts need no change; the procedure phase rechecks the wording and raises a fallout amendment adding a prompt row if it reads as forcing the full form.
- `rules/workflow-lifecycle.md` Validation Reporting is satisfied by the compact status line (Status, Output, Pending move) and validation line (Validation, Unresolved items), because all five fields stay present.
- The compact form of `code-implementation` keeps the one-line traceability summary in every case because that workflow names it the cycle's traceability record; the Execution Status table and Blocker Log are persisted in the procedure's own Execution Status.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether `prompts/01_issue-to-plan.md`, `prompts/02_plan-to-implementation-procedure.md`, or `prompts/03_implementation.md` read as forcing the full form through "in full" | Wording judgment, no tool decides it | Procedure phase rereads the three prompts after the edit; a conflict becomes a fallout amendment with a prompt row | False |
| UNK-02 | Whether the full-form text moves cleanly (no cross-reference to a heading that moves) | A reference search for the moved headings is done at implementation | `tools/check_skills_references.py` and `tools/check_skills_heading_cycles.py` at each phase | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `skills/code-implementation/workflow.md` | Modify | Medium — loaded by every code-implementation cycle; ceiling 42118 B | 21 | High (98% single author) | not applicable (not rsynced) |
| `skills/code-implementation/workflow-edge.md` | Modify | Low — loaded on demand; 12258 B under a 16384 B limit | 1 | High (100% single author) | not applicable (not rsynced) |
| `skills/plan-to-implementation-procedure/workflow.md` | Modify | Medium — loaded by every plan-to-implementation-procedure cycle; ceiling 34876 B | 12 | High (98% single author) | not applicable (not rsynced) |
| `skills/plan-to-implementation-procedure/workflow-edge.md` | Modify | Low — loaded on demand | 2 | High (100% single author) | not applicable (not rsynced) |
| `skills/issue-to-plan/workflow.md` | Modify | Medium — loaded by every issue-to-plan cycle; 1 B below its ceiling | 14 | High (98% single author) | not applicable (not rsynced) |
| `skills/issue-to-plan/workflow-edge.md` | Modify | Low — loaded on demand | 1 | High (100% single author) | not applicable (not rsynced) |
| `skills/git-commit-and-sync/workflow.md` | Modify | Medium — loaded by every commit and sync run; at its ceiling | 4 | High (96% single author) | not applicable (not rsynced) |
| `skills/git-commit-and-sync/workflow-edge.md` | Create | Low — new on-demand file, no existing reader | N/A (new) | N/A (new) | not applicable (not rsynced) |

## Design
Path B (more than 3 files, a new file). Analysis recorded:
- Architecture (checked in Step 3): the four workflows already use the pattern "load `...workflow-edge.md` and follow its ... section" for rarely used branches (`skills/code-implementation/workflow.md` Step 1 edge cases, Rollback; `skills/issue-to-plan/workflow.md` Step 8c; `skills/plan-to-implementation-procedure/workflow.md` Step 3c). The full form is exactly such a branch (needed only on a deviation), so it moves to the edge file and the workflow keeps the compact default plus the pointer.
- Dependency graphing (checked in Step 3): the report sections are referenced by `skills/code-implementation/SKILL.md` (Output format), `skills/git-commit-and-sync/SKILL.md` (Phase overview row 9), `prompts/01_issue-to-plan.md` Step 9, `prompts/02_plan-to-implementation-procedure.md` Step 4, and `prompts/03_implementation.md` Final Report; `rules/workflow-lifecycle.md` Validation Reporting defines the pre-archival fields. No tool reads the report text.
- Historical analysis and operational dependencies: churn and bus factor are in `Affected areas`; no MCP server, database, or port is involved.
- Decision (deviation conditions): each workflow lists its own deviation conditions at the report section, built from outcomes the workflow already defines (`Blocked`, retries, rollback, `Needs confirmation`, `Plan Gap`, unmapped steps, unresolved items, unrelated gate failures, warnings, other commits published, remaining uncommitted changes), so no new judgment concept is introduced.
- Decision (move verbatim): the moved text is copied without rewording and compared whitespace-normalized, so the full form cannot silently change.
- Decision (new edge file for git): `skills/git-commit-and-sync/` has no edge file and its ceiling equals its size; a new `workflow-edge.md` is the same pattern as the other three skills.
- Predictable fallout check (checked in Step 3): module size - not applicable (no Python); pinned counts - `tools/check_skill_size_baseline.txt` is lowered only advisorily, not edited; tool inventory - no tool added; generated blocks - not affected; gate entry - not affected. A reference to the moved headings from `skills/*/SKILL.md` is searched with `rg` at implementation.
- Consumer scan and persisted schema check: not applicable (no schema, public API, shared constant, or removed symbol; text moves verbatim).
- Validation baseline: N/A: no Python target.

## Implementation steps
1. **Phase 1: `code-implementation`**
   - [ ] Add the full-form section to `skills/code-implementation/workflow-edge.md` (`REQ-001`, `REQ-006`).
   - [ ] Replace the Final Report body of `skills/code-implementation/workflow.md` with the compact form and the pointer (`REQ-001`, `REQ-005`, `REQ-006`); run the three skill checks.
2. **Phase 2: `plan-to-implementation-procedure`**
   - [ ] Add the full-form section to `skills/plan-to-implementation-procedure/workflow-edge.md` (`REQ-002`, `REQ-006`).
   - [ ] Replace the Final report body of `skills/plan-to-implementation-procedure/workflow.md` (`REQ-002`, `REQ-005`, `REQ-006`); run the three skill checks.
3. **Phase 3: `issue-to-plan`**
   - [ ] Add the full-report section to `skills/issue-to-plan/workflow-edge.md` (`REQ-003`, `REQ-006`).
   - [ ] Replace the Step 9 report text of `skills/issue-to-plan/workflow.md` (`REQ-003`, `REQ-005`, `REQ-006`); run the three skill checks.
4. **Phase 4: `git-commit-and-sync`**
   - [ ] Create `skills/git-commit-and-sync/workflow-edge.md` with the full-form section (`REQ-004`, `REQ-006`).
   - [ ] Replace the Phase 9 list of `skills/git-commit-and-sync/workflow.md` (`REQ-004`, `REQ-005`, `REQ-006`); run the three skill checks.
5. **Phase 5: Verification and deployment check**
   - [ ] Review one past report of each workflow against its compact form and rerun the "no reader" search (`REQ-005`; `skills/code-implementation/workflow.md`).
   - [ ] Deployment: N/A, no `scripts/` or `config/` file changes; `skills/` is not rsynced by `deploy/deploy.sh`.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| the four `workflow.md` files | Size ceilings | `uv run python tools/check_skill_size.py` | Exit 0; each file at or below its ceiling |
| the four edge files | Size limit 16384 B | `uv run python tools/check_skill_size.py` | Exit 0 |
| all eight files | References and heading cycles | `uv run python tools/check_skills_references.py`, `uv run python tools/check_skills_heading_cycles.py` | Exit 0 |
| moved text | Verbatim comparison | whitespace-normalized comparison of the pre-change text from `git show HEAD:<file>` with the edge section | Identical |
| report content | Review of past reports | manual comparison recorded in the implementation report | No fact lost |

## Risks
- **Risk**: A moved heading is referenced elsewhere and the reference breaks → **Mitigation**: `tools/check_skills_references.py` and `tools/check_skills_heading_cycles.py` run at each phase, and an `rg` search for the moved heading names runs before the edit.
- **Risk**: The compact form drops a fact the full form required → **Mitigation**: the deviation list is built from the full form's fields, the review of a past report is a Phase 5 step, and the full text stays verbatim in the edge file.
- **Risk**: A workflow ends above its ceiling → **Mitigation**: the compact text plus pointer is shorter than the text it replaces for all four (3220, 926, 2030, 858 B), and the size check runs per phase.
- **Risk**: `skills/git-commit-and-sync/SKILL.md` row 9 or a prompt no longer matches the new default → **Mitigation**: both are reference files read in Phase 5; a conflict becomes a fallout amendment (Plan Amendment Approval Classes).
- **Risk**: The agent uses the compact form in a cycle that had a deviation → **Mitigation**: each section states the deviation conditions first and says "any one of these requires the full form".

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Compact form for `code-implementation` (`skills/code-implementation/workflow-edge.md`, `skills/code-implementation/workflow.md`) | Pending | — | — | |
| 2 | Compact form for `plan-to-implementation-procedure` (`skills/plan-to-implementation-procedure/workflow-edge.md`, `skills/plan-to-implementation-procedure/workflow.md`) | Pending | — | — | |
| 3 | Compact form for `issue-to-plan` (`skills/issue-to-plan/workflow-edge.md`, `skills/issue-to-plan/workflow.md`) | Pending | — | — | |
| 4 | Compact form for `git-commit-and-sync` (`skills/git-commit-and-sync/workflow-edge.md`, `skills/git-commit-and-sync/workflow.md`) | Pending | — | — | |
| 5 | Review past reports; deployment check is N/A (`skills/code-implementation/workflow.md`) | Pending | — | — | |

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
- **Source issue**: issues/20261126-151444_wfeff009_compact-final-reports.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261127-104723
- **Evidence revision**: 1b5713cfa10bad8c4ce6aa43ede8c07cf30d54ee
- **Related target files**: `skills/code-implementation/workflow.md`, `skills/code-implementation/workflow-edge.md`, `skills/plan-to-implementation-procedure/workflow.md`, `skills/plan-to-implementation-procedure/workflow-edge.md`, `skills/issue-to-plan/workflow.md`, `skills/issue-to-plan/workflow-edge.md`, `skills/git-commit-and-sync/workflow.md`, `skills/git-commit-and-sync/workflow-edge.md`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| `REQ-001` | Issue Required Changes 1; `skills/code-implementation/workflow.md` Final Report | `skills/code-implementation/workflow.md` | Phase 1 | AC-1, AC-5 | `uv run python tools/check_skill_size.py` | Confirmed by repository evidence |
| `REQ-001` | Issue Required Changes 1 | `skills/code-implementation/workflow-edge.md` | Phase 1 | AC-1 | `uv run python tools/check_skill_size.py` | Derived from confirmed evidence |
| `REQ-002` | Issue Required Changes 1; `skills/plan-to-implementation-procedure/workflow.md` Final report | `skills/plan-to-implementation-procedure/workflow.md` | Phase 2 | AC-2, AC-5 | `uv run python tools/check_skill_size.py` | Confirmed by repository evidence |
| `REQ-002` | Issue Required Changes 1 | `skills/plan-to-implementation-procedure/workflow-edge.md` | Phase 2 | AC-2 | `uv run python tools/check_skill_size.py` | Derived from confirmed evidence |
| `REQ-003` | Issue Required Changes 1; `skills/issue-to-plan/workflow.md` Step 9 | `skills/issue-to-plan/workflow.md` | Phase 3 | AC-3, AC-5 | `uv run python tools/check_skill_size.py` | Confirmed by repository evidence |
| `REQ-003` | Issue Required Changes 1 | `skills/issue-to-plan/workflow-edge.md` | Phase 3 | AC-3 | `uv run python tools/check_skill_size.py` | Derived from confirmed evidence |
| `REQ-004` | Issue Required Changes 1; `skills/git-commit-and-sync/workflow.md` Phase 9 | `skills/git-commit-and-sync/workflow.md` | Phase 4 | AC-4, AC-5 | `uv run python tools/check_skill_size.py` | Confirmed by repository evidence |
| `REQ-004` | Issue Required Changes 1; ceiling equals size | `skills/git-commit-and-sync/workflow-edge.md` | Phase 4 | AC-4 | `uv run python tools/check_skill_size.py` | Derived from confirmed evidence |
| `REQ-005` | Issue Required Changes 2, Constraints | `skills/code-implementation/workflow.md` | Phase 1, Phase 5 | AC-5 | review of a past report | Explicit in issue |
| `REQ-005` | Issue Required Changes 2, Constraints | `skills/plan-to-implementation-procedure/workflow.md` | Phase 2, Phase 5 | AC-5 | review of a past report | Explicit in issue |
| `REQ-005` | Issue Required Changes 2, Constraints | `skills/issue-to-plan/workflow.md` | Phase 3, Phase 5 | AC-5 | review of a past report | Explicit in issue |
| `REQ-005` | Issue Required Changes 2, Constraints | `skills/git-commit-and-sync/workflow.md` | Phase 4, Phase 5 | AC-5 | review of a past report | Explicit in issue |
| `REQ-006` | Issue Constraints (size gate), Acceptance Criteria 3 | `skills/code-implementation/workflow.md` | Phase 1 | AC-6 | `uv run python tools/check_skills_references.py` | Explicit in issue |
| `REQ-006` | Issue Constraints, ceilings measured in Step 3 | `skills/plan-to-implementation-procedure/workflow.md` | Phase 2 | AC-6 | `uv run python tools/check_skills_references.py` | Explicit in issue |
| `REQ-006` | Issue Constraints, ceilings measured in Step 3 | `skills/issue-to-plan/workflow.md` | Phase 3 | AC-6 | `uv run python tools/check_skills_references.py` | Explicit in issue |
| `REQ-006` | Issue Constraints, ceilings measured in Step 3 | `skills/git-commit-and-sync/workflow.md` | Phase 4 | AC-6 | `uv run python tools/check_skills_references.py` | Explicit in issue |
