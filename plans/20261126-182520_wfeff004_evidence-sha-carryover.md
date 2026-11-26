## Goal
- Let a later phase skip the re-read of a file that was already verified, by recording the commit SHA at which a Plan's evidence was verified and adding a read-only tool that reports, with `git`, which files changed, are uncommitted, or are not covered since that SHA; a changed, uncommitted, or unrecorded file keeps today's full verification.

## Priority
Medium

## Scope
- **In-Scope**:
  - `tools/check_evidence_freshness.py` (new): `check` (report the freshness of the files a Plan or procedure cites) and `record` (print the Traceability line to write, refuse when a cited file is uncommitted).
  - `tests/tools/test_check_evidence_freshness.py` (new): unit tests on temporary git repositories.
  - The recording format: one `Evidence revision` line in the Plan's `## Traceability` section (`templates/plan.md`), with the file set derived from the Plan itself.
  - The skip rule in `rules/ai-execution.md` Adversarial Verification (Base), and one short reference each in `skills/issue-to-plan/workflow.md`, `skills/plan-to-implementation-procedure/workflow.md`, and `skills/code-implementation/workflow.md`.
  - `tools/TOOL_DESCRIPTIONS.md`.
- **Out-of-Scope**:
  - What is verified, `tools/stale_detector.py`, and the target-file revalidation steps (kept as they are).
  - Caching verification results outside the repository.
  - Registration in `rules/tool-gates.md` (size ceiling; the tool is named by the workflows) and any hook, gate, or CI step.
- **Dependencies**: N/A: none.

## Background
- Source: the review of the issue-to-implementation flow, issue wfeff004. Step 2/3 adversarial verification against current source and by experiment:
  - Confirmed: `skills/issue-to-plan/workflow.md` has a "Same-cycle dedup" rule (line 147) that already uses path-scoped `git status --short -- <path>` and `git log -1 --format=%H -- <path>`; it covers one cycle only. `skills/plan-to-implementation-procedure/workflow.md` Step 3a and `skills/code-implementation/workflow.md` Step 3a re-verify claims, as `rules/ai-execution.md` "Adversarial Verification (Base)" (line 78) requires; no workflow records a revision, and a Plan's evidence cells end with `(checked in Step N)`.
  - Confirmed: `tools/check_workitem_traceability.py` reads only the Traceability fields in `SOURCE_FIELD_NAMES` and `Related target files`, so an extra field is ignored; `tools/_workitem_leftover_rules.py` reports a whole-value `{...}` Traceability value, so an unfilled placeholder in the template is caught.
  - Git primitives, measured (Step 3): `git diff --name-only <sha> HEAD -- <paths>` lists committed changes including added and deleted files; `git status --porcelain=v1 -- <paths>` lists working-tree and untracked changes and prints nothing for ignored files; `git cat-file -e <sha>:<path>` tells whether a file existed at the revision; an unknown SHA is `fatal: Not a valid object name`. Two `git` calls per check are enough for any number of paths.
  - Size constraints (Step 3): four target files sit at their `tools/check_skill_size_baseline.txt` ceilings, so every edit must be size neutral: `rules/ai-execution.md` 17031 B (ceiling 17031), `skills/plan-to-implementation-procedure/workflow.md` 34876 B (34876), `skills/code-implementation/workflow.md` 42113 B (42118), `skills/issue-to-plan/workflow.md` 42530 B (42540). `templates/plan.md` is 12144 B (default limit 16384).
  - Cost claim: the largest recent Plan had 38 target rows; the three phases each re-read the same files. The saving depends on how often a repository moves between phases, which is not measured here.

## Problem
- The same unchanged files are read again in every phase, and nothing recorded lets a later phase prove that they did not change.

## Reason for Change
- Time and token cost grows with the number of target rows. Efficiency without lowering the verification standard; not urgent.

## Implementation Intent
- Make evidence content-addressed: one recorded revision, a file set derived from what the Plan already cites, and a read-only freshness check; any file that is changed, uncommitted, or not covered is verified in full as today.

