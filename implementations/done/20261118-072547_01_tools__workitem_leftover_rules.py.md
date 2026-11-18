# Procedure: tools/_workitem_leftover_rules.py - plan and procedure leftover rules (new module)

## Goal

Create the rule module that reports an unfilled plan or procedure scaffold as leftover findings: a Traceability field whose whole value is a `{...}` placeholder, a table data row whose cells are all empty, and, for a plan, a line equal to a bracket-wrapped placeholder line of the `templates/plan.md` fence.

## Scope
**Release unit**: N/A: not part of a release unit

- New module with the three structural rules of the Plan's option D, one entry point per kind, each finding carrying the file, the line number, and the line text. (REQ-001)
- Relocate the existing issue leftover rule (`find_template_leftovers` and `_issue_template_leftover_lines`) from the checker into this module verbatim — same detail wording, same `rule` parameter behavior — so the module hosts all three kinds' leftover rules (verification addition, 20261118-133100: the checker measures 24275 B of the 24576 B size gate, leaving 301 B — less than the wiring in the sibling procedure document costs — so the issue rule must move out for the wiring to land; the Plan's "new module so the checker stays under the size gate" rationale extended to the issue rule).
- Run-time derivation of the bracket-line set from the plan template fence; no recorded line list. (REQ-001)
- Keep every function under radon grade C and pass the `tools/` conventions. (REQ-006)

## Assumptions

- Option D (structural rules) is the chosen design; the maintainer confirmation recorded as UNK-01 is outstanding and this module is not executed until that confirmation lands. Resolved 20261118-133100: the Plan was archived as a verified plan (commit `51c0497f6`) and the maintainer's `memo3.md` execution instruction directs this batch, so option D is confirmed and execution proceeds.
- The finding shape follows the checker's existing `template-leftover` findings (a dict with `category`, `file`, `detail`): the line number and line text go into `detail` for the new plan and procedure rules; the relocated issue rule keeps its existing wording (`verbatim issue-template leftover: {stripped}`, no line number) unchanged so its pinned tests keep passing. (Checked 20261118 against `tools/check_workitem_structure.py`.)
- The rule module imports only the standard library; it does not import the checker. The checker passes template paths or a pre-derived set in, mirroring how `find_template_leftovers` accepts a reusable `rule` parameter so a directory scan loads the template once. (Checked 20261118.)
- Dash placeholder rows (`| — |`) are not empty rows: the empty-row rule matches cells with no characters at all after stripping. (Plan Risk mitigation; `templates/execution-status.md` states these rows stay in filled documents.)

## Design decisions

