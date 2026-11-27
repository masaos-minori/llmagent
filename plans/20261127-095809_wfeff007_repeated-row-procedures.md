## Goal
- Add a tool `tools/generate_repeated_procedures.py` that writes one implementation procedure document per listed Plan row from a single body template with path placeholders, refusing rows whose `Change Responsibility` differs, so the author writes the shared content once.

## Priority
Low

## Scope
- **In-Scope**: the new tool and its unit tests; the `tools/TOOL_DESCRIPTIONS.md` rows; one pointer in `skills/plan-to-implementation-procedure/workflow.md` Step 3c.
- **Out-of-Scope**: changing the one-document-per-row rule, the lightweight-fill criteria, or `tools/generate_workitem.py` (it is at its size ceiling); running `tools/stale_detector.py` (the orchestrator of the wfeff006 Plan does that); generating row-specific content.
- **Dependencies**: Sequencing only: the size headroom of `skills/plan-to-implementation-procedure/workflow.md` is freed by the finalize-procedure-checks Plan (wfeff006), see Assumptions.
  - **Depends on**: plans/20261127-095609_wfeff006_finalize-procedure-checks.md | phase 3 | that Plan moves a 1207 B paragraph out of `skills/plan-to-implementation-procedure/workflow.md`; without it the file has 23 B of headroom under its size ceiling and this Plan's Step 3c pointer does not fit

## Background
`skills/plan-to-implementation-procedure/SKILL.md` Core Execution Rules require one document per `Implementation Target Files` row. In one session ten configuration procedures differed only by path and were produced with an ad hoc script. Verified in Step 3: `tools/generate_workitem.py` already has `--kind implementation-procedure --all-rows` (`generate_all_rows`, lines 408-456), which writes an empty skeleton for every row with the shared pass timestamp and the row's position as `seq`; it cannot take a subset of rows or a shared body, so the Issue's "one empty document per call" is outdated but the need remains.

## Problem
The shared content is rewritten per document, and an ad hoc script is neither reviewed nor reusable.

## Reason for Change
Token and time cost for large repeated-row Plans; low urgency.

## Implementation Intent
A separate tool that reuses the existing sequence, timestamp, naming, and collision functions of `tools/generate_workitem.py` as a library, keeps each document's own traceability and Execution Status, and refuses any row whose change text could hide a row-specific change.

