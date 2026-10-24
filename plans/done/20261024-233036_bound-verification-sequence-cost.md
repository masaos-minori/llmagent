# Plan: bound verification sequence cost in code-implementation cycles

## Goal
- Make impact-based test selection actually take effect during `code-implementation` fix iterations (it currently cannot,
  see Design), scope post-fix re-validation to the validators a fix can affect, and keep full-suite runs to the
  once-plus-Attempt-Limit bound the workflow already states, with every verification gate unchanged and each skipped
  re-run recorded.

## Priority
Medium

## Scope
- **In-Scope**: in `skills/code-implementation/workflow.md`, the iteration test command in Step 4 (testmon with a selector
  that survives `-m`), scoped re-validation wording in Step 3e's on-failure path and Step 4's fix-then-rerun path, the rule
  that a full-suite re-run follows only a passing targeted run, and the audit note for skipped re-runs; in
  `skills/python-test-and-fix/workflow.md` Step 10 and `skills/python-test-and-fix/SKILL.md` Phase overview row 10, the
  correction of the testmon commands and wording.
- **Out-of-Scope**: removing or weakening the single per-cycle full-suite gate, the `diff-cover` threshold in
  `rules/toolchain.md`, the boundary-test requirement, or the `routing.md` checker obligations; `AGENTS.md` Attempt Limit
  and Failure Log semantics; `rules/ai-execution.md` Repository Tool Usage item 8; redundant re-reads, `git` state checks,
  and call sequencing (perf001); question-call count and wait policy (perf005); lazy loading of the Step 0 load set (user
  decision 2026-10-24); toolchain changes (pytest configuration, CI, coverage thresholds, `rules/toolchain.md` gate
  definitions).
- **Dependencies**: perf001 (Plan archived at `plans/done/20261024-215858_cut-redundant-rereads-and-turn-overhead.md`,
  procedures generated, not yet executed) edits `skills/code-implementation/workflow.md` `## Multi-file processing`, and perf005
  (Frozen Plan `plans/20261024-233356_cut-blocking-question-waits.md`) adds a `## Question policy` section and a Final Report
  line to the same file; neither touches Step 3e or Step 4, so they are completable in any order, but whichever is applied
  later MUST re-read the current file and re-anchor (30-day churn on the file: 13 commits).

## Background
A 2026-10-24 investigation over the opencode session-history DB reported, for 186 `code-implementation` cycles, 34.8 shell
calls and about 7.1 minutes of command execution per cycle, `pytest` 3.44 times per cycle with full-suite runs averaging
157 s, full-suite re-runs in failure-retry loops (22 full runs across 6 cycles in the worst session), and zero
`pytest --testmon` calls although `pytest-testmon` is declared in `pyproject.toml` and named in Step 4 of the workflow.
Post-fix re-validation re-runs the whole Step 3e sequence (ruff 1.51, mypy 1.44, bandit 0.77, `lint-imports` 0.72 per cycle).

## Problem
Repeated full-suite `pytest` runs and whole-sequence re-passes after each fix are the largest controllable machine-time cost
inside a cycle, and the configured impact-based selection is never used.

## Reason for Change
Full-suite execution alone accounts for 369 minutes in the measured cycles, and retry loops compound it. Cutting repeated
runs removes work volume without removing a gate.

## Implementation Intent
Keep every gate; change iteration discipline only. Use impact-based selection for iteration runs with the selector that works
together with the repository's `-m` safety filter. After a full-suite failure, confirm the fix with a targeted run before the
next full run. Re-run, after a fix, only the validators whose inputs the fix changed, and record every validator skipped as
already passed and unaffected so the evidence stays auditable. Correct the same selector error in the `python-test-and-fix`
skill that the workflow cites.

## Requirements
- `REQ-001`: In `skills/code-implementation/workflow.md` Step 4, make impact-based selection the iteration path for targeted
  tests, using `uv run pytest --testmon-forceselect -m "not integration and not production_paths_allowed" tests/` (a selector
  that survives `-m`), with a documented fallback (mirrored-path tests plus `rg`-found importers) only when testmon cannot
  run, and a stated reason recorded in that case.
