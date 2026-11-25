## Goal
- Make `tools/check_workitem_structure.py` judge Unknown and Risk companion documents (`issues/{timestamp}[_{NN}]_unknowns.md` and `issues/{timestamp}[_{NN}]_risks.md`) against `templates/unknowns-issue.md` and `templates/risks-issue.md`, so that the output of `tools/generate_workitem.py --kind unknowns|risks` passes the `workitem-structure` hook and a companion document that lacks a section of its own template is still reported.

## Priority
High

## Scope
- **In-Scope**: companion-kind detection by filename inside `issues/` (and `issues/done/` for `--file`); required headings for the two companion kinds taken from their templates; the `--kind` choices and the default kind set; new unit tests; the structure-gate row of `rules/tool-gates.md`; the `check_workitem_structure.py` rows and a new shared-base row of `tools/TOOL_DESCRIPTIONS.md`.
- **Out-of-Scope**: scaffold-leftover rules for companion documents; the `procedure-length` advisories; deciding a "decision record" shape for multi-decision unknowns documents (the only such file was removed by `e85d0c148`); editing or restructuring any archived companion document; changing the hook regex or baselines; `skills/issue-to-plan` companion generation.
- **Dependencies**: N/A: none. The earlier Issue about the same defect was removed from `issues/` before this Plan; no open Plan or Issue overlaps the target files at this time (re-checked by the overlap tool in Step 8b).

## Background
Companion documents are a distinct work-item kind: `skills/issue-to-plan` Step 6 writes them through `tools/generate_workitem.py --kind unknowns|risks` from `templates/unknowns-issue.md` and `templates/risks-issue.md`, and `skills/issue-creator` excludes them from the Issue naming convention. `tools/check_metadata_field_policy.py` already treats both templates as their own profiles. The structure checker defines three kinds in `_WORK_ITEM_KINDS` (`tools/check_workitem_structure.py:119-124`) and `infer_kind()` (`:372-384`) maps a path to a kind by its top-level directory only, so a companion document under `issues/` is judged against `templates/issue.md`. The pre-commit hook `workitem-structure` matches `^(issues|plans|implementations)/[^/]+\.md$` (`.pre-commit-config.yaml:126-130`), so it covers companion documents.

Verified on 2026-11-25 (master `9cdeac5e0`): the two live companion documents that first exposed the defect were deleted by `e85d0c148`, so the discover-mode scan now reports only 10 advisory `procedure-length` findings (exit 0) and the hook passes; the defect is latent. It is reproduced by the producer's own output: `generate_workitem.py --kind unknowns` writes a scaffold for which `check_workitem_structure.py --file` reports 15 `missing required section` findings. 26 of the 32 archived companion documents under `issues/done/` do not satisfy their own current template (they predate its revision); the default scan skips `done/`.

## Problem
The checker has no notion of the companion kinds. Every companion document committed under `issues/` fails the `workitem-structure` hook with `missing required section` findings for sections its own template never requires, and a genuinely malformed companion document cannot be told apart from those false positives.

## Reason for Change
`issue-to-plan` Step 6 produces companion documents whenever a Plan has a blocking Unknown or an unmitigated Risk, so the next such document blocks its own commit and the CI lint job (`pre-commit run --all-files`). The gate is latent today only because no companion document currently exists in `issues/`.

## Implementation Intent
Add the companion kinds beside, not inside, the existing directory-based kinds: a small new module owns the strict filename pattern and the template map, and the checker asks it for the kind before falling back to the directory. Keep the existing kinds, flags, output, and exit codes unchanged. The checker is 23,930 B against the 24,576 B module-size gate, so the new logic must be in a new module and the checker's own growth must stay minimal. Companion documents get only the missing-section rule (their templates define no leftover or status rules).

