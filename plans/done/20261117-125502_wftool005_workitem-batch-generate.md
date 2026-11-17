## Goal
- Add a supported way to file several issues from one source in a single, collision-safe call: a new tool reads a Markdown spec that holds the issue documents, allocates unique increasing timestamps, creates the files atomically (or previews them), and checks every created file, so a batch no longer needs a one-off generator.

## Priority
Low

## Scope
- **In-Scope**: (1) a new tool `tools/generate_issue_batch.py` with a spec parser, naming validation, timestamp allocation, collision refusal in `issues/` and `issues/done/`, atomic writes, `--dry-run`, and a post-write check; (2) a new test module; (3) the batch path in `skills/issue-creator/workflow.md` Step 10.2 and a timestamp note in `skills/issue-creator/SKILL.md`; (4) the tool description with the spec format.
- **Out-of-Scope**: batch generation of plans, procedures, or Unknown and Risk files; posting issues to GitHub; any change to `tools/generate_workitem.py` (it is over the size gate and its baseline entry must not grow); filling issue content from anything but the spec.
- **Dependencies**: the post-write check of this Plan calls the structure checker with several paths and relies on its leftover detection, both added by `plans/20261117-124139_wftool001_gate-workitem-structure.md`. `tools/TOOL_DESCRIPTIONS.md` is also edited by the other tooling issues of this batch, the Frozen Plans for them, and the open procedure `implementations/20261117-110514_04_tools_TOOL_DESCRIPTIONS.md.md`; this Plan adds new rows only (see Assumptions, UNK-02).
  - **Depends on**: plans/20261117-124139_wftool001_gate-workitem-structure.md | phase 1 | the post-write check passes every created path to one `--file` call and relies on the leftover check

## Background
Filed from the investigation of the issue -> plan -> implementation toolchain. `tools/generate_workitem.py --kind issue` creates one empty skeleton per call and fills no field. When a list of 23 issues was filed from one source, the files came from a one-off generator outside the repository, with timestamps assigned in advance in one-second steps and in-batch references written through a private placeholder. `tools/generate_workitem.py` already has a batch mode for procedures (`--all-rows`), so batch creation is an accepted pattern in this tool family.

## Problem
Each batch filing reinvents generation, naming checks, and collision checks; an ad hoc generator skips the exact-path absence check in `issues/` and `issues/done/` unless its author reimplements it (`Explicit in code`: `check_collision` exists in the generator, a one-off script does not call it). The generator is 28930 bytes against a 24576-byte limit and is grandfathered in the size baseline, so it cannot take a new option (`Explicit in code`, `tools/check_module_size_tools_baseline.txt`).

## Reason for Change
Batch filing recurs: review findings, audit tasks, and refactoring proposals each produce several issues, and the single-issue loop of the skill stays valid for one issue. A supported path gives every batch the same naming, collision, and check behavior. It is not urgent; the cost is a new tool.

## Implementation Intent
A spec file carries the issue documents themselves, so all content comes from the author and the tool only names, orders, writes, and checks. The tool lives in a new file that imports the existing path and collision helpers, leaving the grandfathered generator untouched. Everything is validated before the first write, so a bad spec creates nothing.