- `REQ-002`: In Step 3e's on-failure path and Step 4's fix-then-rerun path, state that after a fix only the validators whose
  inputs the fix changed are re-run (formatting or lint fix: `ruff`; type fix: `mypy` and `ruff`; import change:
  `lint-imports`, `mypy`, and `ruff`; security fix: `bandit` and `ruff`), that the complete Step 3e sequence is re-run when a
  fix spans families or changes imports or public signatures, and that "Completed when: all of the above pass" holds when
  every validator has passed against the final content of the files it examines.
- `REQ-003`: In Step 4, state that a full-suite re-run after a failure follows only a passing targeted run that includes the
  previously failing tests, within the existing Attempt Limit, so no full-suite run is spent on a failure a targeted run could
  have caught.
- `REQ-004`: In Step 3e and Step 4, require that each validation run skipped as "passed earlier and unaffected by this fix" is
  recorded in the Execution Status Notes of the validation row, naming the validator and the fix, so the evidence
  requirements remain auditable.
- `REQ-005`: In `skills/python-test-and-fix/workflow.md` Step 10 and `skills/python-test-and-fix/SKILL.md` Phase overview row
  10, correct the testmon commands and wording: testmon selection is deactivated whenever `-m` is given, so the example forms
  that combine `--testmon` with `-m` run everything; use `--testmon-forceselect` together with `-m`, and replace "if
  available" with the condition that actually applies. Re-verified 2026-10-24 (Step 3a of
  `plan-to-implementation-procedure`): Step 10 already carries a `--testmon-forceselect -m ...` example and its description
  (added earlier the same day), so only the remaining plain-`--testmon` forms (the `--testmon ... -m` example line and the
  opening "Use `pytest --testmon`" and "MUST NOT re-run `pytest --testmon`" prose) and the missing "`-m` deactivates plain
  `--testmon`" note are changed; the existing forceselect and noselect lines stay. Measured again 2026-10-24 on
  `tests/tools/test_check_workitem_structure.py`: `--testmon -m ...` printed "selection automatically deactivated because -m
  was used" (7 passed); `--testmon-forceselect -m ...` printed "7 deselected".

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `skills/code-implementation/workflow.md` | Detailed procedure for Steps 3e and 4 | Replace the "when available" bare `pytest --testmon tests/` with the `-m`-compatible selector and fallback, add scoped re-validation to the Step 3e on-failure path and Step 4's fix-then-rerun path, add the targeted-before-full rule, and add the skipped-run audit note | `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`; AC-1, AC-2, AC-3, AC-4, AC-5, AC-6 | (checked in Step 3) `skills/code-implementation/workflow.md` Step 4 first bullet "Determine the targeted test scope via `pytest --testmon tests/` ... when available; otherwise ...", Step 4 "Run the repository-defined full test suite exactly once per cycle", Step 3e "On a failure: fix the code and re-run this same Step 3e" | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | Verified |
| `skills/python-test-and-fix/workflow.md` | Step 10 Impact-Based Execution | Change the example commands from `--testmon -m ...` to `--testmon-forceselect -m ...`, add the note that `-m` deactivates plain `--testmon` selection | `REQ-005`; AC-5, AC-6 | (checked in Step 3) `skills/python-test-and-fix/workflow.md` Step 10 code block `uv run pytest --testmon -m "not integration and not production_paths_allowed" tests/`; measured: `testmon: selection automatically deactivated because -m was used` against `tests/tools/test_check_workitem_structure.py`, while `--testmon-forceselect -m ...` reported `7 deselected` | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | Verified |
| `skills/python-test-and-fix/SKILL.md` | Phase overview row 10 | Align row 10 ("Leverage `pytest-testmon` if available") with the corrected Step 10 | `REQ-005`; AC-5, AC-6 | (checked in Step 3) `skills/python-test-and-fix/SKILL.md` Phase overview row `| 10 | Impact-based execution |` | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | Verified |

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
| `rules/toolchain.md` | Defines the validation sequence, the coverage threshold, and the diff-cover command that stay unchanged | `REQ-002`, `REQ-003` |
| `rules/ai-execution.md` | Repository Tool Usage item 8 (non-empty target and collected-test confirmation) stays intact | `REQ-001`, `REQ-002` |
| `routing.md` | Its Tools table lists the routing checkers that Step 3e applies and that this Plan must not weaken | `REQ-002` |
| `pyproject.toml` | Declares `pytest-testmon>=2.1`, the pytest markers (`integration`, `production_paths_allowed`), and `addopts` | `REQ-001`, `REQ-005` |
| `tests/conftest.py` | The production-isolation guard and the `production_paths_allowed` marker that the `-m` filter excludes | `REQ-001` |
| `tools/check_skills_references.py` | Defines what reference text the checker accepts | `REQ-001` to `REQ-005` |
| `tools/check_skills_heading_cycles.py` | Defines the heading-cycle condition the new references must not trigger | `REQ-001` to `REQ-005` |