## Requirements
- `REQ-001`: A Plan MUST record the revision at which its evidence was verified as one `Evidence revision` line in `## Traceability`; the file set it covers MUST be derived from the Plan (backticked repository paths in the Plan, with `:LINE` suffixes removed) plus any extra paths named with `--also`, so a Plan does not grow by a per-claim list.
- `REQ-002`: `tools/check_evidence_freshness.py check` MUST report, for a Plan or a procedure (a procedure uses the revision of its `Source plan`), every cited file that is changed since the revision, uncommitted, or unrecorded, and MUST exit 1 when there is at least one and 0 when all are unchanged; a missing revision, an unknown SHA, or an unreadable document MUST exit 2 so the phase verifies in full.
- `REQ-003`: `tools/check_evidence_freshness.py record` MUST print the line to write and refuse (exit 1) when a cited file has an uncommitted change, so the recorded revision never covers unverified working-tree text.
- `REQ-004`: `rules/ai-execution.md` Adversarial Verification (Base) MUST state the skip rule: a claim may be cited as verified at the recorded revision only when every file it names is reported unchanged; a changed, uncommitted, unrecorded, or tree-wide-search claim is verified in full; and the rule MUST NOT apply to a new claim.
- `REQ-005`: `skills/issue-to-plan/workflow.md`, `skills/plan-to-implementation-procedure/workflow.md`, and `skills/code-implementation/workflow.md` MUST each reference the rule and the tool in one short statement (the issue-to-plan one also records the line), and `templates/plan.md` MUST carry the field; none of the four files may grow past its size ceiling.
- `REQ-006`: `tools/TOOL_DESCRIPTIONS.md` MUST describe the tool, and a documented dry run on one existing Plan MUST be recorded in the implementation procedure's Notes.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/check_evidence_freshness.py` | Create: `check` and `record` subcommands over `git` | No tool compares a recorded revision with the repository; the same-cycle dedup uses raw `git` commands | REQ-001, REQ-002, REQ-003; AC-01 to AC-05 | `issue-to-plan/workflow.md:147` uses path-scoped `git status` and `git log`; the primitives were run in Step 3 | `tests/tools/test_check_evidence_freshness.py` | Verified |
| `tests/tools/test_check_evidence_freshness.py` | Create: tests on temporary git repositories | The tool is defined by its behavior on committed, uncommitted, and unrecorded files | REQ-001 to REQ-003; AC-01 to AC-05 | `tests/tools/` holds one test file per tool | `tests/tools/test_check_evidence_freshness.py` | Verified |
| `templates/plan.md` | Modify: add the `Evidence revision` field to `## Traceability` and one sentence on the evidence convention | The Plan has nowhere to record the revision | REQ-001, REQ-005; AC-06 | Traceability block of the template (checked in Step 3); extra fields are ignored by `check_workitem_traceability.py` | `uv run python tools/check_workitem_structure.py --kind plan` | Verified |
| `rules/ai-execution.md` | Modify: add the skip rule to Adversarial Verification (Base), size neutral | The base rule requires verification and has no unchanged-since case | REQ-004; AC-07 | Section at line 78; 17031 B equals its ceiling | `uv run python tools/check_skill_size.py` | Verified |
| `skills/issue-to-plan/workflow.md` | Modify: record the line in Step 7 and extend the same-cycle dedup pointer, size neutral | issue-to-plan is the phase that writes the evidence | REQ-005; AC-06, AC-08 | Same-cycle dedup at line 147; 42530 B against 42540 B | `uv run python tools/check_skill_size.py` | Verified |
| `skills/plan-to-implementation-procedure/workflow.md` | Modify: one statement in Step 3a, size neutral | Step 3a re-verifies the Plan's claims every time | REQ-005; AC-08 | Step 3a text read in Step 3; 34876 B equals its ceiling | `uv run python tools/check_skill_size.py` | Verified |
| `skills/code-implementation/workflow.md` | Modify: one statement in Step 3a, size neutral | Step 3a re-verifies the procedure's claims every time | REQ-005; AC-08 | Step 3a at line 289; 42113 B against 42118 B | `uv run python tools/check_skill_size.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Modify: Index row and a detail row for the tool | The sync check requires every tool to be listed | REQ-006; AC-09 | `tools/check_tool_descriptions_sync.py` | `uv run python tools/check_tool_descriptions_sync.py` | Verified |

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
  `Implementation steps` in backticks: `tools/close_procedures_batch.py` and the companion check read
  only backticked paths. `uv run python tools/backtick_plan_related_tests.py plans/{filename}.md`
  normalizes a Plan, and `tools/check_workitem_structure.py` reports a plain path
  (`plain-path-citation`).

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/check_workitem_traceability.py` | Reads only the named Traceability fields, so the new field is ignored; the `Source plan` resolution the tool reuses for procedures | REQ-001, REQ-002 |
| `tools/_workitem_leftover_rules.py` | Reports a whole-value `{...}` Traceability value, which covers the template placeholder | REQ-001 |
| `tools/_workitem_citation_check.py` | The backticked-path reading the derived file set follows | REQ-001 |
| `tools/amend_plan.py` | Adds a target row after freeze; the recorded revision must not be refreshed by it (D-5) | REQ-001 |
| `tools/stale_detector.py` | Kept as it is; the freshness check complements it | REQ-004 |
| `tools/check_skill_size_baseline.txt` | Ceilings that bound four target files | REQ-004, REQ-005 |
| `tools/compare_test_baseline.py` | The model of a small tool with a text report and exit codes 0, 1, 2 | REQ-002 |

## Acceptance Criteria
- `AC-01` (REQ-002): On a temporary repository, a recorded revision with no later change reports every cited file unchanged and exits 0; a file changed in a later commit, a file with a working-tree or staged change, an untracked cited file, and a deleted file are each reported with their status and exit 1.
- `AC-02` (REQ-002): A file that does not exist at the revision and still does not exist (a file the Plan creates) is unchanged; a file created after the revision is reported.
- `AC-03` (REQ-002): A path given with `--also` that the Plan does not cite is reported `unrecorded`; a missing `Evidence revision`, an unknown SHA, and an unreadable document exit 2; a procedure resolves the revision through its `Source plan` (also under `plans/done/`).
- `AC-04` (REQ-001): The cited set is every backticked repository path of the Plan with `:LINE` and `:LINE-LINE` suffixes removed; globs, placeholders, commands, and pytest ids are not paths.
- `AC-05` (REQ-003): `record` prints `- **Evidence revision**: <40-hex SHA>` for the current `HEAD` and exits 1, naming the files, when a cited file is uncommitted.
- `AC-06` (REQ-001, REQ-005): `templates/plan.md` has the field and the sentence; a Plan carrying a real SHA gives no new finding in `uv run python tools/check_workitem_structure.py` and `tools/check_workitem_traceability.py`.
- `AC-07` (REQ-004): The rule is in Adversarial Verification (Base), applies only to unchanged-since claims, and excludes new claims, changed or uncommitted or unrecorded files, and tree-wide search claims.
- `AC-08` (REQ-005): The three workflows each reference the rule and the tool in one statement; `uv run python tools/check_skill_size.py` passes with no ceiling raised.
- `AC-09` (REQ-006): `uv run python tools/check_tool_descriptions_sync.py` passes, and a dry run of `check` on one archived Plan with a recorded revision (made for the test, outside the repository) is recorded in the procedure Notes.

## Tests
- T-01 (REQ-001 to REQ-003, AC-01 to AC-05): tests on temporary git repositories (`git init` in `tmp_path`, deterministic identity through `-c` options): unchanged, committed change, staged and unstaged change, untracked, deleted, created-after, created-and-still-absent, `--also` unrecorded, missing revision, unknown SHA, procedure through `Source plan`, `:LINE` stripping, `record` refusal. Write first and confirm they fail.
- T-02 (REQ-001, AC-06): the structure and traceability checkers on a Plan text with the field.
- T-03 (REQ-004, REQ-005, AC-07, AC-08): `uv run python tools/check_skill_size.py` and the reading of the changed rule files.
- T-04 (REQ-006, AC-09): `uv run python tools/check_tool_descriptions_sync.py` and the dry run.
- Run ruff format and check, mypy (CI invocation), and bandit on the tool and its test (the tool starts `git` through `subprocess`: justified `# nosec` comments as in `tools/amend_plan.py`); `tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`; the full suite once, compared with `tools/compare_test_baseline.py`.

