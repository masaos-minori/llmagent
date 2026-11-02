## Goal
- Add a consumer-scan step to `issue-to-plan` for changes to persisted schema, public APIs, or shared constants, backed by a new read-only tool that lists the candidate direct and indirect consumers of a change, so the `Implementation Target Files` table is complete at freeze time instead of being completed one file at a time during implementation.

## Priority
High

## Scope
- **In-Scope**:
  - A new read-only tool, `tools/scan_change_consumers.py`, that takes change seeds (a symbol, a column or table name, a constant, or a file) and prints a categorized candidate report in plain text and JSON.
  - Candidate categories: direct references in `scripts/`, `tests/`, `tools/`, `deploy/`, and `docs/`; tests that patch or import the module defining the seed; inventory-style checkers and pinned constants; ADR citations of tests.
  - An evaluation of `.testmondata` as an additional "tests that execute this file" source, used only when the file exists and is fresh, with the state stated in the output otherwise.
  - A step in `skills/issue-to-plan/workflow.md` that runs the tool for the named change classes and requires each candidate to be recorded as a target row, a reference row, or a stated "not affected" reason, with the record format noted in `templates/plan.md`.
  - Registration of the tool in `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, and the gate runner mapping.
- **Out-of-Scope**:
  - Changing Plan Freeze rules or making the scan a blocking gate.
  - Detecting consumers by running the test suite during planning.
  - Dependency ordering between Plans and the release-unit concept (separate Plans).
- **Dependencies**: N/A: none blocking. Re-verified in Step 2 (2026-11-02): no open Issue lists these files as targets. Sequencing notes, all additive and compatible (judged in Assumptions A5 to A7): `routing.md` and `tools/run_validation_gates.py` are also edited by `plans/20261102-075445_flowimp005_gates-hook-parity.md`; `routing.md` also by `plans/20261102-075753_flowimp004_schema-change-checklist.md`.

## Background
- `Operationally observed` (session of 2026-10-30, from the Issue): three Frozen Plans (`dbmig001`, `wftaskapi001`, `wfrecovery001`) were amended after freeze because a file outside the table had to change: `tools/check_db_separation.py` (its `TABLE_OWNERSHIP` inventory rejected a new table), `tests/deploy/test_init_db_eventbus_schema.py` (its sandbox config pinned a key inside a TOML table, so a subprocess reached the production database), and `tests/integration/test_orchestrator_integration.py` (mocked tasks had no status; a mocked engine returned a `MagicMock` attempt number). Each omission was found only by a full-suite run or a pre-commit hook.
- `Explicit in code` (checked in Step 3): `skills/plan-to-implementation-procedure/workflow.md` Step 3c ends a cycle `Blocked: additional target file discovered` for a file outside the table; `skills/issue-to-plan/workflow.md` Step 2 and Step 3 verify files, symbols, and line numbers the Issue names, and no step enumerates indirect consumers.
- Verified in Step 2 (2026-11-02): all three seeds named for the live check (`workflow_schema_version`, `WORKFLOW_SCHEMA_VERSION`, `begin_stage_if_new`) exist in `scripts/`, `tests/`, and `tools/`. A plain `rg` over the three historical files with those seeds hits only `tools/check_db_separation.py`; the deploy test and the orchestrator integration test have no direct seed hit. Expected recall on this seed set is therefore partial, and the tool MUST report it rather than assume it.
- Verified in Step 2 (2026-11-02): no `.testmondata*` file exists in the repository root or one level below, although `pytest-testmon` is a declared dependency (`pyproject.toml`, `tox.ini`) and `.gitignore` ignores the file. The Issue's statement that a local file exists and was last updated on 2026-10-25 does not hold today.
- `Explicit in code` (checked in Step 3): `tools/run_validation_gates.py` `drift_report()` reports an error for a `routing.md` "When to run which tool" checker that has no gate mapping, and `tests/tools/test_run_validation_gates.py` `test_drift_all_routing_checkers_mapped` asserts that on the live `routing.md`. A new routing row therefore needs a mapping entry in the same change.
- Verified in Step 2 (2026-11-02): the Issue's "queued Plans" (`toolexec001`, `wflease001`, `dlqbox001`) are already archived; the open persisted-state work is `plans/20261101-133244_dbmigrunner001_runner-unsafe-table-rebuild.md` and later schema Plans.

## Problem
A Frozen Plan's target table is the only scope the later phases may touch. When it omits an indirect consumer, the implementation cycle stops, the Plan is amended, and work waits for approval, although the cause was knowable at planning time with a search.

## Reason for Change
Schema, DDL, and public-API changes are the most common change class in this repository, and each has the same blind spot. The cost was three amendments in one release and recurs with every persisted-state Plan.

## Implementation Intent
Treat consumer discovery as a planning step with a tool, not as the author's memory. The tool is heuristic and read-only; its output is a candidate list that the Plan author classifies, never a verdict. Categories that cannot be detected reliably are reported as limits in the output. The testmon data is a source of last resort: used only when present and fresh, and its state is always printed.

## Requirements
- `REQ-001`: `tools/scan_change_consumers.py` MUST take one or more seeds and print a categorized candidate report in plain text and in JSON, labeling every result as a candidate and stating that a missing consumer is not evidence of absence.
- `REQ-002`: The report MUST cover at least these categories: direct references in `scripts/`, `tests/`, `tools/`, `deploy/`, and `docs/`; tests that patch or import the module defining the seed; inventory-style checkers and pinned constants; ADR citations of tests. For a seed in no category it MUST report nothing for that category.
- `REQ-003`: The tool MUST evaluate `.testmondata` as an additional source, use it only when it exists and is fresh, open it read-only, and print its state (absent, stale, or used) in every report.
- `REQ-004`: `skills/issue-to-plan/workflow.md` MUST contain a step that runs the tool for changes to persisted schema, public API, or shared constants and requires each candidate to be recorded as a target row, a reference row, or a stated "not affected" reason; `templates/plan.md` MUST describe the record format.
- `REQ-005`: The tool MUST be read-only with no network access and no writes except stdout and an optional report path, and MUST be registered in `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, and the gate runner mapping so the drift check passes.
- `REQ-006`: The implementing change MUST record the recall of the live run with the three seeds against the three historical omissions, naming which were not found and why.

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8b, 2026-11-02; all rows `Verified`)

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/scan_change_consumers.py` | New file: the scan tool | New file; no tool enumerates consumers (`tools/` directory exists) | REQ-001, REQ-002, REQ-003, REQ-005 / AC-1, AC-2, AC-5 | no existing consumer-scan tool in `tools/TOOL_DESCRIPTIONS.md` (checked in Step 3) | `tests/tools/test_scan_change_consumers.py` | Verified |
| `tests/tools/test_scan_change_consumers.py` | New file: unit tests over temporary trees | New file for the new tool (`tests/tools/` exists) | REQ-001, REQ-002, REQ-003 / AC-1, AC-2 | `tests/tools/` holds one test module per tool (checked in Step 3) | itself | Verified |
| `skills/issue-to-plan/workflow.md` | The consumer-scan step and record rule | Step 2 and Step 3 do not enumerate indirect consumers | REQ-004 / AC-3 | "Step 3: Inspect Related Files" section (checked in Step 3) | `check_skills_references.py`, `check_skills_heading_cycles.py` | Verified |
| `templates/plan.md` | Record format for scan candidates | The notes on filling `Implementation Target Files` do not mention a scan record | REQ-004 / AC-3 | "Notes on filling Implementation Target Files and Reference Files" (checked in Step 3) | `check_workitem_structure.py` on a generated Plan | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Register the tool | Every `tools/*.py` needs a row | REQ-005 / AC-4 | `check_tool_descriptions_sync.py` hook (checked in Step 3) | `tools/check_tool_descriptions_sync.py` | Verified |
| `routing.md` | Row in "When to run which tool" | The scan has no routing entry | REQ-005 / AC-4 | table "When to run which tool" (checked in Step 3) | `tools/run_validation_gates.py drift` | Verified |
| `tools/run_validation_gates.py` | Gate mapping entry for the new routing row | `drift_report()` fails for a routing checker without a mapping | REQ-005 / AC-4 | `drift_report`, `ROUTING_GATES`, placeholder-token rule for gates needing an argument (checked in Step 3) | `tests/tools/test_run_validation_gates.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/check_plan_target_overlaps.py` | Pattern for a read-only, candidates-not-verdict tool | REQ-001 |
| `tools/check_mock_patch_targets.py` | Existing detection of `patch("module.Symbol")` targets, reusable in approach | REQ-002 |
| `tools/check_adr_invariant_matrix.py` | How ADR-cited tests are written, for the ADR category | REQ-002 |
| `tools/check_db_separation.py` | Historical consumer; its `TABLE_OWNERSHIP` inventory is the inventory-checker example | REQ-002, REQ-006 |
| `tests/deploy/test_init_db_eventbus_schema.py` | Historical consumer (deploy-script category) | REQ-006 |
| `tests/integration/test_orchestrator_integration.py` | Historical consumer (mock-based category) | REQ-006 |
| `pyproject.toml` | `pytest-testmon` dependency declaration | REQ-003 |
| `.gitignore` | Confirms `.testmondata` is ignored | REQ-003 |
| `docs/10_adr/adr_01_index.md` | ADR invariant matrix that cites tests | REQ-002 |
| `skills/plan-to-implementation-procedure/workflow.md` | Step 3c "additional target file discovery" the scan aims to prevent | REQ-004 |

## Acceptance Criteria
- AC-1 (`REQ-001`, `REQ-002`): Against fixture trees in `tests/tools/`, the tool reports each category for a seed that appears in that category and nothing for an unrelated seed; text and JSON outputs both state that results are candidates.
- AC-2 (`REQ-003`): With no testmon file, a stale file, and a fresh file, the report prints `absent`, `stale`, and `used` respectively and never opens the file for writing.
- AC-3 (`REQ-004`): `skills/issue-to-plan/workflow.md` contains the step, `templates/plan.md` states the record format, and `check_skills_references.py` and `check_skills_heading_cycles.py` pass.
- AC-4 (`REQ-005`): `check_tool_descriptions_sync.py` passes with the tool registered and `tools/run_validation_gates.py drift` reports no unmapped checker.
- AC-5 (`REQ-005`): A run on the live repository finishes within the planning time target (a target under 30 seconds, `Needs confirmation` until measured) and writes nothing.
- AC-6 (`REQ-006`): A live run with the seeds `workflow_schema_version`, `WORKFLOW_SCHEMA_VERSION`, and `begin_stage_if_new` is recorded in the implementing change with the recall against the three historical files and the reason for each file not found.

## Tests
- `REQ-001`, `REQ-002`: unit tests over temporary directory trees, one per category, plus an unrelated-seed case and a text/JSON output case.
- `REQ-003`: tests for absent, stale, and fresh testmon data, including an unreadable or unrecognized file reported as a limit.
- `REQ-004`: structure check of a Plan generated with the new record format.
- `REQ-005`: `check_tool_descriptions_sync.py`, the drift check, and a no-write assertion in the tests.
- `REQ-006`: one manual live run with the three seeds.

## Documentation Impact
- Yes. `skills/issue-to-plan/workflow.md` and `templates/plan.md` state the new step and its record format; `tools/TOOL_DESCRIPTIONS.md` and `routing.md` list the tool (REQ-004, REQ-005). Intent and failure behavior only (heuristic, candidates only). No `docs/*.md` change: workflow tooling, not system design.

## Assumptions
- A1: Recall on the three historical omissions can be measured after the fact and is an acceptable quality bar for a heuristic tool (from the Issue); the Step 2 pre-check shows partial recall is expected.
- A2: The tool enumerates files with `git ls-files`, so ignored and generated trees (`.venv/`, `__pycache__/`) stay out of scope (`skills/DESIGN.md` Out-of-scope paths). Falsifiable by a scan reading an ignored path.
- A3: Seeds are resolved to defining modules by a lightweight text match of `def`, `class`, and assignment names, not AST parsing, matching `tools/check_plan_target_overlaps.py` (corrected in plan-to-implementation-procedure Step 3a: `tools/check_mock_patch_targets.py` is AST-based, so only some candidate tools are text-based). Falsifiable by a seed defined in a way the match misses, which the output reports as a limit.
- A4: The first version treats the testmon source as optional; absence is the normal state today.
- A5: Overlap judgment (Step 8b): `routing.md` is also a target of `plans/20261102-075445_flowimp005_gates-hook-parity.md` and `plans/20261102-075753_flowimp004_schema-change-checklist.md`. Judged compatible: this Plan adds one row to the "When to run which tool" table, the first adds rows to the same table, the second edits the "Conditional load" list; the edits are row-additive.
- A6: Overlap judgment (Step 8b): `tools/run_validation_gates.py` is also a target of `plans/20261102-075445_flowimp005_gates-hook-parity.md`. Judged compatible and sequencing-dependent in one respect: that Plan's hook-parity check does not affect a tool without a hook, and this Plan adds one mapping entry; whichever lands second rebases.
- A7: Overlap judgment (Step 8b): `tools/TOOL_DESCRIPTIONS.md` is also a target of `plans/20261102-075445_flowimp005_gates-hook-parity.md`. Judged compatible: this Plan adds a new tool row, that Plan updates the existing `run_validation_gates.py` rows.
- A8: `git-fame` is not used; Bus Factor is `N/A` (single-owner repository).
- A9: Overlap judgment (plan-to-implementation-procedure Step 2, `tools/check_plan_target_overlaps.py`, 2026-11-02, after later sibling Plans were frozen): `routing.md`, `tools/run_validation_gates.py`, and `tools/TOOL_DESCRIPTIONS.md` are also targets of `plans/20261102-080134_flowimp003_plan-dependency-gate.md`, `plans/20261102-081027_flowimp011_plan-amend-tool.md`, and `plans/20261102-081312_flowimp010_artifact-commit-split.md`; `templates/plan.md` is also a target of `plans/20261102-080134_flowimp003_plan-dependency-gate.md` (`Scope` block) and `plans/20261102-080336_flowimp002_plan-release-units.md` (`Implementation steps` block); `skills/issue-to-plan/workflow.md` is also a target of `plans/20261102-080336_flowimp002_plan-release-units.md` (Step 5 line). Judged compatible: each adds its own row or mapping entry, or edits a different block or step than this Plan (a notes section of `templates/plan.md`, Step 3 of the skill); no conflict. Sequencing: whichever lands second rebases on the shared files; edits must be located by heading, not line number.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether `.testmondata` is reliable enough as a source and how its schema can be read safely | No `.testmondata*` file exists to inspect; its refresh in a normal workflow is unconfirmed | Implement the source as optional; if the file is absent or its schema is unrecognized, report the limit; evaluate when a file can be produced | False |
| UNK-02 | How much of the mock-based case a text search catches without testmon | The orchestrator integration test has no direct seed hit | Measure in the live run (REQ-006) and report the limit in the tool output | False |
| UNK-03 | Whether the scan completes in under 30 seconds on this repository | Not measured | Time the live run at implementation; optimize file reading if the target is missed | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/scan_change_consumers.py` | Create | Low (new, read-only, no importers) | 0 | N/A | not applicable (rsynced) |
| `tests/tools/test_scan_change_consumers.py` | Create | Low | 0 | N/A | not applicable (rsynced) |
| `skills/issue-to-plan/workflow.md` | Modify | Medium (every issue-to-plan run reads it) | 12 | N/A | not applicable (rsynced) |
| `templates/plan.md` | Modify | Medium (every Plan follows it) | 5 | N/A | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low | 82 | N/A | not applicable (rsynced) |
| `routing.md` | Modify | Medium (loaded by every task) | 28 | N/A | not applicable (rsynced) |
| `tools/run_validation_gates.py` | Modify | Medium (gate selection and drift check) | 8 | N/A | not applicable (rsynced) |

## Design
- Tool shape: `uv run python tools/scan_change_consumers.py --seed <seed> [--seed <seed> ...] [--format text|json] [--report <path>]`. Files come from `git ls-files`; each is read as text once. Output is grouped by category, each hit shows the file and a short matching line, and the header states "candidates only; absence is not evidence".
- Categories: (1) direct references per directory; (2) patch and import consumers: resolve the seed's defining module, then find tests that name that module in a `patch("...")` target or an import; (3) inventory-style checkers and pinned constants: `tools/` checkers and baseline or inventory files that name the seed or its module; (4) ADR citations: tests that contain the seed and are cited by `docs/10_adr/` matrix rows; (5) testmon, optional.
- Testmon: the source is attempted only when a `.testmondata` file exists and is newer than a freshness threshold; it is opened read-only (`immutable` URI) and an unrecognized schema is reported as a limit. The state line is printed in every report.
- Skill step: added to `skills/issue-to-plan/workflow.md` Step 3 (Path B inspection) for the three change classes; each candidate is recorded in the Plan's `Design` section as a target row, a reference row, or "not affected: {reason}". The scan is guidance, not a gate (out of scope: making it blocking).
- Alternatives rejected: running the test suite during planning (out of scope, 7 to 8 minutes); AST-based resolution for the seed's defining module (heavier; `tools/check_plan_target_overlaps.py` is regex-based, while `tools/check_mock_patch_targets.py` is AST-based, so the repository has both, and the patch-target category may reuse that tool's `extract_patch_targets` approach).
- Registration: the routing row carries a `<seed>` placeholder, so the gate runner entry is reported `Not available` at run time but keeps its mapping, matching existing placeholder gates.
- Compatibility: no existing tool, rule, or Freeze semantics change.

## Implementation steps
1. **Phase 1: Tool and tests**
   - [ ] Implement `tools/scan_change_consumers.py` with seeds, categories, text and JSON output, and the testmon state line (`REQ-001`, `REQ-002`, `REQ-003`, `REQ-005`; `tools/scan_change_consumers.py`)
   - [ ] Write unit tests over temporary trees for each category, the unrelated-seed case, and the testmon states (`REQ-001`, `REQ-002`, `REQ-003`; `tests/tools/test_scan_change_consumers.py`)
2. **Phase 2: Registration**
   - [ ] Add the `TOOL_DESCRIPTIONS.md` row, the `routing.md` row, and the gate mapping entry (`REQ-005`; `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, `tools/run_validation_gates.py`)
3. **Phase 3: Skill and template**
   - [ ] Add the consumer-scan step and the record rule (`REQ-004`; `skills/issue-to-plan/workflow.md`)
   - [ ] Add the record format note (`REQ-004`; `templates/plan.md`)
4. **Phase 4: Verification** (no `scripts/` or `config/` change, so no deploy step is required)
   - [ ] Run the tool lint sequence of `routing.md` "Adding a new tool", the live run with the three seeds, time it, and record the recall (`REQ-005`, `REQ-006`; `tools/scan_change_consumers.py`)
   - [ ] Run `check_tool_descriptions_sync.py`, the drift check, `check_skills_references.py`, and `check_skills_heading_cycles.py` (`REQ-004`, `REQ-005`; all rows)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/scan_change_consumers.py` | Unit over temporary trees | `uv run pytest tests/tools/test_scan_change_consumers.py -v` | all pass |
| `tools/scan_change_consumers.py` | Lint, type, security | `uv run ruff format tools/scan_change_consumers.py`; `uv run ruff check tools/scan_change_consumers.py`; `uv run mypy tools/scan_change_consumers.py`; `uv run bandit tools/scan_change_consumers.py` | clean |
| `tools/scan_change_consumers.py` | Live smoke run (REQ-006) | `uv run python tools/scan_change_consumers.py --seed workflow_schema_version --seed WORKFLOW_SCHEMA_VERSION --seed begin_stage_if_new` | completes; recall against the three historical files recorded |
| `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, `tools/run_validation_gates.py` | Registration and drift | `uv run python tools/check_tool_descriptions_sync.py`; `uv run python tools/run_validation_gates.py drift`; `uv run pytest tests/tools/test_run_validation_gates.py -v` | pass |
| `skills/issue-to-plan/workflow.md`, `templates/plan.md` | Reference and heading checks | `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` | no findings |

## Risks
- **Risk**: Heuristic recall is partial (the Step 2 pre-check reaches one of three historical files by direct text) and the step gives false confidence. → **Mitigation**: every report states "candidates only; absence is not evidence", the skill step does not make the scan a gate, and REQ-006 records the measured recall.
- **Risk**: Scanning the whole tree is slow. → **Mitigation**: `git ls-files` limits the file set and each file is read once; UNK-03 measures it against the 30-second target.
- **Risk**: Opening `.testmondata` could write to it or break on an unknown schema. → **Mitigation**: read-only `immutable` open, an unrecognized schema is reported as a limit, and the source is optional.
- **Risk**: A new routing row without a gate mapping makes the drift check fail. → **Mitigation**: the gate runner mapping is a target row of this Plan (Phase 2).
- **Risk**: `routing.md`, `tools/TOOL_DESCRIPTIONS.md`, and `tools/run_validation_gates.py` are shared with sibling Plans. → **Mitigation**: edits are row-additive; overlaps are judged in Assumptions A5 and A6.
- **Risk**: Pre-existing `vulture` and `bandit` findings in `scripts/` (measured in Step 5) are mistaken for regressions. → **Mitigation**: baseline recorded in the sibling Plans; only findings on the new tool count.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see `templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Tool and tests: `tools/scan_change_consumers.py`, `tests/tools/test_scan_change_consumers.py` | Completed | — | 20261102-101341 |  |
| 2 | Registration: `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, `tools/run_validation_gates.py` | Completed | — | 20261102-101341 |  |
| 3 | Skill and template: `skills/issue-to-plan/workflow.md`, `templates/plan.md` | Completed | — | 20261102-101341 |  |
| 4 | Verification: lint sequence, live run with recall record, checkers | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261102-085054_01_tools_scan_change_consumers.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261102-085054_02_tests_tools_test_scan_change_consumers.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261102-085054_03_skills_issue-to-plan_workflow.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261102-085054_04_templates_plan.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261102-085054_05_tools_TOOL_DESCRIPTIONS.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261102-085054_06_routing.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261102-085054_07_tools_run_validation_gates.py.md | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261030-191006_flowimp001_consumer-impact-scan.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261102-080004
- **Related target files**: `tools/scan_change_consumers.py`, `tests/tools/test_scan_change_consumers.py`, `skills/issue-to-plan/workflow.md`, `templates/plan.md`, `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, `tools/run_validation_gates.py` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (tool with seeds and categorized report) | `tools/scan_change_consumers.py` | Phase 1 | AC-1 | unit tests | Explicit in issue |
| REQ-001 | Testing Expectations (unit tests per category) | `tests/tools/test_scan_change_consumers.py` | Phase 1 | AC-1 | unit tests | Explicit in issue |
| REQ-002 | Required Changes (categories) | `tools/scan_change_consumers.py` | Phase 1 | AC-1 | per-category tests | Explicit in issue |
| REQ-003 | Required Changes (evaluate `.testmondata`); Unresolved Questions; Step 2 (file absent) | `tools/scan_change_consumers.py` | Phase 1 | AC-2 | testmon state tests | Confirmed by repository evidence |
| REQ-003 | Testing Expectations ("tool unavailable or data stale" path) | `tests/tools/test_scan_change_consumers.py` | Phase 1 | AC-2 | testmon state tests | Explicit in issue |
| REQ-004 | Required Changes (add a step to `issue-to-plan`) | `skills/issue-to-plan/workflow.md` | Phase 3 | AC-3 | reference and heading checkers | Explicit in issue |
| REQ-004 | Target Files (`templates/plan.md` notes) | `templates/plan.md` | Phase 3 | AC-3 | `check_workitem_structure.py` | Explicit in issue |
| REQ-005 | Required Changes (register the tool) | `tools/TOOL_DESCRIPTIONS.md` | Phase 2 | AC-4 | `check_tool_descriptions_sync.py` | Explicit in issue |
| REQ-005 | Required Changes (register in `routing.md`); Constraints (read-only, time) | `routing.md` | Phase 2 | AC-4, AC-5 | drift check | Explicit in issue |
| REQ-005 | Step 2 (drift requires a gate mapping for a routing row) | `tools/run_validation_gates.py` | Phase 2 | AC-4 | drift check; `test_drift_all_routing_checkers_mapped` | Confirmed by repository evidence |
| REQ-006 | Acceptance Criteria (live run with three seeds, recall reported) | `tools/scan_change_consumers.py` | Phase 4 | AC-6 | live smoke run | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261102-085054 -->