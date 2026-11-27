## Goal
- Add a read-only orchestration tool `tools/finalize_procedures.py` that runs the procedure acceptance checks for every procedure of a Plan, prints only failures, classifies each `symbol_missing` stale finding with a suggested action, and applies that action only under an explicit flag.

## Priority
Medium

## Scope
- **In-Scope**: the new tool and its unit tests; the `tools/TOOL_DESCRIPTIONS.md` rows; the references in `skills/plan-to-implementation-procedure/workflow.md` (Step 3c and Step 4) and the matching detail in `skills/plan-to-implementation-procedure/workflow-edge.md`, including moving the existing stale-mismatch classification paragraph from the former to the latter to stay within the skill size ceiling.
- **Out-of-Scope**: changing `tools/stale_detector.py`, `tools/check_workitem_structure.py`, `tools/check_workitem_traceability.py`, or `tools/mark_procedure_new_symbols.py`; generating procedure content; the repeated-row generator (a separate Plan).
- **Dependencies**: N/A: none open (the plan-path citation work, wfeff003, is complete and archived; the Plan for wfeff007 shares the size headroom of `skills/plan-to-implementation-procedure/workflow.md`, see Assumptions)

## Background
`skills/plan-to-implementation-procedure/workflow.md` Step 3c requires `tools/stale_detector.py` and `tools/check_workitem_structure.py` per document, and Step 4 requires `tools/check_workitem_traceability.py --plan-coverage` per Plan; Step 3c names `tools/mark_procedure_new_symbols.py` for names a document creates. These were run in loops, and `mark_procedure_new_symbols.py mark --all` marked names that were not code symbols (values, attributes, external library names). Verified in Step 3: `tools/mark_procedure_new_symbols.py:57-70` (`reported_missing_symbols`) parses `Symbol '<name>' not found in source` lines from `tools/stale_detector.py`, and `mark_names` inserts ` (new)` after every unmarked backticked occurrence with no classification.

## Problem
Repeated runs and manual classification of the same findings cost time and tokens, and the classification is easy to get wrong. The Issue also states two things that the repository does not support: that four checks run per document (only three checkers are named in Step 3c and Step 4), and that the Plan coverage check reports counts (on success it prints only `No findings.`).

## Reason for Change
Efficiency; no correctness risk. Not urgent.

## Implementation Intent
A thin orchestrator that runs the three existing checkers unchanged as subprocesses, reports a compact failure list, and suggests (and, with a flag, applies) `(new)` marking or un-backticking for `symbol_missing` findings only, leaving ambiguous names untouched.