## Documentation Impact
Yes. `templates/plan.md`, `rules/ai-execution.md`, the three workflows, and `tools/TOOL_DESCRIPTIONS.md`.

## Assumptions
- A Plan is written before it is committed, so the recorded revision is `HEAD` while the cited files are clean; `record` enforces the clean condition. Commits by another session between verification and recording are a residual risk (R-03).
- The set derived from a Plan (its cited paths) is the set of files its claims depend on, because a claim names the files it relies on in its evidence cell; a dependency a claim does not name is unrecorded by construction and verified in full.
- A procedure uses the Plan's revision: its claims were verified at or after it, so a file unchanged since the Plan's revision is unchanged at the procedure's.
- A shallow or partial clone may not contain the recorded SHA; the tool then exits 2 and the phase verifies in full (fail closed).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the owner accepts the recording format of D-1 (one revision line, derived file set), as the issue asks to "propose the recording format first and stop for confirmation" | The owner has not seen the format | This Plan is the proposal: the owner confirms or changes D-1 before `plan-to-implementation-procedure` runs; no procedure is generated by this cycle | False |
| UNK-02 | How much time and token cost the skip saves in practice | No measurement of repository movement between phases | The documented dry run reports the unchanged share for one Plan; a saving below the cost of reading the report is a reason to drop the rule | False |
| UNK-03 | Whether a claim that depends on a file it does not name occurs often | Evidence cells were not audited | The rule makes such a claim "unrecorded" and verified in full, so it costs nothing in correctness | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/check_evidence_freshness.py` | Create | Low (standalone, no importer) | N/A (new) | N/A (new) | not applicable (tools/ is not deployed) |
| `tests/tools/test_check_evidence_freshness.py` | Create | Low | N/A (new) | N/A (new) | not applicable |
| `templates/plan.md` | Modify | High (read by `issue-to-plan` and the leftover rule at run time) | measured by the procedure | measured by the procedure | not applicable |
| `rules/ai-execution.md` | Modify | High (base rule of every workflow) | measured by the procedure | measured by the procedure | not applicable |
| `skills/issue-to-plan/workflow.md` | Modify | High | measured by the procedure | measured by the procedure | not applicable |
| `skills/plan-to-implementation-procedure/workflow.md` | Modify | High | measured by the procedure | measured by the procedure | not applicable |
| `skills/code-implementation/workflow.md` | Modify | High | measured by the procedure | measured by the procedure | not applicable |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Medium | high | 3 or more authors (unverified) | not applicable |

## Design
Path B (eight files, a new module, rule files loaded by every cycle). Analysis: the tool imports only the standard library and `subprocess`; no importer; `lint-imports` contracts (which cover `scripts/`) are not touched; no database, port, or dependency. Churn and bus factor of the existing files are measured by the procedure with `git log --since=30.days` before the edits (the rows say "measured by the procedure" because the counts move daily).

Decisions:
- **D-1 Recording format (the issue's open question; for the owner's confirmation).** One line in the Plan's `## Traceability`: `- **Evidence revision**: <40-hex SHA>`, placed after `Generated at`. The file set is not written out: it is derived from the Plan (backticked repository paths, `:LINE` removed) plus `--also` paths, so a 38-row Plan gains one line. Alternative: a per-claim file list in each evidence cell (accurate per claim but much longer). Rejected for length; the derived set is a superset of every claim's files, so a change reports more than necessary, never less.
- **D-2 Freshness check.** `check <doc>`: read the revision (a procedure through its `Source plan`, also under `plans/done/`); run `git diff --name-only <sha> HEAD -- <paths>` and `git status --porcelain=v1 -- <paths>`; classify each path as `changed`, `uncommitted`, or `unrecorded` (from `--also`), everything else `unchanged`; print the non-unchanged paths and one summary line; exit 1 when any is reported, 0 when none, 2 on unusable input. A path counts unchanged only when its existence at the revision equals its existence now and no commit or working-tree change touched it, so a file the Plan creates stays unchanged while absent.
- **D-3 Recording.** `record <plan>`: print `- **Evidence revision**: <HEAD>` and exit 0 when the cited files are clean; exit 1 naming the uncommitted ones otherwise. The tool writes nothing (read-only); the phase pastes the line.
- **D-4 Skip rule.** In `rules/ai-execution.md`: a claim is cited as verified at the recorded revision only when every file it names is unchanged by the check; any other claim, a claim from a tree-wide search (`rg` over a directory, "no other caller"), and every new claim are verified in full. The base order of verification and the stop rule are unchanged.
- **D-5 Amend.** `tools/amend_plan.py` does not refresh the revision: a refresh would bless claims that were not re-verified. A file it adds is not in the revision's coverage until verified, and is reported as changed or unchanged by the same rules (a new file is reported).
- **D-6 Size.** Each of the four rule files is edited size-neutrally: the added sentence is offset by tightening wording elsewhere in the same file, measured with `wc -c` against the ceiling; if it is impossible, stop and report (no ceiling is raised), as in wfeff002 and wfeff003.
- **D-7 Subprocess.** The tool runs `git` through `subprocess.run` with a fixed argv list and no shell, `check=False`, and a `# nosec B404` / `# nosec B603` justification as `tools/amend_plan.py` does.

