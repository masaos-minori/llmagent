## Goal
- Leave exactly one tool that inserts the `(new)` marker into implementation procedures, the one that refuses to mark a symbol that exists in source, keep the retired tool's multi-file capability in it, and name it in the two workflows at the point where `stale_detector.py` reports a missing symbol.

## Priority
Medium

## Scope
- **In-Scope**: (1) `tools/mark_procedure_new_symbols.py` accepts several procedure paths in `list` and `mark`; (2) its test module gains the migrated cases and multi-path tests; (3) `tools/fix_procedure_new_markers.py` and its test are removed; (4) the two workflows name the remaining tool; (5) `tools/TOOL_DESCRIPTIONS.md` drops the retired tool, adds the remaining one to the dry-run list, and replaces a hard-coded count.
- **Out-of-Scope**: changing `tools/stale_detector.py`; marking symbols in archived procedures; editing the `Done`-status writer (a sibling Plan); an alias or wrapper for the removed tool.
- **Dependencies**: `tools/TOOL_DESCRIPTIONS.md` is also edited by the other tooling issues of this batch, by the Frozen Plans `plans/20261117-124139_wftool001_gate-workitem-structure.md` and `plans/20261117-124614_wftool002_status-vocabulary-unify.md`, and by the procedure `implementations/20261117-110514_04_tools_TOOL_DESCRIPTIONS.md.md` (archived in `implementations/done/` at revalidation). The first Plan edits other rows; the second edits the same two sentences of the convention paragraph (see Assumptions and the dependency below).
  - **Depends on**: plans/20261117-124614_wftool002_status-vocabulary-unify.md | phase 4 | both Plans edit the dry-run and atomic-write writer lists of the convention paragraph in `tools/TOOL_DESCRIPTIONS.md`; the writer-list wording here is final only after that Plan's edit

## Background
Filed from the investigation of the issue -> plan -> implementation toolchain. Both tools add ` (new)` after backticked names in procedure documents so that `stale_detector.py` does not report them as `symbol_missing`. `plan-to-implementation-procedure` Step 3 and `code-implementation` both run the detector; neither workflow names a tool for the marker.

## Problem
Two tools do one job and only one guards it. `tools/mark_procedure_new_symbols.py` has a `list` step and refuses a name that the detector does not report missing; `tools/fix_procedure_new_markers.py` takes any name, so it can mark an existing symbol as new and silence the check that protects it (`Explicit in code`). Neither tool is referenced by a skill, `routing.md`, or a template; the retired tool is named only by its own file, its test, and `tools/TOOL_DESCRIPTIONS.md` (`Explicit in code`, `rg` over files outside `done/` archives). The description of the retired tool names a `--files` option that its parser does not have (it takes positional paths) (`Explicit in code`). Archived plans still mention the tool, which is outside this change.

## Reason for Change
An operator has no rule for which tool to use, and the unguarded one can defeat a validation guard. The workflows do not say how to apply a `(new)` marker, and a copied command from the description fails. Nothing makes the change time-sensitive; it removes an unguarded tool before it is used on a live procedure.

## Implementation Intent
Keep the guarded tool, because its refusal rule protects the staleness check; retire the other. The retired tool's only extra capability, several files per call with one symbol list, moves into the kept tool's `list` and `mark` so that capability is not lost. The workflows name the tool where a missing symbol is handled, without weakening `code-implementation`'s rule that a stale procedure is aborted and reported, not corrected on the spot.