## Requirements
- `REQ-001`: For a Plan path the tool finds every procedure whose `Source plan` matches (under `implementations/`, and `implementations/done/` when `--include-done` is given), runs `tools/stale_detector.py {doc}` and `tools/check_workitem_structure.py --file {doc}` per document and `tools/check_workitem_traceability.py --plan-coverage {plan}` once, always with the checkers' default arguments, runs every check even after a failure, and prints only failing rows as `{document} | {tool} | exit {code} | {finding}`.
- `REQ-002`: Each `symbol_missing` finding is classified as `created here` (the name is defined by the same document: a function or class definition, an assignment `NAME = ...` or `name: type`, or a parameter of a function the document defines), `not a code symbol` (the name occurs only inside a quoted literal or as a value token), or `ambiguous` (neither); the suggested action is `add (new)`, `remove backticks`, or `report only`. Other stale finding types are printed unclassified.
- `REQ-003`: With `--apply` the tool performs only the unambiguous actions (`(new)` via `tools/mark_procedure_new_symbols.py:mark_names`, un-backticking by exact backticked occurrence), writes through `tools/_atomic_write.py`, re-runs the checks for the changed documents, and never changes an `ambiguous` name; `--dry-run` prints the diff and writes nothing; without `--apply` no file is written.
- `REQ-004`: When every check passes the tool prints exactly one summary line carrying the procedure count and the Plan's target row count (computed by the tool, because the coverage checker prints no counts) and the coverage exit code.
- `REQ-005`: The result equals running the three tools by hand: the tool never passes `--no-siblings`, `--sibling-order any`, or any option that weakens a check; its exit code is 0 when every check passes, 1 when any fails, 2 on a usage error; each underlying exit code stays visible in its failing row.
- `REQ-006`: `tools/TOOL_DESCRIPTIONS.md` documents the tool; `skills/plan-to-implementation-procedure/workflow-edge.md` holds the mismatch-classification text moved from `skills/plan-to-implementation-procedure/workflow.md` Step 3c plus the tool usage, and `skills/plan-to-implementation-procedure/workflow.md` Step 3c and Step 4 point to the tool, ending at or below its 34876 B ceiling in `tools/check_skill_size_baseline.txt`.

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8b: every row `Verified`; `tools/audit_plan_target_paths.py` and the additional checks passed)

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/finalize_procedures.py` | Create the orchestrator: discover procedures, run the three checkers, classify `symbol_missing`, optional `--apply` | New file; the directory `tools/` exists | `REQ-001`..`REQ-005`; AC-1..AC-6 | `tools/stale_detector.py:1048-1073` `main` prints `result.summary` and returns 1 on a stale result; `tools/mark_procedure_new_symbols.py:57-70` `reported_missing_symbols` and `:90-110` `mark_names`; `tools/check_workitem_traceability.py --plan-coverage` prints `No findings.` and exits 0 on a covered Plan; `tools/_atomic_write.py` helpers (checked in Step 3) | `tests/tools/test_finalize_procedures.py` | Verified |
| `tests/tools/test_finalize_procedures.py` | Create unit tests with synthetic Plans and procedures covering each classification | New file; the directory `tests/tools/` exists; the Issue's Testing Expectations require synthetic procedures per classification | `REQ-001`..`REQ-005`; AC-1..AC-6 | `tests/tools/test_amend_plan.py` is the fixture-Plan pattern; `tests/conftest.py:35` puts `tools/` on `sys.path` (checked in Step 3) | `tests/tools/test_finalize_procedures.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Add the tool's Index row and Work Items row | `tools/check_tool_descriptions_sync.py` fails for an undocumented tool; `amend_plan.py` rows are the placement pattern | `REQ-006`; AC-7 | `tools/check_tool_descriptions_sync.py:_documented_tool_files` reads backticked `*.py` names from this file (checked in Step 3) | `tests/tools/test_finalize_procedures.py` | Verified |
| `skills/plan-to-implementation-procedure/workflow-edge.md` | Add a section for the moved stale-mismatch classification and the tool usage | The detail must live where the size headroom is: this file is 6089 B and has no baseline entry (limit 16384 B) | `REQ-006`; AC-7 | `skills/plan-to-implementation-procedure/workflow-edge.md` headings at lines 8, 32, 42, 55, 78, 88 are the on-demand sections; `tools/check_skill_size_baseline.txt` has no entry for it (checked in Step 3) | `tools/check_skill_size.py` run | Verified |
| `skills/plan-to-implementation-procedure/workflow.md` | Replace the 1207 B stale-mismatch paragraph of Step 3c with a pointer to the edge section and add the tool to Toolchain and Step 4 | The Issue names Step 3c and Step 4; the file is 34853 B against a 34876 B ceiling (23 B headroom), so a plain addition would fail the size gate | `REQ-006`; AC-7 | `skills/plan-to-implementation-procedure/workflow.md` Step 3c lists the mismatch cases (1) to (3) in one paragraph of 1207 B (measured in Step 3); `tools/check_skill_size_baseline.txt` line 15 records 34876 (checked in Step 3) | `tools/check_skill_size.py` run | Verified |

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
| `tools/stale_detector.py` | Output format (`Stale: N mismatch(es)`, `- type: detail`), exit code 1 on a stale result; 41036 B and baselined, so not modified | `REQ-001`, `REQ-002` |
| `tools/check_workitem_structure.py` | `--file` read-only check and its `No findings.` output | `REQ-001` |
| `tools/check_workitem_traceability.py` | `--plan-coverage` semantics and exit codes | `REQ-001`, `REQ-004` |
| `tools/mark_procedure_new_symbols.py` | `reported_missing_symbols`, `mark_names`, the `(new)` marker; reused as a library | `REQ-002`, `REQ-003` |
| `tools/_atomic_write.py` | Atomic write, dry-run diff, and the `--dry-run` option helper | `REQ-003` |
| `templates/implementation-procedure.md` | Section names the classifier scans (`Procedure`, `Method`, `Details`) and the `(new)` rules | `REQ-002` |
| `tools/check_skill_size_baseline.txt` | The 34876 B ceiling for `skills/plan-to-implementation-procedure/workflow.md` | `REQ-006` |
| `tools/check_module_size_tools_baseline.txt` | Confirms the 24576 B tools gate and that the new file has no entry | `REQ-001` |
| `tests/tools/test_amend_plan.py` | Fixture-Plan pattern for the new tests | `REQ-001` |