Consumer scan: no persisted schema, public API, or shared constant changes (`not applicable`). Predictable fallout: tool inventory pinned by `tools/check_tool_descriptions_sync.py` (row 8); skill size gate (D-6); module size gate for `tools/` `not affected`; the leftover rule reads `templates/plan.md` at run time (the new field is a `{...}` placeholder, reported only when left unfilled).

## Implementation steps
1. **Phase 1: Tests first (REQ-001 to REQ-003)**
   - [ ] Write the tests on temporary git repositories and confirm they fail (REQ-001 to REQ-003; `tests/tools/test_check_evidence_freshness.py`)
2. **Phase 2: The tool (REQ-001 to REQ-003)**
   - [ ] Implement `check` and `record` (REQ-001 to REQ-003; `tools/check_evidence_freshness.py`)
3. **Phase 3: Template, rule, and workflows (REQ-001, REQ-004, REQ-005)**
   - [ ] Add the field and the sentence to the template (REQ-001, REQ-005; `templates/plan.md`)
   - [ ] Add the skip rule, size neutral (REQ-004; `rules/ai-execution.md`)
   - [ ] Record the line in Step 7 and reference the rule, size neutral (REQ-005; `skills/issue-to-plan/workflow.md`)
   - [ ] Reference the rule in Step 3a, size neutral (REQ-005; `skills/plan-to-implementation-procedure/workflow.md`)
   - [ ] Reference the rule in Step 3a, size neutral (REQ-005; `skills/code-implementation/workflow.md`)