- One entry point per kind (`plan_leftover_findings(doc_path, *, bracket_lines=...)` and `procedure_leftover_findings(doc_path)`), named so the checker's kind branch reads the same way its `issue` branch does. The bracket set is produced by a `load_plan_bracket_lines(template_path)`-style helper the caller loads once; the default is to read `templates/plan.md` on the spot, mirroring the `rule=None` pattern of `find_template_leftovers`.
- Whole-value placeholder rule: a `## Traceability` bullet whose value after `** field **: ` is exactly one `{...}` token (for example `- **Related target files**: {target_file_path}`). Values that merely contain braces inside other text are not reported, matching the existing test `test_braces_in_the_documents_own_content_are_not_reported` for issues.
- All-empty table row rule: a pipe row whose every cell is empty after stripping, skipping the `---` separator rows; this reports the generator's `| — | — |`-free empty scaffold rows but never the dash rows.
- Bracket rule for plans only: the comparison set is derived at run time from the fenced blocks of `templates/plan.md`, keeping fence lines that are bracket-wrapped placeholder lines; option B measured 9 such lines and no procedure line, which is why procedures skip this rule. (Plan Design, option B kept as rule (c).)
- The rules never compare the Freeze paragraph or other prose. (Plan Implementation Intent)
- Verification (20261118-133100, pre-execution stale detection passed): `templates/plan.md` and `templates/implementation-procedure.md` fences exist and re-measured — plan scaffold: 2 whole-value `{...}` Traceability lines (`{path}`, `{timestamp}`) and 4 all-empty table rows, matching the Plan; procedure scaffold: 5 whole-value `{...}` Traceability lines, matching the Plan. The current plan fence holds 7 bracket-wrapped lines (the Plan measured 9; the set is derived at run time and no rule or test depends on the count). Checker structure confirmed current: `find_template_leftovers` with the reusable `rule` parameter at line 288, `_issue_template_leftover_lines` at line 265, the kind branching in `collect_single_file_findings`, and the checker at 24275 B (this document's sibling cites the stale 21266 B — the status-value Plan grew it), leaving 301 B under the 24576 B gate. UNK-03 resolved: the status-value Plan landed (commit `74a4e1f3a`), its checker additions are in place.

## Alternatives considered

- Option A (recorded list of never-surviving lines). Rejected in the Plan: needs upkeep with every template edit, and 37 plan lines survive in only some documents.
- Option C (marker comments in the templates). Rejected in the Plan: larger change, leaves in-flight documents unmarked.
- An empty-section rule. Rejected in the Plan: 28 archived procedures hold an empty section body (UNK-02); it would report filled documents.

## Implementation

### Target file

`tools/_workitem_leftover_rules.py` (new) (no scaffold is created here — the first edit creates it)

### Procedure

1. Module docstring: name the three rules, state that the plan bracket set is derived from `templates/plan.md` at run time, and that findings render through the checker's `template-leftover` category with the line number and line text in the detail.
2. Implement the Traceability whole-value rule and the all-empty-row rule as shared helpers both kinds call, and the bracket rule as a plan-only helper. Each returns finding dicts (`category` `template-leftover`, repository-relative `file`, `detail` naming the line number and text).
3. Implement the bracket-set loader: read the plan template, extract the fenced blocks, and keep the bracket-wrapped placeholder lines; a caller may pass a pre-derived set so a directory scan reads the template once.
4. Type hints throughout (`list[dict[str, str]]`, `frozenset[str] | None`), standard library only (`re`, `pathlib`).
5. Keep each function small enough that `radon cc -n C` reports nothing for this module.
6. Relocate the issue rule: move `find_template_leftovers` and `_issue_template_leftover_lines` from the checker into this module as-is (verification amendment to Scope), exposing them as `find_issue_leftover_findings` and `issue_template_leftover_lines` with the repository root passed in by the caller instead of the checker's `ROOT_DIR` global, mirroring how `find_status_value_findings` takes text and a relative path in from the checker.

### Method

Create the file, then validate; no other file is edited by this document (the checker wiring is a separate procedure document).

### Details

- The scaffold signals this module must catch, taken from the generator's templates: the plan scaffold carries all-empty table rows, whole-value `{...}` Traceability lines, and bracket-wrapped lines; the procedure scaffold carries whole-value `{...}` Traceability lines (its empty section bodies are not used). The exact scaffold text comes from `templates/plan.md` and `templates/implementation-procedure.md`, read at implementation time rather than copied into this module.
- Repository-relative path rendering must match the checker's (`relative_to(ROOT_DIR).as_posix()` style) so reports read alike; pass the root or the relative path in from the caller instead of re-discovering the repository root.

## Compatibility considerations

- New module; its only planned caller is `tools/check_workitem_structure.py`. No CLI surface of its own.
- Filled documents: the measured sample (newest 40 archived plans, newest 60 archived procedures, and the active set) reports nothing under these rules; AC-4 re-runs that measurement at implementation time and requires zero false reports.

## Security considerations

- Reads files only; no subprocess, no network. `bandit` must stay clean.

## Rollback considerations

- Delete the module and its import from the checker (both landed in one commit series); no state is involved.

## Validation plan

- `uv run pytest tests/tools/test_check_workitem_structure.py -v` (the rule tests of the companion test document import these entry points directly).
- `uv run ruff format tools tests/tools`, `uv run ruff check tools tests/tools`.
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`.
- `uv run bandit tools/_workitem_leftover_rules.py`.
- `uv run radon cc tools/_workitem_leftover_rules.py -s -n C` reports nothing.
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`.
- Corpus measurement rerun (plan Phase 3): newest filled plans and procedures plus the active set, zero reports, recorded in the commit message body. (REQ-004; the measurement script is not committed.)

## Completion criteria

- AC-1: the module reports the three line kinds for a scaffold and nothing for a filled document; the bracket set follows a changed fence (fence-derivation test).
- AC-4: the recorded re-measurement reports zero false reports.
- AC-6: ruff, mypy, bandit, radon, and the `tools/` size gate are clean.

## Out of Scope

- Issue leftover behavior (the verbatim issue-template rule keeps its wording and tests; only its code relocates into this module per the amended Scope bullet).
- The checker's call sites (separate procedure document), the tests (separate document), and `routing.md` / `tools/TOOL_DESCRIPTIONS.md` (separate documents).
- Empty-section detection (UNK-02) and any content-quality judgment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261118-140604 | 20261118-140604 | 20261118: verified, implemented, all validation gates pass; corpus re-measure zero reports on active and newest sets |
| 2 | Add or update tests per Validation plan | Completed | 20261118-140604 | 20261118-140604 | 20261118: verified, implemented, all validation gates pass; corpus re-measure zero reports on active and newest sets |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261118-140604 | 20261118-140604 | 20261118: verified, implemented, all validation gates pass; corpus re-measure zero reports on active and newest sets |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261118-140604 | 20261118-140604 | 20261118: verified, implemented, all validation gates pass; corpus re-measure zero reports on active and newest sets |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-004, REQ-006
- **Source issue**: issues/20261117-132204_wftoolfu004_plan-leftover-detection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-134334_wftoolfu004_plan-leftover-detection.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-072547
- **Related target files**: `tools/_workitem_leftover_rules.py`