## Acceptance Criteria
- AC-1 (`REQ-001`, `REQ-004`): A synthetic Plan whose procedures all pass produces exactly one summary line and exit 0.
- AC-2 (`REQ-001`, `REQ-005`): A failing structure check, stale check, or coverage check appears as one row naming the document, tool, and exit code, and the other checks still run.
- AC-3 (`REQ-002`): A name defined by the same document is classified `created here`; a value or an external name is classified `not a code symbol`; a name matching neither is `ambiguous`; a non-`symbol_missing` finding is printed unclassified.
- AC-4 (`REQ-003`): Without `--apply` no file changes; with `--apply` only unambiguous names change, an ambiguous name is untouched, and `--dry-run` writes nothing.
- AC-5 (`REQ-005`): On a real Plan the tool's pass or fail result and exit codes equal running the three tools by hand.
- AC-6 (`REQ-001`): `--include-done` extends discovery to `implementations/done/`; a Plan with no procedures reports that and exits 1.
- AC-7 (`REQ-006`): `check_tool_descriptions_sync.py` and `check_skill_size.py` pass, with `skills/plan-to-implementation-procedure/workflow.md` at or below 34876 B and no rule text lost from the moved paragraph.

## Tests
- `REQ-001`, `REQ-004`: tests with a synthetic Plan, two procedures, and the three checkers run for real against fixtures in a temporary directory (the tool's `--root` option).
- `REQ-002`: one test per classification and one for an unclassified finding type, using synthetic procedures.
- `REQ-003`: tests that `--apply` marks, un-backticks, and leaves `ambiguous` unchanged, that a second run is idempotent, and that `--dry-run` writes nothing.
- `REQ-005`: a documented comparison run on one existing Plan (recorded in the implementation report).
- Tool checks: ruff, mypy, bandit on both new files (`routing.md` "Adding a new tool").

## Documentation Impact
N/A: no `docs/*.md` change. The tool row and the two skill files are target rows (`REQ-006`).

## Assumptions
- The classification lives in the new tool and `tools/mark_procedure_new_symbols.py` stays unchanged (resolves the Issue's open question): the Issue's Target Files list only the new tool, `mark --all` keeps its documented behavior, and the tool reuses `mark_names` as a library.
- The three checkers named in `skills/plan-to-implementation-procedure/workflow.md` Step 3c and Step 4 are the checks to run; the Issue's "four" has no fourth named checker in that file.
- The tool reads `Source plan` matches by path with `plans/` and `plans/done/` treated as the same, as Step 3c's `Already implemented` rule does. Verified in procedure generation Step 3a: `tools/check_workitem_traceability.py:_procedures_of_plan` matches `Source plan` by base name and its discovery includes `done/`, so the coverage check counts archived procedures; the per-document checks run on active procedures by default and on archived ones only with `--include-done`, because `tools/stale_detector.py` on an archived procedure reports `new_target_exists` once its file has been created (observed on `implementations/done/` procedures of an archived Plan).
- The Plan for the repeated-row generator (wfeff007) also edits `skills/plan-to-implementation-procedure/workflow.md` and `tools/TOOL_DESCRIPTIONS.md`; this Plan lands first and frees about 1 KB of headroom there by moving the paragraph, which that Plan relies on.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the lexical `created here` rules misclassify names in real procedures | The rules are defined from the Issue text and the checked procedure format; they are not yet run against the archived procedures | `REQ-005` comparison on an existing Plan; any doubtful name stays `ambiguous`, which is never edited | False |
| UNK-02 | The Issue's "four checks per document" | Only three checkers are named in Step 3c and Step 4 | The tool runs the three; a fourth would be a new Requirement | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/finalize_procedures.py` | Create | Low — new standalone tool; subprocess calls to three unchanged checkers, imports `mark_names` only | N/A (new) | N/A (new) | not applicable (not rsynced) |
| `tests/tools/test_finalize_procedures.py` | Create | Low — new test file | N/A (new) | N/A (new) | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low — read by `tools/check_tool_descriptions_sync.py` | 81 | High (100% single author) | not applicable (not rsynced) |
| `skills/plan-to-implementation-procedure/workflow-edge.md` | Modify | Low — loaded on demand; grows by about 1.5 KB under a 16384 B limit | 1 | High (100% single author) | not applicable (not rsynced) |
| `skills/plan-to-implementation-procedure/workflow.md` | Modify | Medium — loaded by every plan-to-implementation-procedure cycle; size ceiling 34876 B, text removal must be verbatim in the edge file | 11 | High (98% single author) | not applicable (not rsynced) |

## Design
Path B (more than 3 files, a new module). Analysis recorded:
- Architecture (checked in Step 3): the checkers are CLI scripts in `tools/`; `tools/mark_procedure_new_symbols.py` already runs `tools/stale_detector.py` by `subprocess` with `sys.executable`. The orchestrator follows that pattern (subprocess, default arguments) so each tool's exit semantics stay visible, and imports only `mark_names` from the mark tool (the repository convention is `from tools.x import ...` with `sys.path` set when `__package__` is empty, as in `tools/fill_affected_areas.py`).
- Dependency graphing (checked in Step 3): new files have no callers; `tools/TOOL_DESCRIPTIONS.md` is read by `tools/check_tool_descriptions_sync.py`; the two skill files are read by every `plan-to-implementation-procedure` cycle (`workflow.md`) or on demand (`workflow-edge.md`).
- Historical analysis and operational dependencies: churn and bus factor are in `Affected areas`; no MCP server, database, or port is involved.
- Decision (size): `skills/plan-to-implementation-procedure/workflow.md` has 23 B of headroom, so the 1207 B stale-mismatch paragraph of Step 3c moves verbatim to a new `### Step 3c: stale mismatch classification` section of `skills/plan-to-implementation-procedure/workflow-edge.md`, and `workflow.md` keeps a pointer plus the tool reference, in the repository's existing "load workflow-edge.md and follow its ... section" form. `workflow-edge.md` grows by about 1.5 KB (limit 16384 B, no baseline).
- Decision (classification): lexical, conservative, `ambiguous` by default. Its defining patterns are fixed in the procedure and covered by one test each.
- Decision (module size): the tool must stay at or below 24576 B (`check-module-size-tools`); if it grows past about 20000 B the classifier moves to `tools/_procedure_symbols.py` through a fallout amendment.
- Predictable fallout check (checked in Step 3): module size - new file under the gate; pinned counts - no test pins the number of tools (`rg` over `tests/tools/`); tool inventory - the `tools/TOOL_DESCRIPTIONS.md` rows are target rows; generated blocks - not affected; gate entry in `tools/_validation_gate_defs.py` and `rules/tool-gates.md` row - not affected: the tool takes a Plan argument at run time and has no trigger point, like `tools/amend_plan.py`'s ad hoc use.
- Consumer scan and persisted schema check: not applicable (no schema, public API, shared constant, or removed symbol; the moved paragraph keeps its text).
- Validation baseline: `radon` N/A for a new file; `vulture` is not installed (Tool availability guard); `bandit` is run by path on the new files; diff-cover N/A because CI measures `--cov=scripts`, so `tools/` is validated by unit tests.

## Implementation steps
1. **Phase 1: Tool, tests, and inventory**
   - [ ] Create `tools/finalize_procedures.py` (`REQ-001`..`REQ-005`).
   - [ ] Create `tests/tools/test_finalize_procedures.py` (`REQ-001`..`REQ-005`).
   - [ ] Add the Index row and Work Items row to `tools/TOOL_DESCRIPTIONS.md` (`REQ-006`); run ruff, mypy, bandit, `check_tool_descriptions_sync.py`, and the tests.
2. **Phase 2: Add the edge section**
   - [ ] Add `### Step 3c: stale mismatch classification` (moved text verbatim plus the tool usage) to `skills/plan-to-implementation-procedure/workflow-edge.md` (`REQ-006`); run `tools/check_skill_size.py`.
3. **Phase 3: Point from the workflow**
   - [ ] In `skills/plan-to-implementation-procedure/workflow.md` replace the Step 3c paragraph with the pointer, add the Toolchain and Step 4 references (`REQ-006`); run `tools/check_skill_size.py` and confirm the file is at or below 34876 B.
4. **Phase 4: Verification and deployment check**
   - [ ] Run the tool on one existing Plan and compare with the three tools by hand (`REQ-005`; `tools/finalize_procedures.py`).
   - [ ] Deployment: N/A, no `scripts/` or `config/` file changes; `tools/` and `skills/` are not rsynced by `deploy/deploy.sh`.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/finalize_procedures.py` | Unit with synthetic Plans and procedures | `uv run pytest tests/tools/test_finalize_procedures.py` | All tests pass |
| `tools/finalize_procedures.py` | Static checks | `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run bandit` on the file | No findings |
| `tools/finalize_procedures.py` | Size gate | `uv run python -m tools.check_module_size --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | Exit 0 |
| `tools/TOOL_DESCRIPTIONS.md` | Inventory sync | `uv run python tools/check_tool_descriptions_sync.py` | Exit 0 |
| `skills/plan-to-implementation-procedure/workflow.md` | Size ceiling | `uv run python tools/check_skill_size.py` | Exit 0; at or below 34876 B |
| `skills/plan-to-implementation-procedure/workflow-edge.md` | Size and references | `uv run python tools/check_skill_size.py`, `uv run python tools/check_skills_references.py` | Exit 0 |
| `tools/finalize_procedures.py` | Comparison on a live Plan | the tool and the three tools by hand | Same pass or fail and exit codes |

## Risks
- **Risk**: The lexical classifier marks a real symbol as `not a code symbol` and un-backticks it → **Mitigation**: `--apply` is opt-in, un-backticking needs an exact quoted-literal or value-token match, everything else is `ambiguous`, and `--dry-run` shows the diff.
- **Risk**: Moving the Step 3c paragraph drops a rule → **Mitigation**: the move is verbatim, a test or checksum comparison of the paragraph text before and after is part of Phase 3, and `check_skills_references.py` runs.
- **Risk**: `skills/plan-to-implementation-procedure/workflow.md` headroom is shared with the wfeff007 Plan → **Mitigation**: this Plan lands first and shrinks the file; the later Plan measures `wc -c` before editing.
- **Risk**: A future change to the checkers' output format breaks the tool's parsing of the stale finding lines → **Mitigation**: the parsing reuses `reported_missing_symbols`' pattern and a test pins the line format.
- **Risk**: The tool lets a failing check look like a pass → **Mitigation**: every check runs, each exit code is shown, and the summary line is printed only when all exit codes are 0.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the tool, its tests, and the `tools/TOOL_DESCRIPTIONS.md` rows (`tools/finalize_procedures.py`, `tests/tools/test_finalize_procedures.py`, `tools/TOOL_DESCRIPTIONS.md`) | Completed | — | 20261127-101516 |  |
| 2 | Add the edge section (`skills/plan-to-implementation-procedure/workflow-edge.md`) | Completed | — | 20261127-101516 |  |
| 3 | Point from the workflow within the size ceiling (`skills/plan-to-implementation-procedure/workflow.md`) | Completed | — | 20261127-101516 |  |
| 4 | Verify on one existing Plan; deployment check is N/A (`tools/finalize_procedures.py`) | Completed | — | 20261127-101516 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261127-100214_01_tools_finalize_procedures.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261127-100214_02_tests_tools_test_finalize_procedures.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261127-100214_03_tools_TOOL_DESCRIPTIONS.md.md | 1 | Procedure | Completed | — | — |
| implementations/20261127-100214_04_skills_plan-to-implementation-procedure_workflow-edge.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261127-100214_05_skills_plan-to-implementation-procedure_workflow.md.md | 3 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261126-151441_wfeff006_finalize-procedure-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261127-095609
- **Evidence revision**: d711dc777d403ebe0bbee6affb1eb0eafaf726b4
- **Related target files**: `tools/finalize_procedures.py`, `tests/tools/test_finalize_procedures.py`, `tools/TOOL_DESCRIPTIONS.md`, `skills/plan-to-implementation-procedure/workflow-edge.md`, `skills/plan-to-implementation-procedure/workflow.md`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| `REQ-001` | Issue Required Changes 1; `skills/plan-to-implementation-procedure/workflow.md` Step 3c and Step 4 | `tools/finalize_procedures.py` | Phase 1 | AC-1, AC-2, AC-6 | `tests/tools/test_finalize_procedures.py` | Confirmed by repository evidence |
| `REQ-001` | Issue Testing Expectations | `tests/tools/test_finalize_procedures.py` | Phase 1 | AC-1, AC-2, AC-6 | `uv run pytest tests/tools/test_finalize_procedures.py` | Explicit in issue |
| `REQ-002` | Issue Required Changes 2; `tools/mark_procedure_new_symbols.py` lines 57-70 | `tools/finalize_procedures.py` | Phase 1 | AC-3 | `tests/tools/test_finalize_procedures.py` | Derived from confirmed evidence |
| `REQ-002` | Issue Acceptance Criteria 2 | `tests/tools/test_finalize_procedures.py` | Phase 1 | AC-3 | `uv run pytest tests/tools/test_finalize_procedures.py` | Explicit in issue |
| `REQ-003` | Issue Constraints (no edit without a flag) | `tools/finalize_procedures.py` | Phase 1 | AC-4 | `tests/tools/test_finalize_procedures.py` | Explicit in issue |
| `REQ-003` | Issue Constraints | `tests/tools/test_finalize_procedures.py` | Phase 1 | AC-4 | `uv run pytest tests/tools/test_finalize_procedures.py` | Explicit in issue |
| `REQ-004` | Issue Required Changes 3; coverage output checked in Step 2 (prints `No findings.` only) | `tools/finalize_procedures.py` | Phase 1 | AC-1 | `tests/tools/test_finalize_procedures.py` | Derived from confirmed evidence |
| `REQ-005` | Issue Required Changes 4, Constraints, Acceptance Criteria 3 | `tools/finalize_procedures.py` | Phase 1, Phase 4 | AC-2, AC-5 | `tests/tools/test_finalize_procedures.py` | Explicit in issue |
| `REQ-005` | Issue Acceptance Criteria 3 | `tests/tools/test_finalize_procedures.py` | Phase 1 | AC-2, AC-5 | `uv run pytest tests/tools/test_finalize_procedures.py` | Explicit in issue |
| `REQ-006` | Issue Documentation Impact; `tools/check_tool_descriptions_sync.py` | `tools/TOOL_DESCRIPTIONS.md` | Phase 1 | AC-7 | `uv run python tools/check_tool_descriptions_sync.py` | Confirmed by repository evidence |
| `REQ-006` | Issue Target Files; size ceiling evidence | `skills/plan-to-implementation-procedure/workflow-edge.md` | Phase 2 | AC-7 | `uv run python tools/check_skill_size.py` | Derived from confirmed evidence |
| `REQ-006` | Issue Target Files; `tools/check_skill_size_baseline.txt` line 15 | `skills/plan-to-implementation-procedure/workflow.md` | Phase 3 | AC-7 | `uv run python tools/check_skill_size.py` | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261127-100214 -->