## Requirements
- `REQ-001`: The tool takes a Plan path, an explicit list of row paths (`--rows`), and a body template file (`--body-template`) whose text may use the placeholders `{path}`, `{name}` (base name), `{seq}`, and `{timestamp}`; it writes one document per row to `implementations/{timestamp}_{seq}_{target_file_slug}.md`, with the Plan's shared pass timestamp (`find_or_record_pass_timestamp`) and the row's 1-indexed position in the table as `seq`, the same values `tools/generate_workitem.py` assigns.
- `REQ-002`: Before writing anything the tool refuses (exit 1, naming the cause) when a listed path is not a row of the Plan, a path is listed twice, an output path or its `done/` counterpart already exists, a placeholder is unknown, or the `Change Responsibility` texts of the listed rows are not identical after replacing each row's own path and base name with `{path}` and `{name}`; no file is written in any refusal case.
- `REQ-003`: Each document ends with a `## Traceability` block filled by the tool from the Plan: Workflow phase `plan-to-implementation-procedure`, Requirement ID from the row's `Related Requirement / Acceptance Criterion` cell, Source issue from the Plan's Traceability, Source plan the Plan path, Source requirement and Source implementation procedure as in `templates/implementation-procedure.md`, Generated at the pass timestamp, Related target files the row path; the template body supplies every section from `## Goal` through `## Execution Status`.
- `REQ-004`: After writing, the tool runs `tools/check_workitem_structure.py --file {document}` on every created document, prints each result, and exits 1 when any fails; `--dry-run` prints the intended paths and writes nothing, including the Plan's timestamp marker.
- `REQ-005`: `tools/TOOL_DESCRIPTIONS.md` documents the tool, and `skills/plan-to-implementation-procedure/workflow.md` Step 3c points to it, ending at or below the 34876 B ceiling of `tools/check_skill_size_baseline.txt`.

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8b: every row `Verified`; `tools/audit_plan_target_paths.py` and the additional checks passed)

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/generate_repeated_procedures.py` | Create the generator: parse rows and change texts, refuse on a mismatch, write one document per row, run the structure check | New file; the directory `tools/` exists; `tools/generate_workitem.py` is 28930 B and baselined at that size in `tools/check_module_size_tools_baseline.txt`, so it cannot take the new code | `REQ-001`..`REQ-004`; AC-1..AC-6 | `tools/generate_workitem.py` `extract_target_file_rows` (line 312), `find_or_record_pass_timestamp` (283), `implementation_procedure_output_path` (235), `check_collision` (265), `extract_fenced_skeleton` (137), `TEMPLATE_IMPLEMENTATION_PROCEDURE` (91) are reusable; `tools/check_workitem_structure.py --file` is the validity check (checked in Step 3) | `tests/tools/test_generate_repeated_procedures.py` | Verified |
| `tests/tools/test_generate_repeated_procedures.py` | Create unit tests with a synthetic Plan of ten rows and the refusal cases | New file; the directory `tests/tools/` exists; the Issue's Testing Expectations require a synthetic Plan | `REQ-001`..`REQ-004`; AC-1..AC-6 | `tests/tools/test_amend_plan.py` is the fixture-Plan pattern; `tests/conftest.py:35` puts `tools/` on `sys.path` (checked in Step 3) | `tests/tools/test_generate_repeated_procedures.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Add the tool's Index row and Work Items row | `tools/check_tool_descriptions_sync.py` fails for an undocumented tool; the `generate_workitem.py` row at line 139 is the nearest sibling | `REQ-005`; AC-7 | `tools/check_tool_descriptions_sync.py:_documented_tool_files` reads backticked `*.py` names from this file (checked in Step 3) | `tests/tools/test_generate_repeated_procedures.py` | Verified |
| `skills/plan-to-implementation-procedure/workflow.md` | Add the Step 3c pointer to the tool (and its Toolchain line) within the size ceiling | The Issue names Step 3c; Step 3c today mentions only the per-call `generate_workitem.py` scaffold | `REQ-005`; AC-7 | `skills/plan-to-implementation-procedure/workflow.md` Step 3c "Optionally scaffold the empty file first" bullet; the file is 34853 B against the 34876 B ceiling in `tools/check_skill_size_baseline.txt` line 15 (checked in Step 3) | `tools/check_skill_size.py` run | Verified |

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
| `tools/generate_workitem.py` | Sequence, timestamp, naming, collision, and skeleton functions to reuse; 28930 B and baselined, so not modified | `REQ-001`, `REQ-002` |
| `tools/check_workitem_structure.py` | The structure check run on each created document | `REQ-004` |
| `templates/implementation-procedure.md` | Required sections and the Traceability field set | `REQ-003` |
| `tools/_atomic_write.py` | Atomic write and the `--dry-run` helper | `REQ-001`, `REQ-004` |
| `tools/check_skill_size_baseline.txt` | The 34876 B ceiling for `skills/plan-to-implementation-procedure/workflow.md` | `REQ-005` |
| `tools/check_module_size_tools_baseline.txt` | Confirms the 24576 B tools gate and the `generate_workitem.py` ceiling | `REQ-001` |
| `tests/tools/test_amend_plan.py` | Fixture-Plan pattern for the new tests | `REQ-001` |

