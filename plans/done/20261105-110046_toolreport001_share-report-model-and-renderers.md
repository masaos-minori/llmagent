## Goal
- A private shared reporting module under `tools/` provides one finding record, deterministic text, JSON, and CSV renderers, and a common `--format` option helper, and the four check tools named in the Issue migrate to it with byte-identical default output, identical exit codes, and an unchanged JSON key set.

## Priority
Medium

## Scope
- **In-Scope**: add `tools/_report.py` and its tests; record the consumer audit of current output formats; migrate `check_adr_authority.py`, `check_adr_reference.py`, `check_adr_invariant_matrix.py`, and `check_workitem_traceability.py` in two batches; add golden-output and determinism tests; document the module, the `--format` convention, and the JSON schema in `tools/TOOL_DESCRIPTIONS.md`.
- **Out-of-Scope**: migrating the other ten tools that define `render_json` (`check_skills_heading_cycles.py`, `check_mock_patch_targets.py`, `check_conftest_integrity.py`, `check_adr_structure.py`, `check_plan_target_overlaps.py`, `check_workitem_structure.py`, `check_known_deviation_sync.py`, `check_skills_references.py`, `scan_change_consumers.py`, `plan_dependency_order.py`) and the tools that define only `render_text`, `render_csv`, `make_finding`, or `collect_issues` (follow-up batches after this Plan); bootstrap, repo-root, and git helpers (`toolcommon001`); exit-code conventions (`toolcli001`); changing any check's logic or the severity model; changing the existing `Issue` dataclass in `tools/_docs_consistency_lib.py`.
- **Dependencies**: lands after the mypy scope Plan, and after the Plan phases that touch `check_workitem_traceability.py` first.
  - **Depends on**: plans/20261105-105442_toolmypy001_add-tools-to-mypy-scope.md | phase all | the shared module must be type-checked
  - **Depends on**: plans/20261105-105230_tracecompanion001_scope-companion-candidates-to-target-plan.md | phase all | both Plans modify `tools/check_workitem_traceability.py`
  - **Depends on**: plans/20261105-105811_toolcommon001_shared-helper-for-tools.md | phase 2 | that phase migrates the git call of `check_workitem_traceability.py`, the same file
  - Coordinate with `issues/20261104-152906_toolwrite001_make-mutating-tools-dry-run-and-atomic.md`, which may reuse the shared `--format` and option helpers.

## Background
Verified on 2026-11-05 (checked in Steps 2 and 3): `def render_json(` is defined in 14 files, `render_text` in 7, `render_csv` in 5, `collect_issues` in 7, `make_finding` in 4, and `build_arg_parser` in 9. Finding types differ: `tools/_docs_consistency_lib.py` defines a frozen `Issue` (`file`, `line_no`, `severity`, `message`); `check_adr_authority.py` uses `Finding` from `tools/_adr_authority_core.py` (`code`, `location`, `message`); `check_workitem_traceability.py` uses `dict[str, str]` findings built by `make_finding`. JSON key sets and sort orders therefore differ (`check_adr_reference.py` and `check_adr_invariant_matrix.py` sort by file and line; `check_adr_authority.py` sorts by code, location, and message). Only four tools accept a `--json` flag, but many accept `--format` with `choices=["json"]` or `["json", "csv"]`. A search of CI workflows, `.pre-commit-config.yaml`, `tools/run_validation_gates.py`, `skills/`, `rules/`, and `routing.md` found no caller that requests JSON or CSV output from the four batch-1 tools; the only match is the `generate_mcp_inventory` gate token in `run_validation_gates.py`. `tools/generate_reference_table.py` imports from `tools.check_adr_invariant_matrix` lazily, so that module's public symbols must remain. Corrected on 2026-11-06 (Step 3a of the procedure pass): `generate_reference_table.py` imports `ADR_INDEX`, `_matrix_rows`, `_read_lines`, and `_split_row` from that module (and its test patches `ADR_INDEX`), so those four names and `collect_issues` MUST stay. Only `check_workitem_traceability.py` has local `render_text`, `render_csv`, and `make_finding`; the two ADR matrix and reference checkers have only a local `render_json` (their default text comes from `report_and_exit` in `tools/_docs_consistency_lib.py`, which stays), and `check_adr_authority.py` has a local `render_json` plus an inline text loop (`[code] location: message` on stdout, `Found N finding(s).` on stderr, which stays). `tests/tools/test_check_workitem_traceability.py` subscripts the dict findings of the `find_*` functions in 19 lines, so the finding model change reaches that test file (added as a target row by amendment). `.github/workflows/ci.yml` runs `tools/check_adr_authority.py` by path; pre-commit runs the other three by `-m` form.