## Requirements
- `REQ-001`: A path `issues/{timestamp}_unknowns.md`, `issues/{timestamp}_{seq}_unknowns.md`, `issues/{timestamp}_risks.md`, or `issues/{timestamp}_{seq}_risks.md`, where `{seq}` is any run of digits because `generate_workitem.py --seq` does not validate its value (also under `issues/done/`) resolves to the `unknowns` or `risks` kind through a strict filename pattern; an ordinary Issue named `{timestamp}_{id}_{slug}.md` (its id always has a letter) and any path outside `issues/` keep their current kind.
- `REQ-002`: The required `## ` headings of the `unknowns` and `risks` kinds come from the fenced block of `templates/unknowns-issue.md` and `templates/risks-issue.md`; a missing heading is reported as `missing required section`, and no leftover, release-unit, status-value, or length rule applies to them.
- `REQ-003`: The existing behavior for `issue`, `plan`, and `implementation` documents, and the `--file`, `--kind`, `--include-done`, `--archived-status`, `--format` forms and exit codes, are unchanged; the default scan covers all five kinds, `--kind` accepts `unknowns` and `risks`, and `--kind issue` no longer includes companion documents.
- `REQ-004`: `tools/check_workitem_structure.py` stays within the 24,576 B module-size gate without a new baseline entry, with the companion logic in a new `tools/_workitem_companion_kinds.py`.
- `REQ-005`: Unit tests cover filename detection (accepted and rejected forms), `infer_kind` for companion paths, one passing companion document per template, one malformed companion document per template that is still reported, regression of the three existing kinds and of the default and `--kind` selection, and the real templates and real producer scaffold.
- `REQ-006`: The structure-gate row of `rules/tool-gates.md` and the `check_workitem_structure.py` rows of `tools/TOOL_DESCRIPTIONS.md` name the companion kinds and their templates, and `tools/TOOL_DESCRIPTIONS.md` has a row for the new module.
- `REQ-007`: The repository gates stay green: `tools/check_tool_descriptions_sync.py`, `tools/run_validation_gates.py drift`, the module-size gate for `tools/`, ruff, mypy, and bandit for the changed tool files, and the `workitem-structure` hook over a scaffold produced by `generate_workitem.py --kind unknowns|risks`.