## Acceptance Criteria
- AC-1 (`REQ-001`): Step 4 names `--testmon-forceselect -m "not integration and not production_paths_allowed"` as the iteration
  test command, states the condition and recorded reason for the fallback, and no longer says "when available" — verified by
  reading and by running the stated command once.
- AC-2 (`REQ-002`): Step 3e's on-failure path and Step 4 name which validators re-run per fix family, when the complete
  sequence re-runs, and the "every validator passed against the final content" meaning of "Completed when" — verified by
  reading.
- AC-3 (`REQ-003`): Step 4 states that a full-suite re-run follows a passing targeted run that includes the previously failing
  tests, within the existing Attempt Limit — verified by reading.
- AC-4 (`REQ-004`): Step 3e and Step 4 require a recorded `skipped: {validator} — passed earlier, unaffected by {fix}` note in
  the Execution Status Notes — verified by reading.
- AC-5 (`REQ-001` to `REQ-005`): no gate is weakened: the single per-cycle full-suite gate, the 90% `diff-cover` threshold,
  the Attempt Limit wording, the Failure Log, and the Repository Tool Usage item 8 confirmations are unchanged, and nothing
  under `rules/` or `routing.md` changed — verified by `git diff`.
- AC-6 (`REQ-001` to `REQ-005`): `uv run python tools/check_skills_references.py` and
  `uv run python tools/check_skills_heading_cycles.py` exit 0.
- AC-7 (`REQ-001`, `REQ-002`, `REQ-003`; outcome, measured by the user, see UNK-03): in a comparable post-change cycle the
  iteration test runs use `--testmon-forceselect` (observable in the tool calls), full-suite runs per cycle do not exceed 1
  plus 1 per distinct full-suite failure attempt, and total `pytest` time per cycle is below the 3.0 minutes baseline.