## Requirements
- `REQ-001`: `list` and `mark` of `tools/mark_procedure_new_symbols.py` accept one or more procedure paths; every path is validated before any write; the guard (refuse a name not reported missing for that path) applies per path; the exit code is `0` only when every path succeeded, `1` when any path had nothing to mark, and `2` for an unusable path; a single path behaves exactly as before.
- `REQ-002`: The test module of the kept tool covers multi-path `list` and `mark`, validation of all paths before a write, and the cases migrated from the retired tool's tests (a real run writes UTF-8, a dry run leaves files unchanged and prints the diff, an already-marked name is left alone, a missing file is an error); the existing refusal test stays.
- `REQ-003`: `tools/fix_procedure_new_markers.py` and `tests/tools/test_fix_procedure_new_markers.py` are removed; no alias, wrapper, or history note remains; no file outside the `done/` archives names the retired tool.
- `REQ-004`: `skills/plan-to-implementation-procedure/workflow.md` and `skills/code-implementation/workflow.md` name `tools/mark_procedure_new_symbols.py` where `symbol_missing` is handled, and `code-implementation` keeps its abort-and-report rule.
- `REQ-005`: `tools/TOOL_DESCRIPTIONS.md` has no entry or list item for the retired tool, lists the kept tool among the `--dry-run` writers, describes its multi-path form, and replaces the hard-coded "the seven above" count with a reference that does not count.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/mark_procedure_new_symbols.py` | Accept several paths in `list` and `mark` | `list` and `mark` take one `path`, and the retired tool's batch capability would be lost | REQ-001 / AC-1, AC-2 | `list_parser` and `mark_parser` each add a single `path`; `_print_mark` applies the refusal guard per call; no complexity above grade B; 7066 B of a 24576 B limit; not in the size baseline (checked in Step 3) | `tests/tools/test_mark_procedure_new_symbols.py` | Verified |
| `tests/tools/test_mark_procedure_new_symbols.py` | Add multi-path tests and migrated cases | The module covers one path and not the retired tool's cases | REQ-002 / AC-3 | Classes `TestMarkNames`, `TestUnmarkedLines`, `TestPrintMark`, and `TestCli` exist; the refusal test is in `TestPrintMark` (checked in Step 3) | The file itself | Verified |
| `tools/fix_procedure_new_markers.py` | Remove the retired tool | Duplicate of the guarded tool, without the refusal rule | REQ-003 / AC-4 | `add_markers` marks any supplied name; open references are the tool, its test, and `tools/TOOL_DESCRIPTIONS.md` only (checked in Step 3) | `tests/tools/test_fix_procedure_new_markers.py` (removed with it) | Verified |
| `tests/tools/test_fix_procedure_new_markers.py` | Remove the retired tool's test | The tested module is removed; useful cases are migrated | REQ-003 / AC-4 | The module imports `tools.fix_procedure_new_markers` and holds four tests (checked in Step 3) | N/A: removed | Verified |
| `skills/plan-to-implementation-procedure/workflow.md` | Name the kept tool in the stale-detector handling | Case (1) says to add `(new)` without naming a tool | REQ-004 / AC-5 | The Step 3 text lists cases (1) to (3) for each detector mismatch (checked in Step 3) | `tools/check_skills_references.py` | Verified |
| `skills/code-implementation/workflow.md` | Name the kept tool in the stale-detector result handling | The result handling names no remedy tool for a missing created symbol | REQ-004 / AC-5 | "Stale detection result handling" states the abort rule and the ways forward (checked in Step 3) | `tools/check_skills_references.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Drop the retired tool, update the kept tool, remove a count | Rows and lists still name the retired tool, the dry-run list omits the kept tool, and a sentence counts "the seven above" | REQ-005 / AC-6 | Rows for both tools exist; the dry-run list names the retired tool; the atomic-write sentence ends with "and the seven above" (re-verified 20261118; the count is stale against the current eight-entry writer list) | `tools/check_tool_descriptions_sync.py` | Verified |

Revalidation (20261118, `plan-to-implementation-procedure` Step 2/3a): the row 7 evidence was corrected — the sentence reads "and the seven above", not "and the six above", and that count is already stale against the current eight-entry `--dry-run` writer list. UNK-02's procedure was found archived in `implementations/done/`. All seven rows were re-checked against current source (paths, sizes, test classes, guard behavior, workflow sections) and stay `Verified`; the section was re-frozen after this single correction cycle.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/stale_detector.py` | Defines the `symbol_missing` output and the `(new)` rules that the kept tool relies on | `tools/mark_procedure_new_symbols.py` / REQ-001 |
| `tools/_atomic_write.py` | The atomic write and dry-run helpers both tools use | `tools/mark_procedure_new_symbols.py` / REQ-001 |
| `templates/implementation-procedure.md` | Its Notes define the `(new)` marker that the workflows refer to | `skills/plan-to-implementation-procedure/workflow.md` / REQ-004 |

## Acceptance Criteria
- AC-1 (REQ-001): With two procedure paths, `list` reports each path and `mark --symbols a,b` marks both; with one path the output and exit code are unchanged (tests).
- AC-2 (REQ-001): A name that the detector does not report missing for one of the paths is refused for that path only; an unusable path ends the run with exit `2` before any file is written (tests).
- AC-3 (REQ-002): The migrated and new cases pass, and the refusal test still passes.
- AC-4 (REQ-003): `rg -n fix_procedure_new_markers` finds no file outside `issues/done/` and `plans/done/` and `implementations/done/`; both removed files are absent.
- AC-5 (REQ-004): Both workflows name `tools/mark_procedure_new_symbols.py`; `code-implementation` still states abort and report; `tools/check_skills_references.py` and `tools/check_skills_heading_cycles.py` pass.
- AC-6 (REQ-005): `tools/check_tool_descriptions_sync.py` passes; the description has no retired-tool mention, lists the kept tool among the dry-run writers, and contains no "the seven above" count.

