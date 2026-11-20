## Goal

- Make `tools/check_adr_invariant_matrix.py` report an Automated Tests table it cannot read (`REQ-004`, missing evidence column) and Index evidence that has no ADR body evidence behind it (`REQ-005`, reverse direction); make the Cadence rule an error and fix the docstring (`REQ-006`, `REQ-007`).
- Gated: apply the governance exception grammar (`REQ-008`) and reject a `Not verified` row that is `Blocking` (`REQ-009`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the checker and its test file (a companion, see `### Companion test files`).
- Plan steps 5, 6, 7 (the checker part), 9 and 12. Steps 9 and 12 are gated on owner decisions UNK-01 and UNK-02.
- Execution order follows the Plan's phases, not `seq`: steps 5 and 6 run only after the data procedures of Plan steps 1 to 4 have landed (the ADR-004, ADR-017, ADR-016, ADR-015, ADR-007, ADR-012, ADR-003 and Index procedures), because each new rule must pass on the live repository.

## Assumptions

- Evidence: the reverse rule, emulated on the pre-change repository in the plan-to-implementation-procedure cycle, flags exactly ADR-004 INV-07, INV-08, INV-09, INV-10 and INV-14, ADR-007 INV-06, ADR-012 INV-04 and ADR-015 INV-01; the data procedures clear every one of them (checked in Step 3a).
- The checker is 22713 bytes against the 24576 byte gate for `tools/`. The new rules are expected to exceed it; the split in Procedure step 7 is part of this document and is recorded as a fallout amendment through `tools/amend_plan.py` before the new module is created.
- `ADR_INDEX`, `_matrix_rows`, `_read_lines`, `_split_row` and `_EXCEPTION_RE` stay defined in the checker: `tools/generate_reference_table.py` imports the first four and `.github/run_cited_adr_tests.py` loads the checker by file path and reads `_EXCEPTION_RE`.
- The repository owner decision of 2026-10-28 (extra Index citations on a shared row are not errors) stays; the reverse rule fires only when the body has no test evidence for the invariant (Plan Assumption A3).
- Steps 9 and 12 are gated; no approval text is written by the implementer.

## Design decisions

- Missing column: a table under `### Automated Tests` that lacks `Verifies` or `Implementation` is an error at its header line; a missing table stays silent, because the reverse rule already reports an Index invariant with no body evidence.
- Reverse rule: an Index-cited test file for ADR-N INV-M with an empty union of body-cited files for INV-M is an error at the Index row; containment of body files in Index files is unchanged.
- Cadence: an error now, no end date and no migration constant.

## Alternatives considered

- Strict set equality between Index and body files: rejected, it contradicts the 2026-10-28 owner decision and the test `test_extra_index_citation_on_a_shared_row_is_accepted`.
- Keep the Cadence warning and record an end date in governance: rejected, it adds a governance edit outside the Plan and keeps a tolerant mode.

## Implementation
### Target file
`tools/check_adr_invariant_matrix.py`
### Procedure
1. (Plan step 5) Add `check_adr_body_table_columns` (new): with `_first_table_after(lines, _AUTOMATED_TESTS_HEADING)`, when the header is non-empty and lacks `Verifies` or `Implementation`, return one `Issue` (severity `_BODY_RULE_SEVERITY`) at the header line, naming the missing columns. Take the header line number from `_table_lines(lines, _AUTOMATED_TESTS_HEADING)[0][0]`. Call it from `collect_issues` for every readable ADR body, next to `check_adr_body_evidence_cells`. `_body_automated_tests_rows` keeps returning `[]` for such a table.
2. (Plan step 6) Add `check_index_only_evidence` (new): for each key `(adr, inv)` of `_index_evidence(index_lines)` whose cited file set is non-empty and whose `adr` has a body in `bodies`, build the union of `_CITED_TEST_FILE_RE` matches over the `_body_automated_tests_rows` cells naming `inv`; when it is empty, return an `Issue` at `index_line[(adr, inv)]` (severity `_BODY_RULE_SEVERITY`) that names the invariant and the Index files. Call it from `collect_issues` after `check_body_index_agreement`. Update the module docstring: describe both new rules and replace the "Three further rules" wording.
3. (Plan step 7) Remove `_CADENCE_RULE_SEVERITY` and its comment; `check_manual_partial_fields` reports `"ERROR"`, and its docstring drops the migration-window wording. In the module docstring drop the "(see ... GV-012 Follow-up Work)" clause and keep the pointer to `.github/run_cited_adr_tests.py`.
4. (Plan step 9, gated on UNK-01) Apply the grammar the owner selects in `_EXCEPTION_RE` and in the use of it by `check_invariant_matrix_test_paths`; amend the Plan with `tools/amend_plan.py` (class fallout) to add `.github/run_cited_adr_tests.py`, `tools/generate_reference_table.py` and `tests/tools/test_run_cited_adr_tests.py` before touching them.
5. (Plan step 12, gated on UNK-02) Add `check_not_verified_blocking` (new): an Index matrix row whose Verification Status cell starts with `Not verified` and whose Gate is not `Non-Blocking`, and an ADR body row whose Implementation cell starts with `Not verified` and whose `Blocking` cell starts with `Yes`, are errors unless the Index cell matches `_EXCEPTION_RE`.
6. After each of steps 1 to 3, run `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`.
7. When the size gate fails, move the ADR body rules (`check_adr_body_evidence_cells`, `check_adr_body_table_columns` (new), `check_body_index_agreement`, `check_index_only_evidence` (new), `_body_automated_tests_rows`) into a new `tools/` module with `tools/module_nodes.py measure` and `extract`; the checker imports them and keeps the five names listed in Assumptions.
### Method
- Reuse `_first_table_after`, `_table_lines`, `_index_evidence` and `_CITED_TEST_FILE_RE`; no new parsing code.
- `Issue` is the existing record from `tools._docs_consistency_lib`; exit codes stay driven by severity.
### Details
- Message shape follows the existing rules, for example `ADR-004 INV-14: the index cites test files [...] but the ADR body records no test evidence for it`.
- `check_index_only_evidence` (new) skips an ADR number that is not in `bodies` (an unreadable body is already reported by `collect_issues`).

### Companion test files
- `tests/tools/test_check_adr_invariant_matrix.py`
  - Procedure: write each fixture first and see it fail. Replace `test_table_without_implementation_column_is_skipped` (class `TestBodyTableBoundaries`) with fixtures that expect an error for a missing `Implementation` column and for a missing `Verifies` column, keeping `test_missing_table_returns_no_issue`; add `TestIndexOnlyEvidence` (new) (no body row, body row `Not verified`, body cites a file, extra Index files on a shared row stay accepted); change `TestManualPartialCadence` to expect `ERROR`. Gated: grammar fixtures (step 4) and `Not verified` plus `Blocking` fixtures (step 5).
  - Validation: `uv run pytest tests/tools/test_check_adr_invariant_matrix.py tests/tools/test_run_cited_adr_tests.py tests/tools/test_generate_reference_table.py tests/tools/test_tool_report_output.py -q`.

## Compatibility considerations

- The checker's CLI, JSON shape and exit-code semantics are unchanged; two names are added to the findings, none removed.
- Importers (`tools/generate_reference_table.py`, `.github/run_cited_adr_tests.py`, three test modules) keep the names they use.
- A repository that fails a new rule is a data defect to fix in the data procedures, not a reason to weaken the rule.

## Security considerations

N/A: a read-only documentation checker; no input crosses a trust boundary.

## Rollback considerations

- Each step is its own commit; revert the commit of a rule to drop it. The module split (step 7) is reverted together with the rule that forced it.

## Validation plan

- `uv run ruff format tools/check_adr_invariant_matrix.py` and `uv run ruff check tools/check_adr_invariant_matrix.py`; the same `ruff check` for the test file.
- `uv run mypy tools/check_adr_invariant_matrix.py tests/tools/test_check_adr_invariant_matrix.py`; `uv run bandit tools/check_adr_invariant_matrix.py`.
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`.
- `uv run python tools/check_adr_invariant_matrix.py` exits 0; `uv run python tools/check_tool_descriptions_sync.py` after a new module is added.

## Completion criteria

- A fixture without the `Implementation` column and one without `Verifies` each exit 1 and failed before the change (AC-2).
- Index-only evidence fixtures exit 1, the containment fixture exits 0, and the live repository exits 0 (AC-3).
- A Manual or Partial row without `Cadence:` or `Expected evidence:` is an `ERROR`; `rg -n "migration window|GV-012 Follow-up" tools/check_adr_invariant_matrix.py` returns nothing (AC-4).
- Gated steps are done only after UNK-01 or UNK-02 is resolved (AC-4, AC-5).

## Out of Scope

- Index and ADR data corrections (their own procedures), the tool description and `governance_04` text, `.github/run_cited_adr_tests.py` and `tools/generate_reference_table.py` unless step 4 amends the Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the missing-column rule (Plan step 5) | Pending | — | — | After the data procedures of Plan steps 1 to 4 |
| 2 | Add the Index-only evidence rule (Plan step 6) | Pending | — | — | After the data procedures of Plan steps 1 to 4 |
| 3 | Make the Cadence rule an error and fix the docstring (Plan step 7) | Pending | — | — | |
| 4 | Apply the exception grammar (Plan step 9) | Pending | — | — | Gated: plans/20261120-095739_adrchk013_invariant-matrix-checks.md phase 9 - UNK-01 owner decision pending |
| 5 | Add the Not verified plus Blocking rule (Plan step 12) | Pending | — | — | Gated: plans/20261120-095739_adrchk013_invariant-matrix-checks.md phase 12 - UNK-02 owner decision pending |
| 6 | Add or update tests per Validation plan (companion test file) | Pending | — | — | Fixtures first, shown failing |
| 7 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (missing evidence column), `REQ-005` (Index-only evidence), `REQ-006` (Cadence error), `REQ-007` (docstring), `REQ-008` (exception grammar, gated), `REQ-009` (Not verified plus Blocking, gated)
- **Source issue**: issues/20261117-123013_adrchk013_invariant-matrix-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-095739_adrchk013_invariant-matrix-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-111659
- **Related target files**: `tools/check_adr_invariant_matrix.py`, `tests/tools/test_check_adr_invariant_matrix.py`