## Requirements
- `REQ-001`: `tools/generate_issue_batch.py` reads one Markdown spec made of issue blocks, each starting with a line `<!-- issue: {id} {slug} -->` followed by a document in the `templates/issue.md` shape; `{id}` matches `[a-z0-9]+` with at least one letter, `{slug}` matches `[a-z0-9_-]+` with at most four words, ids are unique in the spec, and a malformed block is a validation error (exit `2`) before any write.
- `REQ-002`: Timestamps are allocated from one clock read in strictly increasing one-second steps in spec order; every target path is checked in `issues/` and `issues/done/` with the existing collision helper; any collision, invalid block, or duplicate refuses the whole run before the first write.
- `REQ-003`: A token `{{issue:<id>}}` in a block is replaced by the repository-relative path of the issue with that id in the same spec; an unknown id is a validation error.
- `REQ-004`: The tool sets the `Generated at` value of each document to its allocated timestamp and changes no other content.
- `REQ-005`: Files are written atomically; `--dry-run` writes nothing and prints each planned path; if a write fails midway, the tool reports the files already created and deletes none.
- `REQ-006`: After writing, the tool runs the structure and leftover checker once over all created paths and reports per-file results; exit `0` when clean, `1` for findings, `2` for a usage or validation error; the entry point is `main(argv: list[str] | None = None) -> int`.
- `REQ-007`: `tools/TOOL_DESCRIPTIONS.md` documents the tool and the spec format; `skills/issue-creator/workflow.md` Step 10.2 describes the batch path without changing the single-issue path; `skills/issue-creator/SKILL.md` notes that a batch allocates its timestamps.
- `REQ-008`: `tools/generate_workitem.py` is unchanged, the new tool stays below the `tools/` size limit, and no function in it reaches complexity grade C.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/generate_issue_batch.py` | Create the batch tool | No tool creates several issues from a spec; the generator cannot grow | REQ-001 to REQ-006, REQ-008 / AC-1 to AC-6, AC-8 | New file; `tools/` exists; the generator exposes `extract_fenced_skeleton`, `issue_output_path`, `check_collision`, and `GenerationError`, and is listed in the size baseline (checked in Step 3) | `tests/tools/test_generate_issue_batch.py` | Verified |
| `tests/tools/test_generate_issue_batch.py` | Create the test module | No test covers batch creation | REQ-001 to REQ-006 / AC-1 to AC-6 | New file; the directory `tests/tools/` exists; the sibling generator tests redirect `ISSUES_DIR` into `tmp_path` through `monkeypatch` (checked in Step 3) | The file itself | Verified |
| `skills/issue-creator/workflow.md` | Describe the batch path in Step 10.2 | Step 10.2 describes only the one-skeleton tool path | REQ-007 / AC-7 | Step 10.2 "Scaffold the file" lists the tool path and the manual procedure (checked in Step 3) | `tools/check_skills_references.py` | Verified |
| `skills/issue-creator/SKILL.md` | Note that a batch allocates its timestamps | The naming rule says the timestamp is generated at creation time | REQ-007 / AC-7 | The `{timestamp}` bullet in "Issue Filename Generation" says generated at issue creation time (checked in Step 3) | `tools/check_skills_references.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Add the tool rows and the spec format | The tool is new and the spec is a new contract | REQ-007 / AC-7 | The generator has two description rows; the sync checker requires a row for each `tools/*.py` (checked in Step 3) | `tools/check_tool_descriptions_sync.py` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/generate_workitem.py` | Source of the path, skeleton, and collision helpers to import; unchanged | `tools/generate_issue_batch.py` / REQ-001, REQ-002, REQ-008 |
| `templates/issue.md` | The document shape each spec block must follow | `tools/generate_issue_batch.py` / REQ-001 |
| `tools/_atomic_write.py` | Atomic write and dry-run helpers | `tools/generate_issue_batch.py` / REQ-005 |
| `tools/check_workitem_structure.py` | The checker the tool calls after writing | `tools/generate_issue_batch.py` / REQ-006 |
| `tests/tools/test_generate_workitem.py` | Fixture and monkeypatch style to follow | `tests/tools/test_generate_issue_batch.py` / REQ-001 |
| `tools/check_module_size_tools_baseline.txt` | Shows the generator is over the limit and the new tool is not listed | `tools/generate_issue_batch.py` / REQ-008 |

## Acceptance Criteria
- AC-1 (REQ-001): A spec of three valid blocks parses into three issues in order; a block with a bad id, a bad or over-long slug, or a duplicate id exits `2` and creates nothing (tests).
- AC-2 (REQ-002): Three created files carry strictly increasing timestamps; an existing path in `issues/` or in `issues/done/` makes the run refuse before any write (tests).
- AC-3 (REQ-003): `{{issue:<id>}}` becomes `issues/<allocated name>` for an id in the spec, and an unknown id exits `2` (tests).
- AC-4 (REQ-004): Each file's `Generated at` equals the timestamp in its name, and the rest of the document equals the spec block (test).
- AC-5 (REQ-005): `--dry-run` leaves the directory unchanged and prints every planned path; a simulated write failure reports the created files and deletes none (tests).
- AC-6 (REQ-006): The checker runs once with all created paths; a document with leftovers gives exit `1` with the file named; a clean batch gives `0` (tests with a stubbed checker call).
- AC-7 (REQ-007): `tools/check_tool_descriptions_sync.py`, `tools/check_skills_references.py`, and `tools/check_skills_heading_cycles.py` pass, and Step 10.2 keeps the single-issue path unchanged.
- AC-8 (REQ-008): `tools/generate_workitem.py` has no diff, and `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` passes; `radon cc tools/generate_issue_batch.py -s -n C` reports nothing.

## Tests
- `tests/tools/test_generate_issue_batch.py` (new): parsing and validation, allocation, collision in both directories, reference tokens, `Generated at`, dry run, write failure, atomic write, post-write check call, and exit codes; the tests redirect the issue directory into `tmp_path` (REQ-001 to REQ-006).
- Smoke run: `--dry-run` on a two-issue spec against the real repository, then a real run whose created files are removed afterwards (single-path deletes) (REQ-002, REQ-005).

## Documentation Impact
N/A for `docs/*.md`: no file under `docs/` changes. The tool description, the issue-creator workflow step, and the issue-creator naming note change (REQ-007).

## Assumptions
- The tool sets exactly one field itself, `Generated at`, because the author cannot know the allocated timestamp; every other field comes from the spec, so the rule that the tool does not invent content holds.
- A one-second step between issues is acceptable as the allocation rule: the timestamp format has one-second resolution, and the collision helper still guards each path.
- A write failure midway leaves the created files in place and reports them; deleting files in an error path would be a destructive action the tool should not take on its own.
- Overlap with `plans/20261117-124139_wftool001_gate-workitem-structure.md`, `plans/20261117-124614_wftool002_status-vocabulary-unify.md`, `plans/20261117-124834_wftool003_new-marker-tools-merge.md`, and `plans/20261117-125207_wftool004_orphan-tool-routing.md` on `tools/TOOL_DESCRIPTIONS.md` is compatible: this Plan adds new rows and edits no existing row.
- Overlap with `plans/20261117-124139_wftool001_gate-workitem-structure.md` on `skills/issue-creator/workflow.md` is compatible: that Plan edits the Step 10.4 snippet and this Plan edits the Step 10.2 tool-path text.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the maintainer accepts the Markdown spec format of Decision 1 | The issue leaves the format open and asks that the options be presented first | Review Decision 1 before `plan-to-implementation-procedure` runs; the format affects only the parser, the tests, and the documentation, so a change before Phase 1 costs one design edit | False |
| UNK-02 | Order against the open procedure `implementations/20261117-110514_04_tools_TOOL_DESCRIPTIONS.md.md` and the sibling tooling issues that edit `tools/TOOL_DESCRIPTIONS.md` | The procedure's target rows were not read | Read its target rows at implementation time; this Plan adds rows only, so any order works unless the rows coincide | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/generate_issue_batch.py` | Create | Low: new, run by hand | N/A: new file | N/A: new file | not applicable (rsynced) |
| `tests/tools/test_generate_issue_batch.py` | Create | Low | N/A: new file | N/A: new file | not applicable (rsynced) |
| `skills/issue-creator/workflow.md` | Modify | Medium: read on every issue filing | 4 | High: single author | not applicable (rsynced) |
| `skills/issue-creator/SKILL.md` | Modify | Medium: read on every issue filing | 4 | High: single author | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low: documentation rows read by the sync checker | 74 | High: single author | not applicable (rsynced) |

## Design
**Classification**: Path B (a new tool, a new public spec contract, five target rows). The four analyses ran once for this cycle; `skills/python-design/SKILL.md` was applied narrowly to its decision entries and its phase and risk list for the open choices below.
- **Architecture**: the new tool imports the standard library, `tools._atomic_write`, and the helper functions of `tools/generate_workitem.py`, and calls the structure checker as a command; nothing under `scripts/` is involved, so the import-linter contracts are unaffected. Dependency direction: the new tool depends on the generator, never the reverse.
- **Dependency graphing**: nothing imports the generator's helpers except its tests, so importing them from a new tool adds the first reuse; the helpers read the issue directory constant at call time, so tests redirect it the same way the generator's tests do.
- **Historical**: churn is low for the generator and the two issue-creator documents and very high for `tools/TOOL_DESCRIPTIONS.md`; every target has one author. The generator has no complexity above grade B.
- **Operational**: no port, database, dependency, or lock is involved; the persisted-schema check does not apply.
- **Decision 1, spec format**: a Markdown file of issue blocks, each preceded by `<!-- issue: {id} {slug} -->`. Alternatives: YAML (block scalars carry multi-line Markdown, but every one of seventeen fields becomes a key, and a YAML parser adds quoting and implicit-typing pitfalls) and JSON (strict and cheap to parse, but multi-line Markdown must be escaped into strings, which is unreadable for authors). The Markdown form keeps the spec equal to the final documents, matches the repository's one-issue-per-section precedent (`templates/unknowns-issue.md`), and needs no new dependency. Compatibility impact: a new file format and a new tool; no existing caller changes. Reversibility: easy before Phase 1, because only the parser and the documentation depend on it.
- **Decision 2, tool boundary**: a new CLI, not a flag of the generator. Alternative: a `--batch-spec` option on `tools/generate_workitem.py`, rejected because the generator is over the size gate and any added line grows a baseline entry that may only shrink.
- **Decision 3, timestamps**: one clock read, then one-second steps in spec order. Alternative: read the clock per issue, rejected because several issues written within one second would collide in name and order would depend on timing.
- **Decision 4, Traceability**: the tool fills `Generated at` only. Alternative: fill `Workflow phase` and `Related target files` too, rejected because the first is the author's statement and the second restates a section whose content the tool must not interpret. The leftover check reports any field the author left unfilled.
- **Decision 5, in-batch references**: the token `{{issue:<id>}}` resolves to the allocated path, because an author cannot know a path before allocation and cross-issue Dependencies are the common case (the one-off generator needed a private placeholder for exactly this).
- **Decision 6, failure model**: validate the whole spec and every path first, then write; on a mid-run write failure report the created files and delete none.
- **Decision 7, post-write check**: run the structure and leftover checker as a command once over all created paths. This is why the Plan depends on phase 1 of the structure-gate Plan.
- **Baseline**: `vulture` and `bandit` findings under `scripts/` are pre-existing and outside the targets; `diff-cover` has no baseline because the tree equals `master`, and the 90% threshold applies at implementation.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Confirm the spec format and write the tests first**
   - [ ] Confirm Decision 1 with the maintainer before any code; if they choose another format, revise Decision 1 and the parser requirement only (REQ-001; `tools/generate_issue_batch.py`)
   - [ ] Write the tests for parsing, validation, allocation, collision, reference tokens, `Generated at`, dry run, write failure, and the checker call; they fail first (REQ-001 to REQ-006; `tests/tools/test_generate_issue_batch.py`)
2. **Phase 2: Parse, validate, allocate**
   - [ ] Implement the spec parser, the naming validation, the reference resolution, and the timestamp and path allocation as pure functions (REQ-001 to REQ-004, REQ-008; `tools/generate_issue_batch.py`)
3. **Phase 3: Write, preview, check**
   - [ ] Implement the preflight, the atomic writes, `--dry-run`, the write-failure report, the post-write checker call, the exit codes, and `main` (REQ-005, REQ-006, REQ-008; `tools/generate_issue_batch.py`)
4. **Phase 4: Documentation**
   - [ ] Add the tool rows and the spec format (REQ-007; `tools/TOOL_DESCRIPTIONS.md`)
   - [ ] Describe the batch path in Step 10.2 (REQ-007; `skills/issue-creator/workflow.md`)
   - [ ] Add the timestamp note (REQ-007; `skills/issue-creator/SKILL.md`)
5. **Phase 5: Verification** (no deploy step: no `scripts/` or `config/` file changes)
   - [ ] Run the validation sequence of `rules/toolchain.md` for the new tool, both size gates, the description and skills checkers, and the smoke runs; confirm `tools/generate_workitem.py` has no diff (REQ-001 to REQ-008; all target files)

### Release units
N/A: no release unit; each phase passes validation alone when applied in order.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/generate_issue_batch.py` | Unit tests; dry-run and real-run smoke; complexity; security | `uv run pytest tests/tools/test_generate_issue_batch.py -v`; `uv run radon cc tools/generate_issue_batch.py -s -n C`; `uv run bandit tools/generate_issue_batch.py` | Tests pass; radon reports nothing; bandit clean |
| `tests/tools/test_generate_issue_batch.py` | Self; lint and types | `uv run ruff format tools tests/tools`; `uv run ruff check tools tests/tools`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` | Clean |
| `tools/generate_workitem.py` | No change and size gate | `git diff --stat -- tools/generate_workitem.py`; `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | No diff; size gate passes |
| `tools/TOOL_DESCRIPTIONS.md` | Doc consistency | `uv run python tools/check_tool_descriptions_sync.py` | No finding |
| `skills/issue-creator/workflow.md` | Doc consistency | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | No finding |
| `skills/issue-creator/SKILL.md` | Doc consistency | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | No finding |

## Risks
- **Risk**: A bad spec writes some files and then fails → **Mitigation**: the whole spec and every path are validated before the first write, and a test pins it.
- **Risk**: Two issues written in one second collide → **Mitigation**: timestamps come from one clock read in one-second steps, and the collision helper still checks each path.
- **Risk**: The spec format is rejected at review → **Mitigation**: Phase 1 starts with the confirmation, and the format touches only the parser, the tests, and the documentation.
- **Risk**: The post-write check fails because the structure checker does not yet take several paths → **Mitigation**: the Plan depends on phase 1 of the structure-gate Plan, and plan-order tooling reports it as gated.
- **Risk**: The tool invents or alters content → **Mitigation**: a test asserts that the written document equals the spec block except for `Generated at`.
- **Risk**: A real run during the smoke test leaves stray issue files → **Mitigation**: the smoke run removes only the files it created, by path.
- **Risk**: `tools/TOOL_DESCRIPTIONS.md` has very high churn → **Mitigation**: add rows only; rebase through the commit skill and settle the order per UNK-02.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the spec format and write the tests first | In Progress | — | — |  |
| 2 | Parse, validate, and allocate | In Progress | — | — |  |
| 3 | Write, preview, and check | In Progress | — | — |  |
| 4 | Documentation: tool rows, workflow step, naming note | In Progress | — | — |  |
| 5 | Verification: validation sequence, size gates, smoke runs | In Progress | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261117-200906_01_tools_generate_issue_batch.py.md | 1, 2, 3 | Procedure | Pending | — | — |
| implementations/20261117-200906_03_skills_issue-creator_workflow.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261117-200906_04_skills_issue-creator_SKILL.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261117-200906_05_tools_TOOL_DESCRIPTIONS.md.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261117-123334_wftool005_workitem-batch-generate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261117-125502
- **Related target files**: `tools/generate_issue_batch.py`; `tests/tools/test_generate_issue_batch.py`; `skills/issue-creator/workflow.md`; `skills/issue-creator/SKILL.md`; `tools/TOOL_DESCRIPTIONS.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Implementation Intent (a spec file lists issues); Unresolved Questions (spec format) | `tools/generate_issue_batch.py` | Phase 2 | AC-1 | parsing and validation tests | Derived from confirmed evidence |
| REQ-001 | Required Changes (spec format) | `tests/tools/test_generate_issue_batch.py` | Phase 1 | AC-1 | parsing and validation tests | Derived from confirmed evidence |
| REQ-002 | Required Changes (timestamp allocation, name validation, absence check) | `tools/generate_issue_batch.py` | Phase 2 | AC-2 | allocation and collision tests | Explicit in issue |
| REQ-002 | Acceptance Criteria (unique increasing timestamps; refuse a pre-existing path) | `tests/tools/test_generate_issue_batch.py` | Phase 1 | AC-2 | allocation and collision tests | Explicit in issue |
| REQ-003 | Problem (in-batch references needed a private placeholder) | `tools/generate_issue_batch.py` | Phase 2 | AC-3 | reference token tests | Derived from confirmed evidence |
| REQ-003 | Problem (in-batch references) | `tests/tools/test_generate_issue_batch.py` | Phase 1 | AC-3 | reference token tests | Derived from confirmed evidence |
| REQ-004 | Unresolved Questions (Traceability fields); Constraints (no invented content) | `tools/generate_issue_batch.py` | Phase 2 | AC-4 | `Generated at` test | Derived from confirmed evidence |
| REQ-004 | Constraints (no invented content) | `tests/tools/test_generate_issue_batch.py` | Phase 1 | AC-4 | `Generated at` test | Derived from confirmed evidence |
| REQ-005 | Required Changes (`--dry-run`, atomic writes) | `tools/generate_issue_batch.py` | Phase 3 | AC-5 | dry-run and write-failure tests | Explicit in issue |
| REQ-005 | Acceptance Criteria (`--dry-run` writes nothing) | `tests/tools/test_generate_issue_batch.py` | Phase 1 | AC-5 | dry-run and write-failure tests | Explicit in issue |
| REQ-006 | Required Changes (run the structure and leftover check, report per file) | `tools/generate_issue_batch.py` | Phase 3 | AC-6 | checker-call tests | Explicit in issue |
| REQ-006 | Testing Expectations (the structure check call) | `tests/tools/test_generate_issue_batch.py` | Phase 1 | AC-6 | checker-call tests | Explicit in issue |
| REQ-007 | Documentation Impact; Required Changes (Step 10.2) | `tools/TOOL_DESCRIPTIONS.md` | Phase 4 | AC-7 | `tools/check_tool_descriptions_sync.py` | Explicit in issue |
| REQ-007 | Required Changes (Step 10.2); timestamp rule found in Step 3 | `skills/issue-creator/workflow.md` | Phase 4 | AC-7 | `tools/check_skills_references.py` | Explicit in issue |
| REQ-007 | Target Files (`skills/issue-creator/SKILL.md`); timestamp rule found in Step 3 | `skills/issue-creator/SKILL.md` | Phase 4 | AC-7 | `tools/check_skills_heading_cycles.py` | Confirmed by repository evidence |
| REQ-008 | Constraints (size gate; the generator MUST NOT grow) | `tools/generate_issue_batch.py` | Phase 5 | AC-8 | size gate; `radon cc -n C`; `git diff --stat` on the generator | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261117-200906 -->