## Tests
- `tests/tools/test_mark_procedure_new_symbols.py`: multi-path `list` and `mark`, per-path guard, all-paths validation before a write, aggregated exit code, and the migrated cases (REQ-001, REQ-002).
- Smoke run: `list` and `mark --dry-run` on copies of two real procedures (REQ-001).
- Reference checkers for the two workflow edits (REQ-004).

## Documentation Impact
N/A for `docs/*.md`: no file under `docs/` changes. The two workflow documents and the tool description change (REQ-004, REQ-005).

## Assumptions
- Preserving the multi-file call is cheaper than proving that nobody uses it, so the batch capability moves instead of being dropped.
- Validating every path before any write keeps a multi-path `mark` all-or-nothing for usage errors; per-path refusals do not stop the other paths.
- Overlap with the Frozen Plan `plans/20261117-124139_wftool001_gate-workitem-structure.md` on `tools/TOOL_DESCRIPTIONS.md` is compatible: that Plan edits the `check_workitem_structure.py` rows only.
- Overlap with the Frozen Plan `plans/20261117-124614_wftool002_status-vocabulary-unify.md` is a sequencing dependency: both edit the same two sentences of the convention paragraph, so this Plan's writer-list wording follows that Plan's edit (recorded in Scope).
- Archived plans that mention the retired tool are history and stay unchanged.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether an operator script outside the repository calls the retired tool by path | The repository search cannot see external scripts | Confirm at plan review; the multi-file capability is preserved in the kept tool either way | False |
| UNK-02 | Order against the open procedure `implementations/20261117-110514_04_tools_TOOL_DESCRIPTIONS.md.md` and the sibling tooling issues that edit `tools/TOOL_DESCRIPTIONS.md` | The procedure's target rows were not read | Read its target rows at implementation time; the edits are row-level, so land the earlier one first if rows coincide. Resolved at revalidation 20261118: the procedure is archived in `implementations/done/` and its description edits are already applied | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/mark_procedure_new_symbols.py` | Modify | Low: no importer except its test; run by hand | 1 | High: single author | not applicable (rsynced) |
| `tests/tools/test_mark_procedure_new_symbols.py` | Modify | Low | N/A: no commit in the window | High: single author | not applicable (rsynced) |
| `tools/fix_procedure_new_markers.py` | Delete | Low: no caller outside its test and the description | 2 | High: single author | not applicable (rsynced) |
| `tests/tools/test_fix_procedure_new_markers.py` | Delete | Low | 1 | High: single author | not applicable (rsynced) |
| `skills/plan-to-implementation-procedure/workflow.md` | Modify | Medium: read by the planning workflow on every run | 9 | High: single author | not applicable (rsynced) |
| `skills/code-implementation/workflow.md` | Modify | Medium: read by the implementation workflow on every run; highest churn of the targets | 22 | High: single author | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low: documentation read by the sync checker | 74 | High: single author | not applicable (rsynced) |