4. **Phase 4: Documentation and verification (REQ-006)**
   - [ ] Update the tool descriptions (REQ-006; `tools/TOOL_DESCRIPTIONS.md`)
   - [ ] Run the tests, the validators, the documented dry run, and the full suite once; no deployment step (`tools/` and the rule files are not deployed) (all REQ; `tools/check_evidence_freshness.py`, `tests/tools/test_check_evidence_freshness.py`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_evidence_freshness.py` | Unit tests on temporary git repositories | `uv run pytest tests/tools/test_check_evidence_freshness.py` | Fail first, then pass |
| Changed Python | Format, lint, type, security, size | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit tools/check_evidence_freshness.py -c pyproject.toml`, `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | No new finding |
| Plan field | Structure and traceability | `uv run python tools/check_workitem_structure.py --kind plan`, `uv run python tools/check_workitem_traceability.py --active-only` | No new finding |
| Rule files | Size and inventory | `uv run python tools/check_skill_size.py`, `uv run python tools/check_tool_descriptions_sync.py` | Pass |
| Dry run | One existing Plan with a SHA added in a scratch copy | `uv run python tools/check_evidence_freshness.py check <scratch plan>` | Report recorded in Notes |
| Full suite and coverage | Regression | `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan" --junitxml=<path>`, then `uv run python tools/compare_test_baseline.py <path>`; `uv run coverage xml`; `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | No new failure beyond the known `tests/mcp_servers/git/` ones |

## Risks
- **Risk**: The rule lets a stale claim pass because a dependency was not named (likelihood: medium) → **Mitigation**: the rule skips only claims whose named files are all unchanged; an unnamed dependency is unrecorded and verified in full; tree-wide search claims are always re-run (D-4).
- **Risk**: The recorded revision covers working-tree text that was never committed (likelihood: low) → **Mitigation**: `record` refuses uncommitted files (D-3).
- **Risk**: Another session commits a cited file between verification and recording (likelihood: low) → **Mitigation**: `record` is run immediately after verification in `issue-to-plan` Step 7, and the same-cycle path-scoped check of Step 2 stays; a later phase reports any such change as changed.
- **Risk**: The saving is smaller than the added reading of a report (likelihood: medium) → **Mitigation**: UNK-02; the dry run measures it before the rule is relied on.
- **Risk**: A rule file cannot be edited size-neutrally (likelihood: medium) → **Mitigation**: D-6; stop and report.
- **Risk**: A CI or shallow clone lacks the recorded SHA (likelihood: low) → **Mitigation**: exit 2 and full verification.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Tests first | Pending | — | — | |
| 2 | The tool | Pending | — | — | |
| 3 | Template, rule, and workflows | Pending | — | — | |
| 4 | Documentation and verification | Pending | — | — | |

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
- **Source issue**: issues/20261126-151439_wfeff004_evidence-sha-carryover.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261126-182520
- **Related target files**: tools/check_evidence_freshness.py, tests/tools/test_check_evidence_freshness.py, templates/plan.md, rules/ai-execution.md, skills/issue-to-plan/workflow.md, skills/plan-to-implementation-procedure/workflow.md, skills/code-implementation/workflow.md, tools/TOOL_DESCRIPTIONS.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 1; Unresolved Questions bullet 1 | `templates/plan.md`, `tools/check_evidence_freshness.py` | Phase 2, Phase 3 | AC-04, AC-06 | T-01, T-02 | Derived from confirmed evidence |
| REQ-002 | Required Changes bullet 2; Acceptance Criteria bullets 2 and 4 | `tools/check_evidence_freshness.py` | Phase 2 | AC-01, AC-02, AC-03 | T-01 | Explicit in issue |
| REQ-003 | Constraints bullet 2 | `tools/check_evidence_freshness.py` | Phase 2 | AC-05 | T-01 | Explicit in issue |
| REQ-004 | Required Changes bullet 3; Constraints bullets 1 and 3 | `rules/ai-execution.md` | Phase 3 | AC-07 | T-03 | Explicit in issue |
| REQ-005 | Required Changes bullet 3; Documentation Impact | `skills/issue-to-plan/workflow.md`, `skills/plan-to-implementation-procedure/workflow.md`, `skills/code-implementation/workflow.md`, `templates/plan.md` | Phase 3 | AC-06, AC-08 | T-03 | Explicit in issue |
| REQ-006 | Testing Expectations; Documentation Impact | `tools/TOOL_DESCRIPTIONS.md` | Phase 4 | AC-09 | T-04 | Explicit in issue |