## Tests
- Unit tests: `N/A: instruction-only change; no code behavior changes` (all `REQ`).
- Run the corrected iteration command (`uv run pytest --testmon-forceselect -m "not integration and not production_paths_allowed"
  <targeted test file>`) on a cold and a warm `.testmondata`, and confirm the warm run deselects unchanged tests (`REQ-001`,
  `REQ-005`); this was done once during planning against `tests/tools/test_check_workitem_structure.py`.
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` (`REQ-001` to
  `REQ-005`).
- Before/after measurement over at least one real `code-implementation` cycle (`REQ-001`, `REQ-002`, `REQ-003`; AC-7) —
  blocked on UNK-03 for method and baseline.

## Documentation Impact
`N/A: instruction-only change under skills/; no docs/*.md requires an update, and routing.md is not touched because its tool
inventory already lists pytest --testmon.`

## Assumptions
- `--testmon-forceselect` with the repository's `-m` filter is the selector that works: measured during planning,
  `--testmon -m ...` reported "selection automatically deactivated because -m was used" while
  `--testmon-forceselect -m ...` reported "7 deselected" on an unchanged tree (`pytest-testmon` 2.2.0, `pytest` 9.0.3).
- The scoped-re-validation conflict with Step 3e's "Completed when: all of the above pass" is resolved by an operational
  definition rather than left open: a validator counts as passed when it passed against the final content of the files it
  examines, and a validator whose inputs the fix did not change keeps its earlier pass (REQ-002); the issue left this to the
  Plan.
- The Step 4 full-suite run (`uv run coverage run -m pytest tests/`) stays separate from testmon: testmon collection is forced
  off under `coverage`, so the single per-cycle full run cannot feed `.testmondata`.
- Step 8b overlap check (`tools/check_plan_target_overlaps.py`, run at freeze) reported `skills/code-implementation/workflow.md`
  as also targeted by perf001's Plan; judged **compatible** (perf001 edits `## Multi-file processing`, this Plan edits Step 3e
  and Step 4) with a re-anchor sequencing dependency noted in Scope.
- The Step 0 load set is unchanged (user decision 2026-10-24).
- Re-judged at `plan-to-implementation-procedure` Step 2 (2026-10-24, `tools/check_plan_target_overlaps.py`):
  `skills/code-implementation/workflow.md` is also targeted by `plans/20261024-233356_cut-blocking-question-waits.md` (perf005:
  new `## Question policy` section and a Final Report line) and the archived perf001 Plan (`## Multi-file processing`).
  Judged **sequencing dependency, compatible**: this Plan edits Step 3e and Step 4 only; the later-applied Plan re-anchors.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Why `--testmon` was never called in the measured cycles: runtime works here (cold run succeeded, warm run deselected), and the cause is not reproducible from the local opencode DB (0 testmon calls among 131 pytest commands in 9 sessions, 2026-06 to 2026-08), so the historical cause (instruction ambiguity versus the `-m` deactivation in the documented command forms) is unconfirmed | The measured 186 cycles' sessions | None needed to implement: the Plan removes both candidate causes (explicit selector, no "when available") | False |
| UNK-02 | Cost and validity of the first testmon run in a checkout: a cold `.testmondata` makes the first run select everything, and `.testmondata` is one file shared by every session in the repository root (`skills/python-test-and-fix/workflow.md` Step 10 states that concurrent corruption was not verified) | Cold-run duration on the full suite; behavior under concurrent sessions | Measure the first cold run during implementation; keep the `pgrep` pre-check that `skills/python-test-and-fix/workflow.md` Step 10 already requires before runs that use shared artifacts | False |
| UNK-03 | How AC-7 is measured: the issue's figures (186 cycles, 3.0 min `pytest` per cycle) are not reproducible from the local opencode DB (131 pytest commands in 9 sessions, newest session 2026-08-21), and the harness of the post-change cycle is unknown | The DB or host the investigation used; the harness for post-change cycles; the baseline cycle | User names the harness and the comparable cycle; otherwise take a fresh baseline before AC-7 is judged | False |
| UNK-04 | perf001 (Plan archived in `plans/done/`, procedures unexecuted) and perf005 (Frozen Plan `plans/20261024-233356_cut-blocking-question-waits.md`) edit `skills/code-implementation/workflow.md` | Their completion order | Re-read the file and re-anchor each edit when applied after a sibling | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `skills/code-implementation/workflow.md` | Modify | Medium (referenced from 3 repository files; read by every `code-implementation` cycle) | 13 | High (one author) | not applicable (rsynced) |
| `skills/python-test-and-fix/workflow.md` | Modify | Low (referenced from 4 repository files; the Step 10 commands are cited by `skills/code-implementation/workflow.md` Step 4) | 5 | High (one author) | not applicable (rsynced) |
| `skills/python-test-and-fix/SKILL.md` | Modify | Low (referenced from 3 repository files; one table row) | 6 | High (one author) | not applicable (rsynced) |

## Design
- **Selector decision**: `--testmon-forceselect` with the `-m` safety filter. Alternatives considered: (1) keep plain
  `--testmon tests/` as the workflow states today — rejected: it has no `-m`, so it also runs `integration` and
  `production_paths_allowed` tests that the repository excludes for safety, and any `-m` added to it deactivates the selection;
  (2) `--testmon -m ...` as `skills/python-test-and-fix/workflow.md` Step 10 writes it — rejected: measured to deactivate
  selection (it runs everything); (3) `--testmon-noselect` — rejected: it deselects nothing. Compatibility impact: none for
  other callers; the corrected command is stricter and narrower. Reversibility: a documentation revert.
- **Why correcting `python-test-and-fix` is in scope**: the issue lists it "if the policy needs the same strengthening"; the
  measurement shows its documented example is wrong, and the code-implementation workflow cites its Step 10, so leaving it would
  re-introduce the defect.
- **Scoped re-validation, defined**: validators re-run by fix family (formatting or lint: `ruff`; type: `mypy` and `ruff`; import:
  `lint-imports`, `mypy`, `ruff`; security: `bandit` and `ruff`); the complete sequence re-runs when a fix spans families or
  changes imports or public signatures. This generalizes the cross-family rule that Step 4 already states for a fix that touched
  formatting, typing, or imports. "Completed when: all of the above pass" is read as "every validator passed against the final
  content of the files it examines", which a scoped re-run satisfies; the unchanged earlier pass is recorded, not assumed.
- **Existing bounds, as found**: Step 4 already limits the full suite to once per cycle plus the Attempt Limit (3 attempts) for an
  ordinary failure, so the measured 22 full runs in 6 cycles violate the written rule; the change closes the practical gap
  (targeted run first) rather than adding a new limit.
- **Corrected issue wording**: `pytest-testmon` is declared as `>=2.1` in `pyproject.toml` (2.2.0 is the installed version, not the
  declared one).

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Correct the testmon commands in the test skill**
   - [ ] Re-read the current `skills/python-test-and-fix/workflow.md` Step 10 (re-anchor: another session edited it recently),
     change the example commands to `--testmon-forceselect -m ...`, and add the note that `-m` deactivates plain `--testmon`
     selection (`REQ-005`; `skills/python-test-and-fix/workflow.md`).
   - [ ] Align Phase overview row 10 in `skills/python-test-and-fix/SKILL.md` (`REQ-005`; `skills/python-test-and-fix/SKILL.md`).
2. **Phase 2: Update the code-implementation workflow**
   - [ ] Re-read `skills/code-implementation/workflow.md` (re-anchor if perf001 or perf005 changed it) and update Step 4's
     iteration test command and fallback (`REQ-001`; `skills/code-implementation/workflow.md`).
   - [ ] Add the scoped re-validation wording to Step 3e's on-failure path and Step 4's fix-then-rerun path, with the definition
     of "Completed when" (`REQ-002`; `skills/code-implementation/workflow.md`).
   - [ ] Add the targeted-before-full rule and the skipped-run audit note (`REQ-003`, `REQ-004`;
     `skills/code-implementation/workflow.md`).
3. **Phase 3: Verification and deployment check**
   - [ ] Run the corrected iteration command once on a cold and a warm `.testmondata` after the `pgrep` pre-check, and record the
     cold-run duration for UNK-02 (`REQ-001`, `REQ-005`; `skills/python-test-and-fix/workflow.md`,
     `skills/code-implementation/workflow.md`).
   - [ ] Run both skills checkers and confirm by `git diff` that no gate, threshold, or Attempt Limit text changed and nothing
     under `rules/` or `routing.md` changed (`REQ-001` to `REQ-005`; all three files).
   - [ ] Deployment check: no `scripts/` or `config/` file changes, so no deploy hand-off is needed (all three files: `deploy.sh
     Impact` is `not applicable (rsynced)`).
   - [ ] Hand AC-7's measurement to the user once UNK-03 is resolved (`REQ-001`, `REQ-002`, `REQ-003`;
     `skills/code-implementation/workflow.md`).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `skills/code-implementation/workflow.md` | Structural plus command check: the new iteration command deselects on a warm DB | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py`; `uv run pytest --testmon-forceselect -m "not integration and not production_paths_allowed" <targeted test file>` run twice | Checkers exit 0; the second run reports deselected tests |
| `skills/python-test-and-fix/workflow.md` | Same command check against the corrected examples | Same two checkers; the same pytest command | Both exit 0; examples match the measured behavior |
| `skills/python-test-and-fix/SKILL.md` | Wording consistency with Step 10 | Same two checkers | Both exit 0 |
| All three files | Regression of gates | `git diff` over the three files and `rules/`, `routing.md` | No gate, threshold, or Attempt Limit text changed; `rules/` and `routing.md` untouched |
| Cycle outcome (AC-7) | Before/after measurement, user-run | Session tool-call counts and `pytest` time per cycle | `--testmon-forceselect` used; full runs at most 1 plus 1 per failure attempt; `pytest` time below 3.0 min |

## Risks
- **Risk**: The first testmon run on a cold `.testmondata` selects everything, so a cycle's first iteration run costs as much as a
  full run → **Mitigation**: the database persists across cycles (gitignored, repository root), so the cost is paid once; UNK-02
  records the cold-run duration.
- **Risk**: One `.testmondata` is shared by every session, and concurrent runs may corrupt it (not verified) → **Mitigation**:
  keep the `pgrep` pre-check `skills/python-test-and-fix/workflow.md` Step 10 requires; fall back to the mirrored-path selection
  and record the reason if the database is unusable.
- **Risk**: A comment-only edit is not detected by testmon (measured: appending a comment to a source file left "changed files:
  0"), and testmon selects by function-level dependency data, so a changed non-Python input (a config file a test reads) may not
  select its tests → **Mitigation**: testmon narrows only iteration runs; the single full-suite run still runs everything
  (AC-5).
- **Risk**: Scoped re-validation lets an affected validator be skipped by a wrong "unaffected" judgement →
  **Mitigation**: the family table in REQ-002, the full-sequence re-run for cross-family or import changes, and the recorded
  skip note (REQ-004) that makes each skip reviewable.
- **Risk**: `skills/code-implementation/workflow.md` is high-churn (13 commits in 30 days) and perf001 and perf005 edit it →
  **Mitigation**: re-read the current file before each edit and re-anchor (UNK-04).
- **Risk**: The measured reduction cannot be shown because the issue's figures are not reproducible from the local DB →
  **Mitigation**: UNK-03 resolution before AC-7; AC-1 to AC-6 do not depend on it.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the testmon commands in `skills/python-test-and-fix/workflow.md` and `skills/python-test-and-fix/SKILL.md` | Completed | — | 20261025-003438 |  |
| 2 | Update Steps 3e and 4 of `skills/code-implementation/workflow.md` | Completed | — | 20261025-003438 |  |
| 3 | Verification, regression review, and deployment check | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261024-235802_01_skills_code-implementation_workflow.md.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261024-235802_02_skills_python-test-and-fix_workflow.md.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261024-235802_03_skills_python-test-and-fix_SKILL.md.md` | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261024-203550_perf004_bound-verification-sequence-cost.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261024-233036
- **Related target files**: skills/code-implementation/workflow.md; skills/python-test-and-fix/workflow.md; skills/python-test-and-fix/SKILL.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue `Implementation Intent` (first bullet) and `Required Changes` (testmon as the iteration path); measured selector behavior (`testmon: selection automatically deactivated because -m was used`) | skills/code-implementation/workflow.md | Phase 2 | AC-1, AC-5, AC-6 | Corrected command run on a cold and warm DB; both skills checkers | Confirmed by repository evidence |
| REQ-002 | Issue `Implementation Intent` (scoped validators) and `Required Changes` (scoped-re-validation wording); `skills/code-implementation/workflow.md` Step 3e and Step 4 | skills/code-implementation/workflow.md | Phase 2 | AC-2, AC-5, AC-6 | Read of the changed Steps; both skills checkers | Derived from confirmed evidence |
| REQ-003 | Issue `Implementation Intent` (second bullet); `skills/code-implementation/workflow.md` Step 4 | skills/code-implementation/workflow.md | Phase 2 | AC-3, AC-5, AC-6 | Read of Step 4; both skills checkers | Explicit in issue |
| REQ-004 | Issue `Implementation Intent` (third bullet, record skipped runs) | skills/code-implementation/workflow.md | Phase 2 | AC-4, AC-5, AC-6 | Read of Step 3e and Step 4; both skills checkers | Explicit in issue |
| REQ-005 | Issue `Target Files or Areas` (`python-test-and-fix` Step 10 "if the policy needs the same strengthening"); measured selector behavior | skills/python-test-and-fix/workflow.md | Phase 1 | AC-5, AC-6 | Corrected command run; both skills checkers | Confirmed by repository evidence |
| REQ-005 | Same | skills/python-test-and-fix/SKILL.md | Phase 1 | AC-5, AC-6 | Both skills checkers; wording review | Confirmed by repository evidence |