## Problem
Each tool re-implements output formatting, so a formatting fix must be repeated, output contracts diverge, and consumers cannot parse results uniformly.

## Reason for Change
Maintenance and consistency risk; no failure is known and the work is not time-sensitive.

## Implementation Intent
Introduce `tools/_report.py` with one record able to carry both the `file/line_no/severity` and `code/location` styles, and renderers that take a key profile so each migrated tool keeps its current JSON keys and default text. Record the consumer audit first. Migrate four tools in two batches, comparing pre- and post-migration output on fixed fixtures.

## Requirements
- `REQ-001`: A consumer audit of the current text, JSON, and CSV outputs (pre-commit, CI workflows, `run_validation_gates.py`, skills, and importing tools) MUST be recorded before any tool changes, in `tools/TOOL_DESCRIPTIONS.md`.
- `REQ-002`: `tools/_report.py` MUST define one finding record carrying both styles without losing information, and text, JSON, and CSV renderers with deterministic ordering and a key profile that reproduces each migrated tool's current JSON keys.
- `REQ-003`: `tools/_report.py` MUST provide a `--format {text,json,csv}` option helper that lets a tool offer only the formats it already supports and keep its default format.
- `REQ-004`: `tests/tools/test_report.py` MUST cover ordering, empty input, Unicode, each format, and determinism (identical output on repeated runs).
- `REQ-005`: The four named tools MUST use the shared renderers and finding record with no local copy of `render_json`, `render_text`, `render_csv`, or `make_finding` left in them, with identical exit codes, identical default text output, and identical JSON key sets (any JSON key change is a contract change listed per tool).
- `REQ-006`: Golden-output tests recorded before migration MUST compare each migrated tool's text, JSON, and CSV output on fixed fixtures, and `uv run pytest tests/tools -q` and the validation gates MUST pass after each batch.
- `REQ-007`: `tools/TOOL_DESCRIPTIONS.md` MUST list the shared module, the `--format` convention, and the documented JSON schema once.