## Design
**Classification**: Path B (seven target rows, two of them deletions). The four analyses ran once for this cycle.
- **Architecture**: the kept tool imports the standard library and `tools._atomic_write` and runs `tools/stale_detector.py` as a subprocess; nothing under `scripts/` is involved, so the import-linter contracts are unaffected.
- **Dependency graphing**: nothing imports either module except its own test; the only non-test references are `tools/TOOL_DESCRIPTIONS.md` and the retired tool's own docstring. Archived plans (`flowimp007`, `toolwrite001`, and others) mention the retired tool and stay as history.
- **Historical**: both workflow documents change often (22 and 9 commits in 30 days), so the edits are one sentence each; every target has one author.
- **Operational**: no port, database, dependency, or lock is involved; the persisted-schema check does not apply.
- **Decision 1, which tool stays**: the guarded one, as the issue directs. The retired tool's `--symbols` free-form call is the exact path that could mark an existing symbol as new.
- **Decision 2, multi-path semantics**: validate every path first (exit `2` if any is unusable), then apply the guard per path, so one refused name does not block the others. Exit `1` when a path had nothing to mark keeps the existing meaning.
- **Decision 3, workflows**: `plan-to-implementation-procedure` Step 3, case (1), names the tool as the way to apply the marker. `code-implementation` keeps abort-and-report; its "ways forward" bullet that covers an approved correction names the tool for a name the procedure creates. No workflow step starts correcting a procedure on its own.
- **Decision 4, documentation count**: the sentence "and the seven above" breaks when the dry-run list changes (this Plan removes one entry and adds one; the sibling Plan adds another), so it becomes a reference to the writers named in the `--dry-run` paragraph, without a count.
- **Baseline**: `radon` reports no function of grade C or worse in the kept tool; `vulture` and `bandit` findings under `scripts/` are pre-existing and outside the targets; `diff-cover` has no baseline because the tree equals `master`, and the 90% threshold applies at implementation.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Zero-caller check and tests first**
   - [ ] Re-run the open-file `rg` for the retired tool and stop if a caller appears (REQ-003; `tools/fix_procedure_new_markers.py`)
   - [ ] Add the multi-path tests and the migrated cases; the multi-path tests fail first (REQ-002; `tests/tools/test_mark_procedure_new_symbols.py`)
2. **Phase 2: Multi-path support**
   - [ ] Accept several paths in `list` and `mark`, validate all before writing, and aggregate the exit code (REQ-001; `tools/mark_procedure_new_symbols.py`)
3. **Phase 3: Retire the old tool**
   - [ ] Remove the tool (REQ-003; `tools/fix_procedure_new_markers.py`)
   - [ ] Remove its test after the migrated cases pass in the kept module (REQ-003; `tests/tools/test_fix_procedure_new_markers.py`)
4. **Phase 4: Workflows and description**
   - [ ] Name the kept tool in Step 3, case (1) (REQ-004; `skills/plan-to-implementation-procedure/workflow.md`)
   - [ ] Name the kept tool in the approved-correction way forward and keep the abort rule (REQ-004; `skills/code-implementation/workflow.md`)
   - [ ] Drop the retired tool, add the kept tool to the dry-run list, update its row, and replace the count; apply after the sibling Plan's list edit (REQ-005; `tools/TOOL_DESCRIPTIONS.md`)
5. **Phase 5: Verification** (no deploy step: no `scripts/` or `config/` file changes)
   - [ ] Run the validation sequence of `rules/toolchain.md` for the changed tool, the skills reference checkers, `tools/check_tool_descriptions_sync.py`, the `rg` check for the retired name, and a smoke run on copies of two real procedures (REQ-001 to REQ-005; all target files)