## Acceptance Criteria
- AC-1 (`REQ-001`): A synthetic Plan with ten rows of identical `Change Responsibility` (differing in path only) produces ten documents in one call.
- AC-2 (`REQ-001`): The filenames' timestamp and `seq` equal what `tools/generate_workitem.py --kind implementation-procedure --all-rows` assigns for the same Plan.
- AC-3 (`REQ-002`): A row with a different `Change Responsibility` makes the tool refuse and write nothing; so do an unknown path, a duplicate path, an existing output, and an unknown placeholder.
- AC-4 (`REQ-003`): Every generated document carries the `## Traceability` block with the Plan's Source issue and the row's Requirement ID.
- AC-5 (`REQ-004`): Every generated document passes `tools/check_workitem_structure.py`; a failing one yields exit 1; `--dry-run` writes nothing, including the timestamp marker.
- AC-6 (`REQ-001`, `REQ-002`): A row path that is only a companion test row is accepted only if it is a Plan row; the tool does not merge documents (one file per row).
- AC-7 (`REQ-005`): `check_tool_descriptions_sync.py` and `check_skill_size.py` pass, with `skills/plan-to-implementation-procedure/workflow.md` at or below 34876 B.

## Tests
- `REQ-001`: ten-row synthetic Plan; compare filenames with the `--all-rows` output of `tools/generate_workitem.py` in a temporary copy.
- `REQ-002`: one test per refusal case, each asserting no `implementations/` file and no timestamp marker was written.
- `REQ-003`: assert the Traceability block values against the Plan.
- `REQ-004`: assert structure results are printed and exit 1 on a failing template (a template missing a required section); `--dry-run` leaves the Plan byte-identical.
- Tool checks: ruff, mypy, bandit on both new files (`routing.md` "Adding a new tool").

## Documentation Impact
N/A: no `docs/*.md` change. The tool row and the Step 3c pointer are target rows (`REQ-005`).