## Implementation Target Files
**Freeze status**: Frozen
Amended 2026-11-06 (fallout): added tests/tools/test_check_workitem_traceability.py — The existing tests subscript the dict findings of the find_* functions (findings[0]['category'], ['file'], ['detail'] in many assertions); once make_finding returns the shared record those assertions must read record attributes instead, or the file fails

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tests/tools/test_tool_report_output.py` | Golden-output and determinism tests for the migrated tools | New file; fixtures recorded before migration | `REQ-006`; AC-5 | The four tools' output functions and `main` (checked in Step 3) | itself | Verified |
| `tools/_report.py` | Shared reporting layer | New file; `tools/` exists and holds `_`-prefixed private modules | `REQ-002`, `REQ-003`; AC-2 | Private-module convention; `render_json` copies in 14 files (checked in Step 3) | `tests/tools/test_report.py` | Verified |
| `tests/tools/test_report.py` | Unit tests for the shared module | New file; `tests/tools/` exists | `REQ-004`; AC-3 | No existing tests for a shared reporter (checked in Step 3) | itself | Verified |
| `tools/check_adr_reference.py` | Migrate renderer | Replace `render_json` over `Issue` with the shared renderer and key profile `file/line_no/severity/message` | `REQ-005`; AC-4 | `collect_issues` and `render_json` sorted by file and line; `choices=["json"]` (checked in Step 3) | `tests/tools/test_check_adr_reference.py` | Verified |
| `tools/check_adr_invariant_matrix.py` | Migrate renderer | Replace `render_json` over `Issue` with the shared renderer; keep the symbols that `generate_reference_table.py` imports | `REQ-005`; AC-4 | `collect_issues`, `render_json`; lazy import from `generate_reference_table.py` (checked in Step 3) | `tests/tools/test_check_adr_invariant_matrix.py` | Verified |
| `tools/check_adr_authority.py` | Migrate renderer and finding record | Replace `render_json` over `Finding` with the shared renderer and key profile `code/location/message` | `REQ-005`; AC-4 | `render_json` sorts by code, location, message; `choices=["json"]` (checked in Step 3) | `tests/tools/test_adr_authority.py` | Verified |
| `tools/check_workitem_traceability.py` | Migrate renderers and finding model | Replace `make_finding`, `render_text`, `render_json`, `render_csv` and the `--format` argument with the shared layer | `REQ-005`; AC-4 | `make_finding` returns `dict[str, str]`; text, JSON, and CSV renderers; `choices=["json", "csv"]` (checked in Step 3) | `tests/tools/test_check_workitem_traceability.py` | Verified |
| `tests/tools/test_check_workitem_traceability.py` | Adapt finding assertions to the shared record | The existing tests subscript the dict findings of the find_* functions (findings[0]['category'], ['file'], ['detail'] in many assertions); once make_finding returns the shared record those assertions must read record attributes instead, or the file fails | REQ-005 / AC-4 | tests/tools/test_check_workitem_traceability.py has 19 lines subscripting finding dicts by category, file, or detail (checked in Step 3a) | itself | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Audit record, module entry, convention, schema | Add the consumer audit, the module row, the `--format` convention, and the JSON schema | `REQ-001`, `REQ-007`; AC-1, AC-6 | Index lists private modules; no schema text exists (checked in Step 3) | `uv run python tools/check_tool_descriptions_sync.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/_docs_consistency_lib.py` | Defines `Issue` and `report_and_exit`, which stay unchanged and are adapted by the shared module | `REQ-002` |
| `tools/_adr_authority_core.py` | Defines `Finding` (`code`, `location`, `message`) used by `check_adr_authority.py` | `REQ-002` |
| `tools/generate_reference_table.py` | Lazily imports `tools.check_adr_invariant_matrix` symbols | `REQ-005` |
| `tools/run_validation_gates.py` | Consumer of tool exit codes and the `--format` token handling; must not break | `REQ-001`, `REQ-005` |
| `.pre-commit-config.yaml` | Hooks that call the four tools | `REQ-001` |
| `.github/workflows/governance-docs-consistency.yml` | CI steps that call ADR checkers | `REQ-001` |

## Acceptance Criteria
- AC-1: The consumer audit is recorded and names every reader of the four tools' outputs, or states that none was found (`REQ-001`).
- AC-2: One implementation of each renderer and of the finding record exists in `tools/_report.py` and models both severity styles (`REQ-002`, `REQ-003`).
- AC-3: `tests/tools/test_report.py` passes for ordering, empty input, Unicode, each format, and determinism (`REQ-004`).
- AC-4: Each migrated tool contains no local `render_json`, `render_text`, `render_csv`, or `make_finding`, and produces the same exit code, default text output, and JSON key set as before (`REQ-005`).
- AC-5: Golden-output tests pass for text, JSON, and CSV where the tool offers them, and repeated runs give identical JSON (`REQ-006`).
- AC-6: The JSON schema and `--format` convention are documented once and `check_tool_descriptions_sync.py` passes (`REQ-007`).
- AC-7: `uv run pytest tests/tools -q` and the validation gates pass after each batch (`REQ-006`).

## Tests
- Unit tests of the shared module: ordering, empty input, Unicode, each format, key profiles, determinism (`REQ-002`, `REQ-003`, `REQ-004`).
- Golden-output tests per migrated tool on fixed fixtures, with the expected text recorded from the unmigrated tool first (`REQ-005`, `REQ-006`).
- Regression: the existing per-tool tests and `tests/tools/test_generate_reference_table.py` (lazy importer) after each batch (`REQ-005`, `REQ-006`).
- Live-data comparison: run each tool before and after and compare exit code and output (`REQ-005`).

## Documentation Impact
Yes: `tools/TOOL_DESCRIPTIONS.md` (audit record, shared module, `--format` convention, JSON schema; intent and operational notes only) (`REQ-001`, `REQ-007`). No `docs/*.md` file is affected.

## Assumptions
- A key profile (a per-tool ordered key list and sort key) lets one record reproduce each tool's current JSON without changing keys, so batch 1 is not a JSON contract change (judgment; the golden tests confirm it).
- The existing `Issue` and `Finding` classes stay as they are; `tools/_report.py` converts them, so no other importer breaks (judgment; Issue Out of Scope forbids changing the severity model).
- Tool defaults stay: `check_workitem_traceability.py` keeps text as default and JSON or CSV on request; the two ADR checkers keep text with `--format json` on request.
- Overlap judgments (`check_plan_target_overlaps.py`): `tools/TOOL_DESCRIPTIONS.md` is also targeted by the `toolsdocsync001`, `toolcli001`, and `toolcommon001` Plans (different sections: audit and schema versus heading, convention, helper row) and `tools/check_workitem_traceability.py` by the `tracecompanion001` and `toolcommon001` Plans (different functions); the changes are compatible, with the sequencing recorded in Scope.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Readers of the current JSON or CSV output outside the repository | Cannot be searched from the repository; none found inside it | Phase 1 audit records inside-repository readers; an external reader is raised with the owner before any JSON key change (none is planned) | False |
| UNK-02 | Whether one finding record models both severity styles without losing information | Design not yet exercised on all fourteen tools | Batch 1 covers three record styles (`Issue`, `Finding`, `dict`); a style that does not fit is recorded and left for the follow-up batch | False |
| UNK-03 | Order and grouping of the follow-up batches for the remaining ten tools | Owner priority | File one follow-up issue per batch after this Plan completes | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/_report.py` | Create | Medium (becomes the output contract of every migrated tool) | N/A | High (one author across the repository history) | not applicable (rsynced) |
| `tests/tools/test_report.py` | Create | Low | N/A | High | not applicable (rsynced) |
| `tests/tools/test_tool_report_output.py` | Create | Low | N/A | High | not applicable (rsynced) |
| `tools/check_adr_authority.py` | Modify | Medium (CI step and `generate_adr_authority.py` coupling) | N/A (outside top 60) | High | not applicable (rsynced) |
| `tools/check_adr_reference.py` | Modify | Medium (pre-commit hook `adr-reference-scoped`) | 5 | High | not applicable (rsynced) |
| `tools/check_adr_invariant_matrix.py` | Modify | Medium (pre-commit hook; imported lazily by `generate_reference_table.py`) | 6 | High | not applicable (rsynced) |
| `tools/check_workitem_traceability.py` | Modify | Medium (pre-commit hook) | 7 | High | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low | 82 | High | not applicable (rsynced) |
| `tests/tools/test_check_workitem_traceability.py` | Modify | Not assessed (amendment 2026-11-06) | N/A | N/A | Not assessed (amendment 2026-11-06) |

## Design
- Path B (more than 3 files, new module). Architecture analysis: `tools/` is outside the `.importlinter` contracts; `tools/_report.py` imports only the standard library and `orjson` (already a project dependency used by `render_json`), so no cycle arises. Dependency graphing: the four tools' importers are `tests/tools/*` and the lazy import in `generate_reference_table.py`; no CI or hook invokes `--format` on them. Historical analysis: churn figures are in the Affected areas table and all history is by one author. Operational dependency inspection: not applicable (no MCP server, database, or dependency change).
- Validation quality baseline: `radon cc` grades `check_adr_preservation.py` `compare` D (22) elsewhere and none of the four target tools' render functions in the C-or-worse list; migration MUST NOT introduce a C-or-worse function. `vulture` and `bandit` baselines on `scripts/` are unrelated and unchanged. diff-cover baseline: `N/A: no diff exists before implementation`; at least 90 percent on changed lines is required (`rules/toolchain.md`).
- Design decisions: (1) a record with optional `file`, `line_no`, `severity`, `code`, `location`, and required `message`, plus a key profile naming the output keys and sort key; (2) renderers `render_text`, `render_json` (orjson, indent 2, sorted by the profile's sort key), and `render_csv` (header from the profile); (2a, Step 3a) the record is a frozen dataclass with `file`, `line_no`, `severity`, `code`, `location`, `message`; a key profile is an ordered tuple of `(output_key, record_field)` pairs plus a sort key, so `check_workitem_traceability.py` uses the profile `category->code, file->file, detail->message` and keeps its keys `category`, `file`, `detail` (the JSON keeps `OPT_SORT_KEYS` and the original finding order, the CSV keeps its header), the ADR checkers use `file, line_no, severity, message` and `code, location, message`; the text renderer serves only the traceability grouped layout, the other tools keep their existing text path; (3) `add_format_argument(parser, choices, default)`. Alternatives rejected: changing `Issue` in place (affects every docs checker); a plugin registry (more surface than the Issue asks). Compatibility impact: none in batch 1 because key profiles reproduce each current output.
- Consumer scan: the output keys are a public contract of the tools; consumers were enumerated by the audit above (importers: tests and one lazy import; callers: none requesting JSON or CSV). Persisted schemas are not involved.

## Implementation steps
1. **Phase 1: Consumer audit**
   - [ ] Record the readers of each output format and the current key sets and sort orders (`REQ-001`; `tools/TOOL_DESCRIPTIONS.md`)
2. **Phase 2: Golden outputs and shared module**
   - [ ] Record golden outputs from the unmigrated four tools, add them as failing-ready tests, then add the shared module and its unit tests (`REQ-002`, `REQ-003`, `REQ-004`, `REQ-006`; `tests/tools/test_tool_report_output.py`, `tests/tools/test_report.py`, `tools/_report.py`)
3. **Phase 3: Batch 1 (the two ADR matrix and reference checkers)**
   - [ ] Migrate `check_adr_reference.py` and `check_adr_invariant_matrix.py`; run `tests/tools` (`REQ-005`, `REQ-006`; `tools/check_adr_reference.py`, `tools/check_adr_invariant_matrix.py`)
4. **Phase 4: Batch 2 (the authority and traceability checkers)**
   - [ ] Migrate `check_adr_authority.py` and `check_workitem_traceability.py`; run `tests/tools` and the gates (`REQ-005`, `REQ-006`; `tools/check_adr_authority.py`, `tools/check_workitem_traceability.py`)
   - [ ] Adapt finding assertions to the shared record (REQ-005; `tests/tools/test_check_workitem_traceability.py`) — amendment 2026-11-06
5. **Phase 5: Documentation and verification**
   - [ ] Document the module, the `--format` convention, and the JSON schema; run `check_tool_descriptions_sync.py`, the per-file checks of `routing.md` "Adding a new tool", and the live-data comparison (`REQ-005`, `REQ-007`; `tools/TOOL_DESCRIPTIONS.md` and all tool rows). No deploy step: only `tools/` and `tests/` change.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/_report.py` | Unit | `uv run pytest tests/tools/test_report.py -q` | All pass |
| four migrated tools | Golden-output and determinism | `uv run pytest tests/tools/test_tool_report_output.py -q` | All pass; output matches the pre-migration record |
| four migrated tools | Regression per batch | `uv run pytest tests/tools -q` | No new failure |
| four migrated tools | Live-data comparison | Run each tool before and after with its text and JSON modes | Identical exit code, text, and JSON keys |
| changed Python files | Lint, type, security (paths explicit) | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages <files>`, `uv run bandit <files>` | Clean |
| diff | Gates | `uv run python tools/run_validation_gates.py` | Pass |
| `tools/TOOL_DESCRIPTIONS.md` | Sync check | `uv run python tools/check_tool_descriptions_sync.py` | `No issues found.` |

## Risks
- **Risk**: A migrated tool's default text output changes by a byte and breaks a hook or test → **Mitigation**: golden tests recorded before migration (`REQ-006`) and a live-data comparison; two tools per batch.
- **Risk**: The shared record cannot model a tool's style without loss → **Mitigation**: key profiles per tool (UNK-02); a style that does not fit stays unmigrated and is recorded.
- **Risk**: A JSON key change becomes an unnoticed contract change → **Mitigation**: no key change in this Plan; any later change is listed per tool (Issue Constraints).
- **Risk**: `generate_reference_table.py` breaks because a lazily imported symbol moves → **Mitigation**: keep `check_adr_invariant_matrix.py`'s public symbols and run `tests/tools/test_generate_reference_table.py`.
- **Risk**: Several Plans edit the same tools → **Mitigation**: sequencing in Scope; re-run `check_plan_target_overlaps.py` at procedure generation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Record the consumer audit | Completed | — | 20261106-115301 |  |
| 2 | Record golden outputs; add the shared module and its tests | Completed | — | 20261106-115301 |  |
| 3 | Migrate batch 1 (two ADR checkers) | Completed | — | 20261106-115301 |  |
| 4 | Migrate batch 2 (authority and traceability checkers) | Completed | — | 20261106-115301 |  |
| 5 | Document and verify | Completed | — | 20261106-115301 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261106-091630_01_tests_tools_test_tool_report_output.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261106-091630_02_tools__report.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261106-091630_04_tools_check_adr_reference.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261106-091630_05_tools_check_adr_invariant_matrix.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261106-091630_06_tools_check_adr_authority.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261106-091630_07_tools_check_workitem_traceability.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261106-091630_09_tools_TOOL_DESCRIPTIONS.md.md | 1, 5 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261104-152906_toolreport001_share-report-model-and-renderers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261105-110046
- **Related target files**: tools/_report.py, tests/tools/test_report.py, tests/tools/test_tool_report_output.py, tools/check_adr_authority.py, tools/check_adr_reference.py, tools/check_adr_invariant_matrix.py, tools/check_workitem_traceability.py, tools/TOOL_DESCRIPTIONS.md, tests/tools/test_check_workitem_traceability.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; Unresolved Questions | `tools/TOOL_DESCRIPTIONS.md` | 1 | AC-1 | Audit record | Explicit in issue |
| REQ-002 | Required Changes 2; Implementation Intent | `tools/_report.py` | 2 | AC-2 | `test_report.py` | Explicit in issue |
| REQ-003 | Required Changes 3 | `tools/_report.py` | 2 | AC-2 | `test_report.py` | Explicit in issue |
| REQ-004 | Testing Expectations (shared module) | `tests/tools/test_report.py` | 2 | AC-3 | `test_report.py` | Explicit in issue |
| REQ-005 | Acceptance Criteria 1, 2; Background (Step 3) | `tools/check_adr_authority.py` | 4 | AC-4 | Golden tests; live-data comparison | Confirmed by repository evidence |
| REQ-005 | Same | `tools/check_adr_reference.py` | 3 | AC-4 | Golden tests; `test_check_adr_reference.py` | Confirmed by repository evidence |
| REQ-005 | Same | `tools/check_adr_invariant_matrix.py` | 3 | AC-4 | Golden tests; `test_check_adr_invariant_matrix.py` | Confirmed by repository evidence |
| REQ-005 | Same | `tools/check_workitem_traceability.py` | 4 | AC-4 | Golden tests; `test_check_workitem_traceability.py` | Confirmed by repository evidence |
| REQ-006 | Testing Expectations (pre- and post-migration comparison; determinism) | `tests/tools/test_tool_report_output.py` | 2, 3, 4 | AC-5, AC-7 | Golden tests; `uv run pytest tests/tools -q` | Explicit in issue |
| REQ-007 | Required Changes 4; Documentation Impact | `tools/TOOL_DESCRIPTIONS.md` | 5 | AC-6 | `check_tool_descriptions_sync.py` | Explicit in issue |
| REQ-005 | Amendment 2026-11-06: The existing tests subscript the dict findings of the find_* functions (findings[0]['category'], ['file'], ['detail'] in many assertions); once make_finding returns the shared record those assertions must read record attributes instead, or the file fails | tests/tools/test_check_workitem_traceability.py | Phase 4 | AC-4 | itself | Confirmed by repository evidence |