### Release units
N/A: no release unit; each phase passes validation alone when applied in order.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/mark_procedure_new_symbols.py` | Unit tests; smoke on copies | `uv run pytest tests/tools/test_mark_procedure_new_symbols.py -v`; `uv run bandit tools/mark_procedure_new_symbols.py`; `uv run radon cc tools/mark_procedure_new_symbols.py -s -n C` | Tests pass; bandit clean; radon reports nothing |
| `tests/tools/test_mark_procedure_new_symbols.py` | Self; lint and types | `uv run ruff format tools tests/tools`; `uv run ruff check tools tests/tools`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` | Clean |
| `tools/fix_procedure_new_markers.py` and its test | Removal evidence | `rg -n fix_procedure_new_markers --glob '!**/done/**'` | No reference |
| `skills/plan-to-implementation-procedure/workflow.md` | Doc consistency | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | No finding |
| `skills/code-implementation/workflow.md` | Doc consistency | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | No finding |
| `tools/TOOL_DESCRIPTIONS.md` | Doc consistency; size gate | `uv run python tools/check_tool_descriptions_sync.py`; `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | No finding; size gate passes |

## Risks
- **Risk**: A caller of the retired tool exists that the repository search cannot see → **Mitigation**: Phase 1 re-runs the search and stops on a hit; UNK-01 asks at plan review; the capability is preserved in the kept tool.
- **Risk**: The multi-path `mark` marks some files and then fails on another → **Mitigation**: every path is validated before the first write, and a test pins it.
- **Risk**: The workflow edit invites correcting a stale procedure on the spot → **Mitigation**: `code-implementation` keeps its abort-and-report rule and names the tool only for an approved correction.
- **Risk**: Both sibling Plans edit the same sentences of the convention paragraph → **Mitigation**: the dependency on the sibling Plan's phase 4 fixes the order, and the count is removed so the wording cannot go stale again.
- **Risk**: The two workflow documents have the highest churn of the targets (22 and 9 commits in 30 days) → **Mitigation**: one sentence per file; rebase through the commit skill.
- **Risk**: Removing a tool leaves a stale reference somewhere → **Mitigation**: the `rg` check, `tools/check_tool_descriptions_sync.py`, and `tools/check_skills_references.py` run in Phase 5.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Zero-caller check and tests first | Completed | — | 20261118-095545 | zero-caller re-check 20261118: rg -n fix_procedure_new_markers names only the tool, its test, tools/TOOL_DESCRIPTIONS.md, and this batch's procedure docs; multi-path tests written first and failed before the CLI change |
| 2 | Multi-path support in the kept tool | Completed | — | 20261118-095545 | seq 01 procedure archived: implementations/done/20261118-041553_01_tools_mark_procedure_new_symbols.py.md |
| 3 | Retire the old tool and its test | Completed | — | 20261118-100246 | seq 03 procedure archived: tools/fix_procedure_new_markers.py and its test deleted, no alias or wrapper; tools/TOOL_DESCRIPTIONS.md mentions removed by the seq 07 document in the same change |
| 4 | Workflows and tool description | Completed | — | 20261118-100925 | seq 05, 06, 07 procedures archived: both workflows name the kept tool, tools/TOOL_DESCRIPTIONS.md current |
| 5 | Verification: validation sequence, checkers, smoke run | Completed | — | 20261118-101348 | Re-verified on the merged tree after conflict resolution (the origin 3bee87279 implementation, tests, and archived seq 01 document adopted; this session's duplicate batch1 edits dropped): 19 marker-tool + 102 gate tests pass; bandit -c pyproject.toml low-only findings (pre-existing subprocess call, CI -ll gate clear); radon: no grade C+ block; ruff format/check and mypy clean; tool_descriptions_sync, module size, skills reference and heading-cycle checkers: no findings; rg retired name: no match; drift: 47 routing.md checkers all mapped |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261118-041553_01_tools_mark_procedure_new_symbols.py.md | 1, 2 | Procedure | Completed | — | — |
| implementations/20261118-041553_03_tools_fix_procedure_new_markers.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261118-041553_05_skills_plan-to-implementation-procedure_workflow.md.md | 4 | Procedure | Completed | — | — |
| implementations/20261118-041553_06_skills_code-implementation_workflow.md.md | 4 | Procedure | Completed | — | — |
| implementations/20261118-041553_07_tools_TOOL_DESCRIPTIONS.md.md | 4 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261117-123332_wftool003_new-marker-tools-merge.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261117-124834
- **Related target files**: `tools/mark_procedure_new_symbols.py`; `tests/tools/test_mark_procedure_new_symbols.py`; `tools/fix_procedure_new_markers.py`; `tests/tools/test_fix_procedure_new_markers.py`; `skills/plan-to-implementation-procedure/workflow.md`; `skills/code-implementation/workflow.md`; `tools/TOOL_DESCRIPTIONS.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (multi-file input if needed); Unresolved Questions | `tools/mark_procedure_new_symbols.py` | Phase 2 | AC-1, AC-2 | multi-path tests | Derived from confirmed evidence |
| REQ-002 | Required Changes (migrate its test cases) | `tests/tools/test_mark_procedure_new_symbols.py` | Phase 1 | AC-3 | the module's tests | Explicit in issue |
| REQ-003 | Required Changes (remove the tool and its test) | `tools/fix_procedure_new_markers.py` | Phase 3 | AC-4 | `rg -n fix_procedure_new_markers --glob '!**/done/**'` | Confirmed by repository evidence |
| REQ-003 | Required Changes (remove the tool and its test) | `tests/tools/test_fix_procedure_new_markers.py` | Phase 3 | AC-4 | `rg` removal check | Confirmed by repository evidence |
| REQ-004 | Required Changes (name the tool in the two workflows) | `skills/plan-to-implementation-procedure/workflow.md` | Phase 4 | AC-5 | `tools/check_skills_references.py` | Explicit in issue |
| REQ-004 | Required Changes (name the tool in the two workflows) | `skills/code-implementation/workflow.md` | Phase 4 | AC-5 | `tools/check_skills_heading_cycles.py` | Explicit in issue |
| REQ-005 | Required Changes (remove mentions); Problem (option-name mismatch); the count sentence found in Step 3 | `tools/TOOL_DESCRIPTIONS.md` | Phase 4 | AC-6 | `tools/check_tool_descriptions_sync.py` | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261118-041553 -->