## Assumptions
- The tool is separate from `tools/generate_workitem.py` (resolves the Issue's open question): that file is at its baselined size ceiling, so any added code would fail the size gate.
- "Identical `Change Responsibility`" is decided from the Plan text alone by replacing each row's own path and base name with placeholders and comparing whitespace-normalized text, which is decidable without other input.
- This Plan lands after the Plan for wfeff006 (a structured `Depends on` bullet, sequencing only): both edit `skills/plan-to-implementation-procedure/workflow.md` and `tools/TOOL_DESCRIPTIONS.md`; the wfeff006 Plan frees about 1 KB in the first and the two edits do not touch the same lines. The wfeff006 Plan's overlap with this one was judged compatible in Step 8b.
- Companion handling: a listed row is still one document; the tool does not create `### Companion test files` sections, so a companion-eligible test row is simply not listed.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether a Plan whose repeated rows carry the row path inside `Change Responsibility` in a form other than the exact path or base name is refused too often | Only the placeholder substitution rule is defined; real Plans with ten repeated rows are not in the repository to test against | Implementation measures the rule on the archived Plans' tables and reports a rate; a refusal is safe, a false accept is not | False |
| UNK-02 | The state of the sequencing dependency on the wfeff006 Plan | That Plan is not yet implemented | `tools/plan_dependency_order.py` reports it as gated at procedure generation; the owner decides the order | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/generate_repeated_procedures.py` | Create | Low — new standalone tool; imports five functions from `tools/generate_workitem.py`, no existing caller | N/A (new) | N/A (new) | not applicable (not rsynced) |
| `tests/tools/test_generate_repeated_procedures.py` | Create | Low — new test file | N/A (new) | N/A (new) | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low — read by `tools/check_tool_descriptions_sync.py` | 81 | High (100% single author) | not applicable (not rsynced) |
| `skills/plan-to-implementation-procedure/workflow.md` | Modify | Medium — loaded by every plan-to-implementation-procedure cycle; size ceiling 34876 B with 23 B headroom until the wfeff006 Plan lands | 11 | High (98% single author) | not applicable (not rsynced) |

## Design
Path B (more than 3 files, a new module). Analysis recorded:
- Architecture (checked in Step 3): `tools/generate_workitem.py` exposes the needed functions at module level; the new tool imports them (`from tools.generate_workitem import ...`, with the `sys.path` fix when `__package__` is empty, as in `tools/fill_affected_areas.py`) and adds no code to that file. Its `_TABLE_ROW_RE` and `extract_target_file_rows` read only the first cell, so the tool parses the second (`Change Responsibility`) and fourth (`Related Requirement / Acceptance Criterion`) cells itself.
- Dependency graphing (checked in Step 3): new files have no callers; `tools/TOOL_DESCRIPTIONS.md` is read by `tools/check_tool_descriptions_sync.py`; `skills/plan-to-implementation-procedure/workflow.md` is read by every `plan-to-implementation-procedure` cycle.
- Historical analysis and operational dependencies: churn and bus factor are in `Affected areas`; no MCP server, database, or port is involved.
- Decision (all-or-nothing): all refusal checks run before the first write, so a refusal leaves no partial set; the Plan's timestamp marker is the one write `find_or_record_pass_timestamp` makes and it happens only after the refusal checks pass.
- Decision (template ownership): the template body supplies `## Goal` through `## Execution Status`, and the tool owns `## Traceability` because its values are mechanical and per-row.
- Decision (module size): the tool must stay at or below 24576 B (`check-module-size-tools`).
- Predictable fallout check (checked in Step 3): module size - new file under the gate, and `tools/generate_workitem.py` is deliberately untouched; pinned counts - no test pins the number of tools; tool inventory - the `tools/TOOL_DESCRIPTIONS.md` rows are target rows; generated blocks - not affected; gate entry and `rules/tool-gates.md` row - not affected: the tool takes Plan arguments at run time and has no trigger point.
- Consumer scan and persisted schema check: not applicable (no schema, public API, shared constant, or removed symbol).
- Validation baseline: `radon` N/A for a new file; `vulture` is not installed (Tool availability guard); `bandit` runs by path on the new files; diff-cover N/A because CI measures `--cov=scripts`.

## Implementation steps
1. **Phase 1: Tool, tests, and inventory**
   - [ ] Create `tools/generate_repeated_procedures.py` (`REQ-001`..`REQ-004`).
   - [ ] Create `tests/tools/test_generate_repeated_procedures.py` (`REQ-001`..`REQ-004`).
   - [ ] Add the Index row and Work Items row to `tools/TOOL_DESCRIPTIONS.md` (`REQ-005`); run ruff, mypy, bandit, `check_tool_descriptions_sync.py`, and the tests.
2. **Phase 2: Skill pointer**
   - [ ] Add the Step 3c pointer in `skills/plan-to-implementation-procedure/workflow.md` (`REQ-005`); run `tools/check_skill_size.py` and confirm the file is at or below 34876 B.
3. **Phase 3: Deployment check**
   - [ ] Deployment: N/A, no `scripts/` or `config/` file changes; `tools/` and `skills/` are not rsynced by `deploy/deploy.sh`.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/generate_repeated_procedures.py` | Unit with a synthetic Plan | `uv run pytest tests/tools/test_generate_repeated_procedures.py` | All tests pass |
| `tools/generate_repeated_procedures.py` | Static checks | `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run bandit` on the file | No findings |
| `tools/generate_repeated_procedures.py` | Size gate | `uv run python -m tools.check_module_size --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | Exit 0 |
| `tools/TOOL_DESCRIPTIONS.md` | Inventory sync | `uv run python tools/check_tool_descriptions_sync.py` | Exit 0 |
| `skills/plan-to-implementation-procedure/workflow.md` | Size ceiling | `uv run python tools/check_skill_size.py` | Exit 0; at or below 34876 B |

## Risks
- **Risk**: A row-specific change hides in a shared body because two rows' change texts differ only in a way the substitution misses → **Mitigation**: the comparison is exact after substitution, so any other difference refuses; a refusal is safe.
- **Risk**: A partial set of documents is written when a later row fails → **Mitigation**: every refusal check runs before the first write (`REQ-002`), and a test asserts no file exists after each refusal.
- **Risk**: `skills/plan-to-implementation-procedure/workflow.md` has 23 B of headroom until the wfeff006 Plan lands → **Mitigation**: the structured `Depends on` bullet makes `tools/plan_dependency_order.py` report it; Phase 2 measures `wc -c` first and stops when the pointer does not fit.
- **Risk**: The timestamp marker appended to the Plan differs from what `generate_workitem.py` would write → **Mitigation**: the tool calls the same `find_or_record_pass_timestamp`, and a test compares the two.
- **Risk**: Generated documents pass the structure check but contain a stale reference → **Mitigation**: the tool states that `tools/stale_detector.py` is still required; the wfeff006 orchestrator or the manual command covers it.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the tool, its tests, and the `tools/TOOL_DESCRIPTIONS.md` rows (`tools/generate_repeated_procedures.py`, `tests/tools/test_generate_repeated_procedures.py`, `tools/TOOL_DESCRIPTIONS.md`) | Pending | — | — | |
| 2 | Add the Step 3c pointer within the size ceiling (`skills/plan-to-implementation-procedure/workflow.md`) | Pending | — | — | |
| 3 | Deployment check is N/A (`tools/generate_repeated_procedures.py`) | Pending | — | — | |

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
- **Source issue**: issues/20261126-151442_wfeff007_repeated-row-procedures.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261127-095809
- **Evidence revision**: d711dc777d403ebe0bbee6affb1eb0eafaf726b4
- **Related target files**: `tools/generate_repeated_procedures.py`, `tests/tools/test_generate_repeated_procedures.py`, `tools/TOOL_DESCRIPTIONS.md`, `skills/plan-to-implementation-procedure/workflow.md`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| `REQ-001` | Issue Required Changes 1; `tools/generate_workitem.py` lines 283, 235, 312 | `tools/generate_repeated_procedures.py` | Phase 1 | AC-1, AC-2, AC-6 | `tests/tools/test_generate_repeated_procedures.py` | Confirmed by repository evidence |
| `REQ-001` | Issue Acceptance Criteria 1, 3 | `tests/tools/test_generate_repeated_procedures.py` | Phase 1 | AC-1, AC-2, AC-6 | `uv run pytest tests/tools/test_generate_repeated_procedures.py` | Explicit in issue |
| `REQ-002` | Issue Required Changes 2, Acceptance Criteria 2 | `tools/generate_repeated_procedures.py` | Phase 1 | AC-3, AC-6 | `tests/tools/test_generate_repeated_procedures.py` | Derived from confirmed evidence |
| `REQ-002` | Issue Acceptance Criteria 2 | `tests/tools/test_generate_repeated_procedures.py` | Phase 1 | AC-3, AC-6 | `uv run pytest tests/tools/test_generate_repeated_procedures.py` | Explicit in issue |
| `REQ-003` | Issue Constraints (own traceability); `templates/implementation-procedure.md` Traceability | `tools/generate_repeated_procedures.py` | Phase 1 | AC-4 | `tests/tools/test_generate_repeated_procedures.py` | Derived from confirmed evidence |
| `REQ-003` | Issue Implementation Intent | `tests/tools/test_generate_repeated_procedures.py` | Phase 1 | AC-4 | `uv run pytest tests/tools/test_generate_repeated_procedures.py` | Explicit in issue |
| `REQ-004` | Issue Required Changes 3, Constraints | `tools/generate_repeated_procedures.py` | Phase 1 | AC-5 | `tests/tools/test_generate_repeated_procedures.py` | Explicit in issue |
| `REQ-004` | Issue Constraints | `tests/tools/test_generate_repeated_procedures.py` | Phase 1 | AC-5 | `uv run pytest tests/tools/test_generate_repeated_procedures.py` | Explicit in issue |
| `REQ-005` | Issue Documentation Impact; `tools/check_tool_descriptions_sync.py` | `tools/TOOL_DESCRIPTIONS.md` | Phase 1 | AC-7 | `uv run python tools/check_tool_descriptions_sync.py` | Confirmed by repository evidence |
| `REQ-005` | Issue Target Files; `tools/check_skill_size_baseline.txt` line 15 | `skills/plan-to-implementation-procedure/workflow.md` | Phase 2 | AC-7 | `uv run python tools/check_skill_size.py` | Confirmed by repository evidence |