## Implementation Target Files
**Freeze status**: Frozen (validated by `issue-to-plan` Step 8; see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/_workitem_companion_kinds.py` | Create the filename pattern, the template map, and the kind-by-filename helper for the two companion kinds | New file: the checker has 646 B of headroom under the 24,576 B gate, so the companion logic cannot live in it; `tools/` exists | `REQ-001`, `REQ-002`, `REQ-004`; AC-1, AC-2, AC-5 | `wc -c tools/check_workitem_structure.py` = 23,930 B, `tools/check_module_size.py` limit 24,576 B, and no baseline entry for the checker (checked in Step 3); filename forms at `tools/generate_workitem.py:245-261` (checked in Step 3) | `tests/tools/test_check_workitem_structure.py` | Verified |
| `tools/check_workitem_structure.py` | Modify `load_template_specs`, `infer_kind`, `discover_documents`, the `--kind` choices and default set, and the docstring/help to use the companion module | Kind selection is by directory only (`tools/check_workitem_structure.py:119-124`, `:372-384`), so a companion document is judged against `templates/issue.md` | `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`; AC-1 to AC-4 | `infer_kind` at `:372`, `discover_documents` at `:163`, `load_template_specs` at `:155`, `--kind` choices at `:499+`; reproduction: the scaffold of `generate_workitem.py --kind unknowns` yields 15 findings (checked in Step 2) | `tests/tools/test_check_workitem_structure.py` | Verified |
| `tests/tools/test_check_workitem_structure.py` | Modify: install the two companion templates in the fixture and add the companion tests | The file has no companion case and `_install_templates` copies only three templates, so loading the companion specs would fail under the temporary root | `REQ-005`; AC-1 to AC-5 | `_TEMPLATE_NAMES` and `_install_templates` at `tests/tools/test_check_workitem_structure.py:49-65`; `load_template_specs()` is called under a patched `ROOT_DIR` at lines 128, 141, 461, 519, 568 (checked in Step 3) | `uv run pytest tests/tools/test_check_workitem_structure.py -q` | Verified |
| `rules/tool-gates.md` | Modify the structure-gate row to name the companion templates and kinds | The row at line 31 lists only the three canonical templates | `REQ-006`; AC-6 | `rules/tool-gates.md:31` read in Step 3; the gate is run by the hook and `tools/_validation_gate_defs.py` (checked in Step 3) | `uv run python tools/run_validation_gates.py drift` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Modify the two `check_workitem_structure.py` rows (lines 125 and 200) and add a Shared-base row for the new module | The rows describe three kinds; an added `tools/*.py` needs a row (`check_tool_descriptions_sync.py`) | `REQ-006`, `REQ-007`; AC-6, AC-7 | Rows at `tools/TOOL_DESCRIPTIONS.md:125` and `:200`; the private-module precedent at `:77-79` (checked in Step 3) | `uv run python tools/check_tool_descriptions_sync.py` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `templates/unknowns-issue.md` | Source of the unknowns required headings (`Summary`, `Evidence Missing`, `Resolution Path`, `Blocking Impact`, `Related`, `Traceability`) | `REQ-002` |
| `templates/risks-issue.md` | Source of the risks required headings (`Priority`, `Context`, `Risk`, `Suggested resolution`, `Traceability`) | `REQ-002` |
| `tools/generate_workitem.py` | Defines the companion filename forms and writes the scaffold used as a test fixture | `REQ-001`, `REQ-007` |
| `.pre-commit-config.yaml` | The `workitem-structure` hook regex and entry; unchanged | `REQ-003`, `REQ-007` |
| `tools/_validation_gate_defs.py` | Gate patterns for the structure check; unchanged | `REQ-006`, `REQ-007` |
| `tools/check_module_size.py` | Defines the 24,576 B limit and baseline semantics | `REQ-004` |
| `skills/issue-to-plan/workflow.md` | Step 6 producer of companion documents (unchanged) | `REQ-001` |

## Acceptance Criteria
- AC-1 (`REQ-001`): the four companion filename forms resolve to `unknowns` or `risks`, also under `issues/done/`; `{timestamp}_{id}_{slug}.md` (including an id such as `gate001` and a slug ending in `unknowns`), a `plans/` path, and a non-`issues/` path keep their current kind.
- AC-2 (`REQ-002`): a companion document with every heading of its template yields no finding; removing one heading yields exactly that `missing required section` finding; the scaffold written by `generate_workitem.py --kind unknowns` and `--kind risks` yields no finding.
- AC-3 (`REQ-003`): the existing test suite for the three kinds passes unchanged apart from the fixture template list; `--kind issue` excludes companion documents, `--kind unknowns` and `--kind risks` select only them, the default selects all five, and the `--archived-status` and `--file` forms behave as before.
- AC-4 (`REQ-004`): `wc -c tools/check_workitem_structure.py` is at most 24,576 and `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` reports no new violation.
- AC-5 (`REQ-005`): `uv run pytest tests/tools/test_check_workitem_structure.py -q` passes with the new cases and fails when companion detection is removed.
- AC-6 (`REQ-006`): the gate row and tool rows name the companion kinds and templates; `check_tool_descriptions_sync.py` and `run_validation_gates.py drift` pass.
- AC-7 (`REQ-007`): ruff format and check, mypy, and bandit pass for the changed tool files; `uv run python tools/check_workitem_structure.py` exits 0 with only advisory findings; `uv run pre-commit run workitem-structure --all-files` passes; a temporary companion scaffold from `generate_workitem.py` passes `--file` and is then removed.

## Tests
- `REQ-001`: parametrized filename-detection tests (accepted: `{ts}_unknowns.md`, `{ts}_02_unknowns.md`, `{ts}_risks.md`, `{ts}_01_risks.md`; rejected: `{ts}_gate001_unknowns.md`, `{ts}_x_foo-unknowns.md`, `{ts}_unknowns.txt`, a non-numeric sequence such as `ab`; accepted: a one-digit and a three-digit numeric sequence) and `infer_kind` tests for `issues/`, `issues/done/`, `plans/`, `other/`.
- `REQ-002`: per template, a complete document passes, a document with one heading removed reports exactly that heading, and a real-template end-to-end case under the temporary root.
- `REQ-003`: default-kind selection includes the companion kinds; `--kind issue` excludes them; existing tests for plan, issue, implementation, `--file`, `--archived-status` stay green.
- `REQ-005`: a regression check that the companion tests fail without the companion module (mutation by name, reverted).
- `REQ-007`: a test that the live repository passes the companion rule for files present under `issues/` (no live companion documents exist now, so it passes vacuously and guards the next one).

## Documentation Impact
`rules/tool-gates.md` (the structure-gate row) and `tools/TOOL_DESCRIPTIONS.md` (the two checker rows and the new shared-base row) are updated for `REQ-006`. No `docs/*.md` file describes this checker (`rg check_workitem_structure docs` found none), so no `docs/` update is needed. If a decision-record companion shape is adopted later, `templates/unknowns-issue.md` owns it; that is out of scope here.

## Assumptions
- Companion documents need only the missing-section rule; the issue-template leftover rule is not applied to them because it is built from `templates/issue.md` lines (a judgment call of this Plan).
- `--kind issue` excluding companion documents is acceptable: a companion document is no longer an "issue" for this tool, and no caller passes `--kind issue` (the callers use `--file` or the default scan; checked in Step 3).
- Legacy archived companions fail their own template (26 of 32); `--include-done` reporting them is consistent with the existing behavior for the other kinds' archives and is left unchanged.
- The strict pattern `^\d{8}-\d{6}(_\d+)?_(unknowns|risks)\.md$` is the complete set of producer names (the sequence is an unvalidated `--seq` string; digits are the documented form) (only `tools/generate_workitem.py` writes them; checked in Step 2).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether a multi-decision unknowns document (the shape of the removed `_02_unknowns.md`) will be produced again and needs its own documented shape | No live example remains; the file was deleted in `e85d0c148` | Out of scope; if such a document is filed, the maintainer decides between documenting the shape in `templates/unknowns-issue.md` and reporting it as a finding | False |
| UNK-02 | Whether the maintainer wants companion documents inside the commit-time gate at all | The Issue's own choice (checker kind detection) is a stated preference, not a recorded decision | This Plan follows the Issue's preferred shape; reversing it later is a hook-regex change | False |
| UNK-03 | Whether `--include-done` should exempt the 26 legacy archived companions | No policy exists for archived documents of the companion kinds | Left as today (the default scan skips `done/`); revisit only if `--include-done` is adopted in a gate | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/_workitem_companion_kinds.py` | Create | Low: imported only by the checker | N/A: new file | N/A: new file | not applicable (rsynced) |
| `tools/check_workitem_structure.py` | Modify | Medium: run by the hook, the validation gate, `amend_plan.py`, `check_procedure_pass.py`, `generate_issue_batch.py` (all through the CLI) | 7 commits | 70% single author | not applicable (rsynced) |
| `tests/tools/test_check_workitem_structure.py` | Modify | Low | 7 commits | 75% single author (high) | not applicable (rsynced) |
| `rules/tool-gates.md` | Modify | Low: read by `run_validation_gates.py drift` | 3 commits | 67% single author | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Medium: checked by `check_tool_descriptions_sync.py` | 75 commits | 74% single author (high) | not applicable (rsynced) |

## Design
Path B (more than 3 target files and a new module). Analysis recorded in Step 3/5:
- **Architecture**: `tools/` is outside the import-linter root packages (`.importlinter` names `agent`, `db`, `mcp_servers`, ...), so no layering contract applies. The checker imports only `tools._workitem_*` helper modules and the standard library; the new module imports only `re` and `pathlib` and is imported by the checker, so no cycle is possible.
- **Dependency graph**: consumers of the checker are CLI callers only (`.pre-commit-config.yaml`, `tools/_validation_gate_defs.py`, `tools/amend_plan.py:508`, `tools/check_procedure_pass.py:35`, `tools/generate_issue_batch.py:51`); the only importer of its functions is `tests/tools/test_check_workitem_structure.py` (`scan_change_consumers.py --seed infer_kind --seed load_template_specs --seed discover_documents`: other `discover_documents` hits belong to `check_workitem_traceability.py`, which has its own function of that name: `not affected`).
- **Historical**: churn and bus factor are in the Affected areas table; the checker and its tests changed 7 times in 30 days each, so the change is kept small and additive.
- **Operational**: no port, database, or process is involved (`ss` and `fuser` not applicable); no dependency upgrade (`pip-audit` not applicable).

Design decisions:
1. New module `tools/_workitem_companion_kinds.py` exports `COMPANION_TEMPLATES` (kind to template path) and `companion_kind(path)` which applies `^\d{8}-\d{6}(_\d+)?_(unknowns|risks)\.md$` to the file name when the path's top-level directory is `issues` (also `issues/done/`). Alternative considered: extend `_WORK_ITEM_KINDS` with filename patterns inside the checker; rejected because of the size gate.
2. `infer_kind()` calls `companion_kind()` first and falls back to the directory map. `load_template_specs()` adds the two companion kinds from `COMPANION_TEMPLATES`. `discover_documents()` assigns each `issues/*.md` file to its companion kind when `companion_kind()` matches, otherwise to `issue`.
3. `--kind` gains the choices `unknowns` and `risks`; the default set becomes all five kinds. `--kind issue` therefore means ordinary Issues only (compatibility note in the docstring).
4. `collect_findings` and `collect_single_file_findings` run only `find_missing_sections` for the companion kinds; the existing `if kind == ...` branches already skip them.

Consumer scan and predictable fallout check (Step 3), each recorded as a target row, a reference row, or `not affected`:
- Module size: `tools/check_workitem_structure.py` 23,930 B of 24,576 B, not baselined: target row for the new module (`REQ-004`).
- Pinned counts: no test pins the number of kinds or templates; `_TEMPLATE_NAMES` is the fixture list and is a target row (`REQ-005`).
- Tool inventory: the added `tools/_workitem_companion_kinds.py` needs a `tools/TOOL_DESCRIPTIONS.md` row: target row (`REQ-006`).
- Generated blocks: none (`generate_reference_table.py --check` is not affected: `not affected: no generated domain is changed`).
- Consumers of `infer_kind`/`load_template_specs`: only the checker's own test file (target row); other tools call the CLI: `not affected`.
- Persisted schema and public API: none.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Companion kind module**
   - [ ] Create `tools/_workitem_companion_kinds.py` with `COMPANION_TEMPLATES` and `companion_kind()` (`REQ-001`, `REQ-002`, `REQ-004`; `tools/_workitem_companion_kinds.py`).
   - [ ] Add the filename-detection tests and the fixture template list change (`REQ-005`; `tests/tools/test_check_workitem_structure.py`).
2. **Phase 2: Wire the checker**
   - [ ] Extend `load_template_specs`, `infer_kind`, `discover_documents`, the `--kind` choices and default set, and the docstring/help (`REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`; `tools/check_workitem_structure.py`).
   - [ ] Add the companion pass/fail, selection, and real-scaffold tests, including the regression of the three existing kinds (`REQ-003`, `REQ-005`; `tests/tools/test_check_workitem_structure.py`).
   - [ ] Confirm `wc -c tools/check_workitem_structure.py` is at most 24,576 (`REQ-004`).
3. **Phase 3: Documentation rows**
   - [ ] Update the structure-gate row (`REQ-006`; `rules/tool-gates.md`).
   - [ ] Update the two checker rows and add the shared-base row for the new module (`REQ-006`; `tools/TOOL_DESCRIPTIONS.md`).
4. **Phase 4: Verification (no deployment: `tools/`, `tests/`, and `rules/` are not deployed and no `scripts/` or `config/` file changes)**
   - [ ] Run `uv run python tools/check_tool_descriptions_sync.py`, `uv run python tools/run_validation_gates.py`, `uv run python -m tools.run_validation_gates drift`, the `tools/` module-size gate, ruff, mypy, and bandit for the changed tool files, and `uv run pre-commit run workitem-structure --all-files` (`REQ-007`; `tools/check_workitem_structure.py`, `tools/TOOL_DESCRIPTIONS.md`, `rules/tool-gates.md`).
   - [ ] Write a temporary scaffold with `generate_workitem.py --kind unknowns` and `--kind risks`, confirm `--file` reports no finding, then delete the temporary file (`REQ-002`, `REQ-007`; `tools/check_workitem_structure.py`).

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/_workitem_companion_kinds.py` | Unit: accepted and rejected filename forms, directory rule | `uv run pytest tests/tools/test_check_workitem_structure.py -q -k companion` | All companion-detection cases pass |
| `tools/check_workitem_structure.py` | Unit and CLI: kind inference, discovery, selection, template specs; regression of existing kinds | `uv run pytest tests/tools/test_check_workitem_structure.py -q` | All cases pass; removing the companion module fails the new cases |
| `tools/check_workitem_structure.py` | Size gate | `wc -c tools/check_workitem_structure.py` and `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | At most 24,576 B; no new violation |
| `tools/check_workitem_structure.py`, `tools/_workitem_companion_kinds.py` | Lint, types, security | `uv run ruff format --check` and `uv run ruff check` on both files, `uv run mypy tools/check_workitem_structure.py tools/_workitem_companion_kinds.py`, `uv run bandit` on both files | Clean |
| `tools/TOOL_DESCRIPTIONS.md` | Inventory sync | `uv run python tools/check_tool_descriptions_sync.py` | No issues found |
| `rules/tool-gates.md` | Gate and hook parity | `uv run python -m tools.run_validation_gates drift` | Parity reported |
| whole change | Integration: hook and real scaffold | `uv run pre-commit run workitem-structure --all-files`; `generate_workitem.py --kind unknowns|risks` scaffold then `check_workitem_structure.py --file` | Hook passes; scaffolds report no finding |
| `tests/tools/test_check_workitem_structure.py` | Suite impact | `uv run pytest tests/tools -q -n logical` | No new failure (the pre-existing `test_generated_agent_index_stays_within_the_document_ceiling` failure is unrelated) |

Validation baseline (recorded in Step 5): `radon cc tools/check_workitem_structure.py -s` rates every function A (highest 4); `vulture scripts/ --min-confidence 80` reports 3 existing findings outside the targets; `bandit -r scripts/` reports existing findings outside the targets; `bandit tools/check_workitem_structure.py` is clean. The diff-cover baseline is `N/A: no scripts/ target` (coverage is measured over `scripts/` only, and this Plan changes `tools/`, `tests/`, and rules documents).

## Risks
- **Risk**: The new filename pattern misclassifies an ordinary Issue as a companion document → **Mitigation**: the pattern is anchored and requires exactly `{timestamp}[_{digits}]_unknowns|risks.md`; ordinary ids contain a letter; AC-1 tests the near-miss forms (`gate001`, slug ending in `unknowns`).
- **Risk**: Adding code to the checker pushes it over the 24,576 B gate → **Mitigation**: the logic lives in the new module and the checker's growth is limited to a few lines; AC-4 measures it. If it still exceeds the gate, a plan amendment adds a row for a second extracted module instead of a baseline entry.
- **Risk**: Loading the companion templates breaks existing tests that install only three templates under a temporary root → **Mitigation**: the fixture list is a target row and Phase 1 updates it before the checker is wired.
- **Risk**: `--kind issue` stops covering companion documents, which a script may rely on → **Mitigation**: the consumer scan found no caller using `--kind issue`; the docstring and tool rows state the new meaning.
- **Risk**: `--include-done` now reports 26 legacy archived companions → **Mitigation**: this is the existing behavior of the archive scan for other kinds, `--include-done` is not part of any gate or hook, and the default scan is unchanged (`UNK-03`).
- **Risk**: A future decision-record-shaped unknowns document is reported against the unknowns template → **Mitigation**: that is the intended gate behavior; the shape decision stays a maintainer decision (`UNK-01`).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the companion kind module and its detection tests | In Progress | — | — |  |
| 2 | Wire the checker and add selection and regression tests | In Progress | — | — |  |
| 3 | Update the gate row and tool description rows | In Progress | — | — |  |
| 4 | Verify gates, hook, and real scaffolds | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261125-104147_01_tools__workitem_companion_kinds.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261125-104147_02_tools_check_workitem_structure.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261125-104147_03_tests_tools_test_check_workitem_structure.py.md | 1, 2 | Procedure | Pending | — | — |
| implementations/20261125-104147_04_rules_tool-gates.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261125-104147_05_tools_TOOL_DESCRIPTIONS.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261125-091717_gate001_workitem-structure-companion-kinds.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261125-102213
- **Related target files**: `tools/_workitem_companion_kinds.py`, `tools/check_workitem_structure.py`, `tests/tools/test_check_workitem_structure.py`, `rules/tool-gates.md`, `tools/TOOL_DESCRIPTIONS.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (companion-kind detection); filename forms at `tools/generate_workitem.py:245-261` | `tools/_workitem_companion_kinds.py` | Phase 1 | AC-1 | `-k companion` filename and `infer_kind` tests | Confirmed by repository evidence |
| REQ-001 | Same | `tools/check_workitem_structure.py` | Phase 2 | AC-1 | `infer_kind` and discovery tests | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (own template headings); `templates/unknowns-issue.md`, `templates/risks-issue.md` | `tools/_workitem_companion_kinds.py` | Phase 1 | AC-2 | Template-map test | Confirmed by repository evidence |
| REQ-002 | Same; Issue Acceptance Criteria (malformed companion still reported) | `tools/check_workitem_structure.py` | Phase 2 | AC-2 | Pass and fail companion tests; real scaffold check | Confirmed by repository evidence |
| REQ-003 | Issue Constraints (existing forms keep working) | `tools/check_workitem_structure.py` | Phase 2 | AC-3 | Existing suite plus selection tests | Explicit in issue |
| REQ-003 | Same | `tests/tools/test_check_workitem_structure.py` | Phase 2 | AC-3 | Selection and regression tests | Explicit in issue |
| REQ-004 | Verification result: 23,930 B against the 24,576 B gate | `tools/_workitem_companion_kinds.py` | Phase 1 | AC-4 | Size gate | Confirmed by repository evidence |
| REQ-004 | Same | `tools/check_workitem_structure.py` | Phase 2 | AC-4 | `wc -c` and `check_module_size.py` | Confirmed by repository evidence |
| REQ-005 | Issue Testing Expectations | `tests/tools/test_check_workitem_structure.py` | Phases 1 and 2 | AC-5 | `uv run pytest tests/tools/test_check_workitem_structure.py -q` | Explicit in issue |
| REQ-006 | Issue Documentation Impact | `rules/tool-gates.md` | Phase 3 | AC-6 | `run_validation_gates.py drift` | Explicit in issue |
| REQ-006 | Same; predictable fallout check (tool inventory) | `tools/TOOL_DESCRIPTIONS.md` | Phase 3 | AC-6 | `check_tool_descriptions_sync.py` | Derived from confirmed evidence |
| REQ-007 | Issue Acceptance Criteria (hook and drift) | `tools/check_workitem_structure.py` | Phase 4 | AC-7 | Hook run, lint, types, bandit, real scaffold | Explicit in issue |
| REQ-007 | Same | `tools/TOOL_DESCRIPTIONS.md` | Phase 4 | AC-7 | `check_tool_descriptions_sync.py` | Explicit in issue |
| REQ-007 | Same | `rules/tool-gates.md` | Phase 4 | AC-7 | `run_validation_gates.py drift` | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261125-104147 -->