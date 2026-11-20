## Goal
- Make the ADR Invariant Verification Matrix in `docs/10_adr/adr_01_index.md` mirror the ADR bodies, and make `tools/check_adr_invariant_matrix.py` fail when it does not, in both directions, with a missing evidence column reported as an error.

## Priority
Medium

## Scope
- **In-Scope**: Implementation column for the ADR-004 and ADR-017 Automated Tests tables; Automated Tests tables for ADR-015 and ADR-016; Index matrix rows for ADR-016 and ADR-017 and the corrections the body comparison shows; checker rules for a missing column and for Index-only evidence; the Cadence rule as an error; the checker docstring; the exception grammar (gated on UNK-01); pending Blocking amendments and the Not verified plus Blocking rule (gated on UNK-02); the documentation of the tool and of the rule set.
- **Out-of-Scope**: changing invariant substance or decisions; applying any Blocking value change without an approval record; writing or paraphrasing a maintainer approval statement; ADR-014 Blocking values (re-verified as consistent, see Assumptions); `.github/run_cited_adr_tests.py` and `tools/generate_reference_table.py` unless UNK-01 selects a grammar change.
- **Dependencies**: N/A: none open. The Issue's dependency, the ADR approval governance work (adrchk011), is complete and archived; it defined the pending form in `governance_01` and the ledger in `governance_03`. A compatible overlap with the pending adrchk015 (ADR graph semantics) procedures is recorded in Assumptions.

## Background
The ADR body `### Automated Tests` table is the canonical record of verification evidence and the Index matrix mirrors it (`adr_01_index.md`, matrix preamble). The Issue was filed from a consolidated ADR review (`memo-issue.md`, package `ADRCHK2-M01`) and re-verified against current source in Step 2 of this cycle. The checker passes on the repository today because its body rules skip what they cannot read.

## Problem
- The checker skips an `### Automated Tests` table that lacks an `Implementation` or `Verifies` column (`_body_automated_tests_rows` returns an empty list), so ADR-004 (`Status` column) and ADR-017 (no evidence column) are never compared with the Index.
- The checker compares in one direction. `check_body_index_agreement` continues when `index_files` is non-empty and `body_files` is empty, so Index citations with no body evidence pass. Index-only evidence exists today: ADR-012 INV-04 (a directory is cited, no test, no body row), ADR-004 INV-14 (cited in the Index, no table row), ADR-007 INV-06 (the cited test appears in the body only under INV-03 and INV-04), and ADR-015 INV-01 (bullet-form Verification, no table).
- ADR-016 and ADR-017 have no Index matrix row, although ADR-017 INV-01 is Blocking and fatal at startup.
- ADR-003 INV-03 is `Confirmed` in the Index while the body has a `Not verified` row for the Safety Tier part of the same invariant.
- Five body rows are both `Not verified` and `Blocking` (ADR-002 INV-03 and INV-04; ADR-003 INV-03, INV-04 and INV-07), which breaks the Index rule; ADR-012 INV-04 joins them if no test is found.
- The Cadence check is a `WARNING` with no end date (the Index says "during the migration window"); the checker's `Exception: <id>` grammar differs from the `governance_03` exception record; the docstring cites a "GV-012 Follow-up Work" entry that does not exist (`governance_04` records no follow-up work).

## Reason for Change
The matrix gates CI and deployment reviews. A matrix that cannot detect a mismatch with the ADR it mirrors gives false assurance, and two ADRs with Blocking invariants are absent from it.

## Implementation Intent
- The ADR body is the source of truth; the Index mirrors it exactly, row by row.
- The checker reads every ADR body table, reports a table it cannot read, and reports Index evidence that has no body evidence behind it.
- Data is corrected first so each checker rule lands on a clean repository; Blocking value changes are shown only in the pending form until approved.

## Requirements
- `REQ-001`: The ADR-004 and ADR-017 `### Automated Tests` tables have an `Implementation` column that holds the test citations or an explicit status (no decision change).
- `REQ-002`: ADR-015 and ADR-016 record verification in an `### Automated Tests` table with an `Implementation` column, so the checker can read it (no decision change).
- `REQ-003`: The Index matrix gains ADR-016 and ADR-017 rows and every existing row mirrors its body: ADR-003 INV-03 `Partial` with its unverified scope, ADR-012 INV-04 and ADR-004 INV-14 and ADR-007 INV-06 evidence matched by body rows, rows keep their Gate unchanged.
- `REQ-004`: The checker reports as an error an `### Automated Tests` table that lacks the `Verifies` or `Implementation` column, with a fixture that fails today.
- `REQ-005`: The checker reports Index evidence that has no body evidence: an Index-cited test file for an invariant whose body has no row or whose body cells cite no test file, with a fixture that fails today. Extra Index citations on a shared row stay accepted (repository owner decision 2026-10-28).
- `REQ-006`: The Cadence rule reports `ERROR`, and the checker and the Index vocabulary no longer mention a migration window.
- `REQ-007`: The checker docstring cites only follow-up work that exists.
- `REQ-008`: The checker recognizes the exception grammar defined by governance, and the Index vocabulary states it (gated on UNK-01).
- `REQ-009`: Rows that are both `Not verified` and `Blocking` are proposed as pending amendments per the `governance_01` ADR Pending Amendment Form, and the checker rejects a `Not verified` row that is `Blocking` without an approved exception (gated on UNK-02).
- `REQ-010`: The tool description and the `governance_04` rule description state the new rules (fallout from REQ-004 to REQ-006).

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/check_adr_invariant_matrix.py` | Checker rules and docstring | Report an unreadable body table, report Index-only evidence, make the Cadence rule an error, fix the docstring, apply the exception grammar and the Not verified plus Blocking rule once their gates open | REQ-004, REQ-005, REQ-006, REQ-007, REQ-008, REQ-009 / AC-2, AC-3, AC-4, AC-5 | `_body_automated_tests_rows` returns `[]` without both columns; `check_body_index_agreement` skips `body_files` empty; `_CADENCE_RULE_SEVERITY = "WARNING"`; `_EXCEPTION_RE`; docstring cites GV-012 Follow-up Work, absent in `governance_04` (checked in Step 2 and Step 3) | `tests/tools/test_check_adr_invariant_matrix.py`, `tests/tools/test_run_cited_adr_tests.py` | Verified |
| `tests/tools/test_check_adr_invariant_matrix.py` | Fixture tests | Add fixtures that fail today (table without `Implementation` column, Index-only evidence) and update the Cadence tests that expect a warning | REQ-004, REQ-005, REQ-006, REQ-008, REQ-009 / AC-2, AC-3, AC-4 | `TestBodyTableBoundaries::test_table_without_implementation_column_is_skipped` locks the skip; `TestManualPartialCadence` expects warnings (checked in Step 3) | `tests/tools/test_check_adr_invariant_matrix.py` | Verified |
| `docs/10_adr/adr_01_index.md` | Matrix rows and vocabulary | Add ADR-016 and ADR-017 rows, correct ADR-003 INV-03, ADR-012 INV-04, ADR-004 INV-14 and ADR-007 INV-06 rows, drop the migration-window wording, state the exception grammar after UNK-01 | REQ-003, REQ-006, REQ-008 / AC-1, AC-4 | No ADR-016 or ADR-017 row; ADR-012 INV-04 row cites `tests/mcp_servers/git/` (a directory); the vocabulary says "WARNING during the migration window" (checked in Step 2) | `tools/check_adr_invariant_matrix.py`, `tools/check_adr_reference.py`, `tools/generate_adr_authority.py --check` | Verified |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Automated Tests table | Rename the `Status` column to `Implementation` and put each row's test citations in it, add the INV-14 row | REQ-001, REQ-003 / AC-1 | Header is `Test, Verifies, Type, Blocking, Status`; Index rows INV-07, INV-08, INV-09, INV-10 and INV-14 cite tests the table does not (checked in Step 2) | `tools/check_adr_invariant_matrix.py`, `tools/check_adr_structure.py`, `tools/check_adr_preservation.py` | Verified |
| `docs/10_adr/adr_02_03_017_mcp-authentication.md` | Automated Tests table | Add the `Implementation` column and move the test citations from the `Test` cell | REQ-001, REQ-003 / AC-1 | Header is `Test, Verifies, Type, Blocking`; the citations sit in the `Test` cell (checked in Step 2) | `tools/check_adr_invariant_matrix.py`, `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Verification section | Convert the bullet-form Verification to an `### Automated Tests` table citing `tests/tools/test_adr_authority.py` and `tests/tools/test_generate_adr_authority.py` nodes | REQ-002, REQ-003 / AC-1 | `## Verification` holds three `**Test**:` bullets and no table (checked in Step 2) | `tools/check_adr_invariant_matrix.py`, `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md` | Verification section | Convert the single bullet to an `### Automated Tests` table; fallout of REQ-005 (the Index cites `tests/tools/test_generate_reference_table.py::TestCheckDrift::test_live_docs_have_no_drift` for ADR-015 INV-01) | REQ-002 / AC-3 | `## Verification` holds one bullet and no table; Index ADR-015 INV-01 cites a test file (checked in Step 2) | `tools/check_adr_invariant_matrix.py`, `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | Automated Tests table | Name INV-06 in the `Verifies` cell of the row that cites `test_stdio_transport_rejected`; fallout of REQ-005 | REQ-003 / AC-3 | The Index INV-06 row cites that test; the body rows cite it under INV-03 and INV-04 only (checked in Step 2) | `tools/check_adr_invariant_matrix.py`, `tools/check_adr_preservation.py` | Verified |
| `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | Automated Tests table, pending amendment | Add the INV-04 row (a concrete test, else `Not verified`); show the Blocking change as pending when no test exists (gated on UNK-02) | REQ-003, REQ-009 / AC-3, AC-5 | Body rows cover INV-01 to INV-03 and INV-05 to INV-10; the Index cites only a directory for INV-04; a search of `tests/mcp_servers/git/` for an approval-independence test found none (checked in Step 3) | `tools/check_adr_invariant_matrix.py`, `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Manual Review, pending amendment | Add the manual review that covers the Safety Tier part of INV-03 for the Index `Partial` row; show the Blocking changes of INV-03, INV-04 and INV-07 as pending (gated on UNK-02) | REQ-003, REQ-009 / AC-3, AC-5 | Rows at lines 254, 256 and 259 are `Not verified` with Blocking `Yes`; `### Manual Review` names INV-05, INV-08 and INV-09 only (checked in Step 2) | `tools/check_adr_invariant_matrix.py`, `tools/check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Pending amendment | Show the Blocking change of INV-03 and INV-04 as pending (gated on UNK-02) | REQ-009 / AC-5 | Rows at lines 232 and 233 are `Not verified (no automated test exists)` with Blocking `Yes` (checked in Step 2) | `tools/check_adr_invariant_matrix.py`, `tools/check_adr_structure.py` | Verified |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Approval ledger entries | Add the ledger entries that the pending bullets cite (gated on UNK-02); an addition outside the Issue's Target Files, so the scope amendment needs approval through UNK-02 | REQ-009 / AC-5 | The ledger is Part 5 and its last entry is AAL-030; AAL-001 already records the same kind of change (ADR-001 INV-02 verification row set to Non-Blocking); `governance_01` requires a cited entry per pending bullet (checked in Step 3 and corrected in the plan-to-implementation-procedure Step 3a) | `tools/check_adr_structure.py`, `tools/check_known_deviation_sync.py`, `tools/check_docs_quality.py` | Verified |
| `tools/TOOL_DESCRIPTIONS.md` | Tool description | Update the two `check_adr_invariant_matrix.py` rows for the new rules; fallout, required by AGENTS.md Global Rule 9 | REQ-010 / AC-6 | Rows at lines 82 and 184 describe the rules and say the body table is read by its `Implementation` column (checked in Step 3) | `tools/check_tool_descriptions_sync.py` | Verified |
| `docs/00_governance/governance_04_documentation-checks.md` | Rule description | Update section 12 for the new rules; fallout | REQ-010 / AC-6 | Section 12 states the empty-cell and containment rules and no other (checked in Step 3) | `tools/check_docs_consistency.py`, `tools/check_docs_quality.py` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/00_governance/governance_01_documentation-policy.md` | Defines the ADR Pending Amendment Form (bullet text, `AAL-NNN` citation, Status stays `Accepted`) | REQ-009 |
| `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md` | Its INV-02 and INV-03 rows (Confirmed, Non-Blocking) are the re-verified non-defect; its `AAL-016` pending bullet is already recorded | Assumptions A2 |
| `.github/run_cited_adr_tests.py` | Loads the checker by file path and reads `_EXCEPTION_RE` | REQ-008, UNK-01 |
| `tools/generate_reference_table.py` | Imports `ADR_INDEX`, `_matrix_rows`, `_read_lines`, `_split_row` from the checker and keeps its own `_COV_EXCEPTION_RE` | REQ-005, REQ-008, UNK-01 |
| `tests/tools/test_run_cited_adr_tests.py` | `TestCitedExceptions` exercises the `Exception: <id>` grammar | REQ-008, UNK-01 |
| `tests/tools/test_generate_reference_table.py` | Imports the checker module as `matrix_mod` | REQ-005 |
| `tests/tools/test_tool_report_output.py` | Imports the checker module and reads its output format | REQ-004, REQ-005 |
| `tests/tools/test_adr_authority.py` | Source of the nodes cited by the ADR-016 table | REQ-002 |
| `tests/tools/test_generate_adr_authority.py` | Source of the nodes cited by the ADR-016 table | REQ-002 |
| `implementations/20261120-092705_01_docs_10_adr_adr_01_index.md.md` | Pending adrchk015 procedure that edits the Index front matter and edge-definition paragraph | Assumptions A1 |
| `implementations/20261120-092705_02_docs_10_adr_adr_02_07_016_adr-authority-model.md.md` | Pending adrchk015 procedure that edits ADR-016 and pins line numbers | Assumptions A1 |
| `implementations/20261120-092705_04_docs_10_adr_adr_02_01_004_platform-environment-failure-handling-policy.md.md` | Pending adrchk015 procedure that edits the ADR-004 front matter and Related ADRs | Assumptions A1 |
| `implementations/20261120-092705_06_docs_10_adr_adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md.md` | Pending adrchk015 procedure that edits ADR-007 | Assumptions A1 |

## Acceptance Criteria
- `AC-1`: `uv run python tools/check_adr_invariant_matrix.py` exits 0 after each of Phases 1 to 8; the Index matrix has ADR-016 and ADR-017 rows, and each matrix row names the status, Gate and test files its ADR body records (REQ-001, REQ-002, REQ-003).
- `AC-2`: A fixture whose `### Automated Tests` table lacks the `Implementation` column, and one that lacks `Verifies`, each make the checker exit 1; they fail on the checker before Phase 5 (REQ-004).
- `AC-3`: A fixture with Index-cited test files for an invariant that has no body row, and one whose body cells cite no test file, each make the checker exit 1; a fixture with extra Index files on a shared row still exits 0; the live repository exits 0 (REQ-002, REQ-003, REQ-005).
- `AC-4`: A Manual or Partial row without `Cadence:` or `Expected evidence:` is an `ERROR`; `rg -n "migration window|GV-012 Follow-up" tools/check_adr_invariant_matrix.py docs/10_adr/adr_01_index.md` returns nothing; after UNK-01 resolves, the checker accepts the governance exception grammar and rejects a malformed reference (REQ-006, REQ-007, REQ-008).
- `AC-5`: After UNK-02 resolves and Phases 10 to 12 land, no `docs/10_adr/*.md` Automated Tests row is both `Not verified` and `Blocking`, each changed Blocking value is shown in the pending form with an existing ledger entry, and the checker fails on a fixture row that is both (REQ-009). Open until UNK-02 resolves.
- `AC-6`: `tools/TOOL_DESCRIPTIONS.md` and `governance_04` section 12 state the rules that landed, and `uv run python tools/check_tool_descriptions_sync.py` and the docs checkers pass (REQ-010).

## Tests
- `REQ-004`: fixtures for a missing `Implementation` column and a missing `Verifies` column in `tests/tools/test_check_adr_invariant_matrix.py`, written first and shown failing; replace the test that locks the skip.
- `REQ-005`: fixtures for Index-only evidence with no body row, with a body row that cites no test file, and the unchanged containment cases; a live-repository run.
- `REQ-006`: update `TestManualPartialCadence` to expect `ERROR`.
- `REQ-008`: fixtures for the selected grammar and a malformed reference, after UNK-01.
- `REQ-009`: fixture for a `Not verified` row with Blocking `Yes`, and one with an approved exception, after UNK-02.
- `REQ-001`, `REQ-002`, `REQ-003`: no new test; the live-repository checker run and `tools/check_adr_structure.py` cover the data.

## Documentation Impact
Yes. Drivers: REQ-001 to REQ-003 (Index matrix and the ADR Automated Tests tables, per the Issue's Target Files), REQ-006 and REQ-008 (Index vocabulary), REQ-009 (ADR Approval Record pending bullets and the `governance_03` ledger), REQ-010 (the tool description and the rule description in `governance_04` section 12). Target documents are named by the Issue and by `docs/00_index.md` "Document References by Task" for the ADR and governance areas.

## Assumptions
- A1: The pending adrchk015 procedures overlap in files (the Index, ADR-016, ADR-004, ADR-007) but edit other regions: front matter, the edge-definition paragraph, the generated sections, Decision and Summary text, Implementation Notes, and Related ADRs; this Plan edits the matrix, Verification tables and vocabulary. It is a compatible overlap with adrchk015 (ADR graph semantics). The ADR-016 procedure pins line numbers that Phase 2 shifts, so its pinned lines are re-verified by that procedure's own revalidation; falsified if a pinned line no longer matches after Phase 2.
- A2: ADR-014 INV-02 and INV-03 stay unchanged. The Index Gate (`Non-Blocking`) equals the body Blocking value (`No`), and the Index rule only forces a `Not verified` row to be Non-Blocking; a Confirmed row with a Non-Blocking Gate does not break it. Falsified if the owner decides Confirmed rows must be Blocking, which is a separate decision change.
- A3: The repository owner decision of 2026-10-28 (extra Index citations on shared rows are not errors, recorded in the checker docstring and locked by a test) stays; the reverse rule is limited to Index evidence with no body evidence for that invariant. Falsified if the owner asks for strict mirroring.
- A4: An Index `Partial` row keeps its Gate (the vocabulary says Partial leaves the Gate unchanged), so ADR-003 INV-03 stays Blocking; its manual review text in ADR-003 is verification text, not decision text, and needs no approval record.
- A5: No Index matrix row uses `Exception: <id>` today (read in Step 2), so a grammar change needs no row migration. Falsified by `rg -n "Exception: " docs/10_adr/adr_01_index.md` returning a row.
- A6: The checker is 22713 bytes against the 24576 byte gate for `tools/`, a headroom of 1863 bytes; Phases 5 to 7 are expected to exceed it (Risks).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which exception grammar the matrix uses. The `governance_03` Temporary Exception Process (`<!-- exception: {rule-id} — {reason} — {owner} — expires {YYYY-MM-DD} -->`) is scoped to `Warning` findings, while the matrix exception approves an `ERROR` skip-marker finding without an expiry | The owner's statement whether matrix exceptions follow that record or governance defines a separate one | Owner decision. On a change, amend the Plan (`tools/amend_plan.py`, fallout) to add `.github/run_cited_adr_tests.py`, `tools/generate_reference_table.py` and `tests/tools/test_run_cited_adr_tests.py`, which read `Exception:`. Phase 9 stays gated until then | False |
| UNK-02 | Whether the Blocking changes are applied now in the pending form. The form applies changed text and needs ledger entries in `governance_03`, a file outside the Issue's Target Files, while the Issue forbids applying a Blocking change without an approval record | The owner's decision to proceed with the pending form and the scope amendment | Owner decision. Phases 10 to 12 stay gated until then; no approval text is written by the implementer | False |
| UNK-03 | Whether an existing test shows that Git MCP validation does not depend on Agent approval (ADR-012 INV-04) | A concrete test node; `tests/mcp_servers/git/` was searched for `independen` and `approval` and no matching test was found | Phase 3 repeats the search; a test found is cited in the new body row, otherwise the row is `Not verified` and INV-04 joins the UNK-02 set | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. Bus Factor is 1 for every file: one author accounts for all commits (`git shortlog -sn HEAD`).

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/check_adr_invariant_matrix.py` | Modify | Medium: the pre-commit hook, `run_validation_gates.py`, `.github/run_cited_adr_tests.py`, `generate_reference_table.py` and three test modules besides its own use it | 5 | 1 | not applicable (rsynced) |
| `tests/tools/test_check_adr_invariant_matrix.py` | Modify | Low | 4 | 1 | not applicable (rsynced) |
| `docs/10_adr/adr_01_index.md` | Modify | Medium: read by the ADR checkers, `generate_adr_authority.py` and `generate_reference_table.py` | 19 | 1 | not applicable (rsynced) |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Modify | Low | 12 | 1 | not applicable (rsynced) |
| `docs/10_adr/adr_02_03_017_mcp-authentication.md` | Modify | Low | 2 | 1 | not applicable (rsynced) |
| `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Modify | Low | 7 | 1 | not applicable (rsynced) |
| `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md` | Modify | Low | 5 | 1 | not applicable (rsynced) |
| `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | Modify | Low | 5 | 1 | not applicable (rsynced) |
| `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | Modify | Low | 5 | 1 | not applicable (rsynced) |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Modify | Low | 8 | 1 | not applicable (rsynced) |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Modify | Low | 8 | 1 | not applicable (rsynced) |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Modify | Medium: ledger read by `check_adr_structure.py` | 17 | 1 | not applicable (rsynced) |
| `tools/TOOL_DESCRIPTIONS.md` | Modify | Low: read by `check_tool_descriptions_sync.py` | 70 | 1 | not applicable (rsynced) |
| `docs/00_governance/governance_04_documentation-checks.md` | Modify | Low | 12 | 1 | not applicable (rsynced) |

## Design
- **D1 Data before checker**: each new checker rule lands on a repository its rule already passes, so Phases 1 to 4 correct data under the unchanged checker (it must keep exiting 0), and Phases 5 and 6 add the rules. Alternative: add the rules first and fix data in the same change (rejected: the phases could not be validated alone).
- **D2 Reverse rule**: report an Index row's cited test file for ADR-N INV-M when the ADR body has no row for INV-M or its rows cite no test file. Alternative: strict set equality between Index and body (rejected: it contradicts the 2026-10-28 owner decision, A3). A missing table is not itself an error: ADR-010 is Withdrawn and has no matrix row, and the reverse rule already reports an Index invariant that has no body table.
- **D3 Missing column**: an `### Automated Tests` table that exists but lacks `Verifies` or `Implementation` is reported at its heading line; a missing table stays silent (D2). This replaces the silent `[]` return of `_body_automated_tests_rows`.
- **D4 Cadence**: make it an error now. The current Index has no Manual or Partial row missing a field (the checker reports no finding), so no migration window is needed; recording an end date in governance would add a governance edit and keep a tolerant mode that the Current-Specification-Only policy excludes.
- **D5 Pending form**: Blocking changes use the `governance_01` form (bullet under `### Approval Record`, `AAL-NNN` entry, Status stays `Accepted`); no approval text is written.
- **D6 Consumer scan** of `_EXCEPTION_RE`: target rows are the checker and its test; reference rows are `.github/run_cited_adr_tests.py`, `tools/generate_reference_table.py` and `tests/tools/test_run_cited_adr_tests.py`; `tests/tools/test_generate_reference_table.py` and `tests/tools/test_tool_report_output.py` are not affected unless the grammar changes (they import the module, not the constant). Candidates under `docs/10_adr/` cite the ADR-015 test and are covered by Phase 2.
- **D7 Validation quality baseline** (checked in Step 5): `radon cc` on the checker shows `_node_markers` at C (18) and no other function above B (10); `bandit` on the checker reports no issue; `vulture scripts/ --min-confidence 80` reports five findings in `scripts/rag/` and `scripts/shared/`, none in a target; diff-cover is N/A because no `scripts/` file is a target and CI coverage measures `scripts/` only (`rules/toolchain.md` section 7).
- **D8 Persisted schema check**: not applicable; no DDL or schema version changes.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above. Phases 9 to 12 are gated: they start only after
the owner resolves UNK-01 (Phase 9) or UNK-02 (Phases 10 to 12). Every phase before them passes the checker on its own.

1. **Phase 1: Evidence columns for ADR-004 and ADR-017**
   - [ ] Rename the ADR-004 `Status` column to `Implementation`; give each row its test citations (taken from the Index rows INV-07 to INV-10) or its status text; add the INV-14 row citing the three tests the Index cites (REQ-001, REQ-003; `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`)
   - [ ] Add the ADR-017 `Implementation` column and move the citations out of the `Test` cell (REQ-001; `docs/10_adr/adr_02_03_017_mcp-authentication.md`)
2. **Phase 2: Tables for ADR-015 and ADR-016**
   - [ ] Convert the ADR-016 Verification bullets to an `### Automated Tests` table, keeping the `Verifies`, `Type` and `Blocking` values and the Coverage note (REQ-002; `docs/10_adr/adr_02_07_016_adr-authority-model.md`)
   - [ ] Convert the ADR-015 Verification bullet to the same table (REQ-002; `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`)
3. **Phase 3: Body rows that the Index already cites**
   - [ ] Name INV-06 in the `Verifies` cell of the ADR-007 row citing `test_stdio_transport_rejected` (REQ-003; `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`)
   - [ ] Repeat the INV-04 test search (UNK-03); add the ADR-012 INV-04 row with the test found, else `Not verified` (REQ-003; `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`)
   - [ ] Add the ADR-003 manual review for the Safety Tier part of INV-03 (REQ-003; `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`)
4. **Phase 4: Index matrix mirrors the bodies**
   - [ ] Add the ADR-016 and ADR-017 rows (Gate and Status from the bodies); change ADR-003 INV-03 to `Partial` with unverified scope, `Cadence:`, `Expected evidence:` and an Owner; align the ADR-012 INV-04, ADR-004 INV-14 and ADR-007 INV-06 rows with their body rows; update the Pipeline Mapping Summary; keep every Gate unchanged (REQ-003; `docs/10_adr/adr_01_index.md`)
5. **Phase 5: Missing evidence column is an error**
   - [ ] Write the failing fixtures, then report an `### Automated Tests` table without `Verifies` or `Implementation` (REQ-004; `tests/tools/test_check_adr_invariant_matrix.py`, `tools/check_adr_invariant_matrix.py`)
6. **Phase 6: Index-only evidence is an error**
   - [ ] Write the failing fixtures, then report Index-cited test files with no body evidence, keeping the containment cases (REQ-005; `tests/tools/test_check_adr_invariant_matrix.py`, `tools/check_adr_invariant_matrix.py`); when the size gate fails, split the body rules with `module_nodes.py` and report the new module as a fallout amendment
7. **Phase 7: Cadence error and docstring**
   - [ ] Make the Cadence rule an `ERROR`, drop `_CADENCE_RULE_SEVERITY` and the stepped-enforcement comment, remove the GV-012 follow-up citation from the docstring (REQ-006, REQ-007; `tools/check_adr_invariant_matrix.py`, `tests/tools/test_check_adr_invariant_matrix.py`)
   - [ ] Remove "during the migration window" from the Index vocabulary (REQ-006; `docs/10_adr/adr_01_index.md`)
8. **Phase 8: Documentation sync**
   - [ ] Update the two tool description rows (REQ-010; `tools/TOOL_DESCRIPTIONS.md`) and `governance_04` section 12 (REQ-010; `docs/00_governance/governance_04_documentation-checks.md`)
9. **Phase 9: Exception grammar (gated on UNK-01)**
   - [ ] Apply the grammar the owner selects in the checker, its tests and the Index vocabulary; add the Reference Files that read `Exception:` through `tools/amend_plan.py` (REQ-008; `tools/check_adr_invariant_matrix.py`, `tests/tools/test_check_adr_invariant_matrix.py`, `docs/10_adr/adr_01_index.md`)
10. **Phase 10: Ledger entries for the pending amendments (gated on UNK-02)**
    - [ ] Add one ledger entry per pending Blocking change; write no approval text (REQ-009; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`)
11. **Phase 11: Pending Blocking amendments (gated on UNK-02)**
    - [ ] Show each Blocking change in the pending form citing its ledger entry, in ADR-002 (INV-03, INV-04), ADR-003 (INV-03, INV-04, INV-07) and ADR-012 (INV-04 when `Not verified`), and mirror the Gate in the Index rows (REQ-009; `docs/10_adr/adr_02_01_002_platform-config-isolation.md`, `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`, `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`, `docs/10_adr/adr_01_index.md`)
12. **Phase 12: Not verified plus Blocking rule (gated on UNK-02)**
    - [ ] Write the failing fixtures, then report a `Not verified` row that is `Blocking` without an approved exception, in the Index and in ADR bodies (REQ-009; `tests/tools/test_check_adr_invariant_matrix.py`, `tools/check_adr_invariant_matrix.py`)
13. **Phase 13: Validation and hand-off**
    - [ ] Run the validation sequence and the checkers named in Validation plan; no deploy step, because no `scripts/` or `config/` file changes; commit through `git-commit-and-sync` (REQ-001 to REQ-010; every target file)

### Release units
**Unit**: pending-amendments | **Phases**: 10, 11 | **Reason**: a ledger entry without its pending bullet and a pending bullet without its ledger entry each fail `tools/check_adr_structure.py`, so they cannot be validated alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_adr_invariant_matrix.py` | Unit fixtures, failing first; live-repository run | `uv run pytest tests/tools/test_check_adr_invariant_matrix.py tests/tools/test_run_cited_adr_tests.py tests/tools/test_generate_reference_table.py tests/tools/test_tool_report_output.py -q`; `uv run python tools/check_adr_invariant_matrix.py` | Fixtures fail before and pass after each rule; the live run exits 0 |
| `tools/check_adr_invariant_matrix.py` | Lint, type, security, size | `uv run ruff format tools/check_adr_invariant_matrix.py`; `uv run ruff check tools/check_adr_invariant_matrix.py`; `uv run mypy tools/check_adr_invariant_matrix.py`; `uv run bandit tools/check_adr_invariant_matrix.py`; `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | No finding; module size within the gate |
| `tests/tools/test_check_adr_invariant_matrix.py` | Lint and type | `uv run ruff check tests/tools/test_check_adr_invariant_matrix.py`; `uv run mypy tests/tools/test_check_adr_invariant_matrix.py` | No finding |
| `docs/10_adr/*.md`, `docs/10_adr/adr_01_index.md` | Static checks | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_content_policy.py`; `uv run python tools/check_adr_structure.py`; `uv run python tools/check_adr_reference.py`; `uv run python tools/check_adr_authority.py`; `uv run python tools/generate_adr_authority.py --check`; `uv run python tools/check_adr_preservation.py`; `uv run python tools/check_known_deviation_sync.py`; `uv run python tools/check_docs_japanese.py` | No ERROR; `check_adr_preservation.py` reports no changed invariant, reference or Approval text except the pending bullets of Phase 11 |
| `docs/00_governance/*.md`, `tools/TOOL_DESCRIPTIONS.md` | Static checks | `uv run python tools/check_tool_descriptions_sync.py`; `uv run python tools/check_docs_consistency.py --domain deployment`; `uv run python tools/check_needs_confirmation_inventory.py` | No finding |
| Whole change | Gate runner | `uv run python tools/run_validation_gates.py` | `Pass` |

## Risks
- **Risk**: The checker grows past the 24576 byte gate (headroom 1863 bytes) → **Mitigation**: Phases 5 to 7 re-run `check_module_size.py` after each change; when it fails, split the body rules into a new `tools/` module with `module_nodes.py` and record it with `tools/amend_plan.py` as fallout; keep `ADR_INDEX`, `_matrix_rows`, `_read_lines`, `_split_row` and `_EXCEPTION_RE` in the checker, since `generate_reference_table.py` and `.github/run_cited_adr_tests.py` read them.
- **Risk**: The reverse rule rejects legitimate Index evidence on a row shared by several invariants → **Mitigation**: the rule fires only when the invariant has no body row or no body test file (D2, A3), and a containment fixture locks the accepted case; the live run must exit 0 before the phase ends.
- **Risk**: Moving ADR-004 citations into the body changes meaning or drops a status → **Mitigation**: take citations from the Index rows verbatim; run `check_adr_preservation.py` (it reports a changed invariant, reference or test citation as ERROR) and `check_adr_structure.py`.
- **Risk**: Phase 2 and Phase 4 edits shift line numbers that the pending adrchk015 procedures pin → **Mitigation**: A1; those procedures revalidate their targets before editing, and Phase 2 edits below the Decision and Summary text they target.
- **Risk**: A gated phase is executed before its decision → **Mitigation**: the Execution Status rows carry the gate in Notes and `tools/plan_dependency_order.py` reports the Plan; no approval text or ledger entry is written without the owner's statement (Issue Constraints).
- **Risk**: The exception grammar change breaks `.github/run_cited_adr_tests.py`, which loads the checker module by path → **Mitigation**: Phase 9 starts from the consumer scan (D6) and runs `tests/tools/test_run_cited_adr_tests.py` and `tests/tools/test_generate_reference_table.py`.
- **Risk**: Converting ADR-015 and ADR-016 Verification to tables is read as a decision change → **Mitigation**: keep `Verifies`, `Type` and `Blocking` values and the Coverage note unchanged; `check_adr_preservation.py` confirms.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Evidence columns for ADR-004 and ADR-017 | In Progress | — | — |  |
| 2 | Tables for ADR-015 and ADR-016 | In Progress | — | — |  |
| 3 | Body rows that the Index already cites | In Progress | — | — |  |
| 4 | Index matrix mirrors the bodies | In Progress | — | — |  |
| 5 | Missing evidence column is an error | In Progress | — | — |  |
| 6 | Index-only evidence is an error | In Progress | — | — |  |
| 7 | Cadence error and docstring | In Progress | — | — |  |
| 8 | Documentation sync | In Progress | — | — |  |
| 9 | Exception grammar | In Progress | — | — | Gated: UNK-01 |
| 10 | Ledger entries for the pending amendments | In Progress | — | — | Gated: UNK-02 |
| 11 | Pending Blocking amendments | In Progress | — | — | Gated: UNK-02 |
| 12 | Not verified plus Blocking rule | In Progress | — | — | Gated: UNK-02 |
| 13 | Validation and hand-off | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261120-111659_01_tools_check_adr_invariant_matrix.py.md | 5, 6, 7, 9, 12 | Procedure | Pending | — | — |
| implementations/20261120-111659_03_docs_10_adr_adr_01_index.md.md | 4, 7, 9, 11 | Procedure | Pending | — | — |
| implementations/20261120-111659_04_docs_10_adr_adr_02_01_004_platform-environment-failure-handling-policy.md.md | 1 | Procedure | Pending | — | — |
| implementations/20261120-111659_05_docs_10_adr_adr_02_03_017_mcp-authentication.md.md | 1 | Procedure | Pending | — | — |
| implementations/20261120-111659_06_docs_10_adr_adr_02_07_016_adr-authority-model.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261120-111659_07_docs_10_adr_adr_02_07_015_docs-reference-document-class-disposition.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261120-111659_08_docs_10_adr_adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261120-111659_09_docs_10_adr_adr_02_03_012_mcp-git-server-side-write-enforcement.md.md | 3, 11 | Procedure | Pending | — | — |
| implementations/20261120-111659_10_docs_10_adr_adr_02_02_003_agent-runtime-tool-registry-routing-authority.md.md | 3, 11 | Procedure | Pending | — | — |
| implementations/20261120-111659_11_docs_10_adr_adr_02_01_002_platform-config-isolation.md.md | 11 | Procedure | Pending | — | — |
| implementations/20261120-111659_12_docs_00_governance_governance_03_issue-and-uncertainty-management.md.md | 10 | Procedure | Pending | — | — |
| implementations/20261120-111659_13_tools_TOOL_DESCRIPTIONS.md.md | 8 | Procedure | Pending | — | — |
| implementations/20261120-111659_14_docs_00_governance_governance_04_documentation-checks.md.md | 8 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261117-123013_adrchk013_invariant-matrix-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261120-095739
- **Related target files**: `tools/check_adr_invariant_matrix.py`; `tests/tools/test_check_adr_invariant_matrix.py`; `docs/10_adr/adr_01_index.md`; `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`; `docs/10_adr/adr_02_03_017_mcp-authentication.md`; `docs/10_adr/adr_02_07_016_adr-authority-model.md`; `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md`; `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`; `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`; `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`; `docs/10_adr/adr_02_01_002_platform-config-isolation.md`; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`; `tools/TOOL_DESCRIPTIONS.md`; `docs/00_governance/governance_04_documentation-checks.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Reason for Change; ADR-004 header `Status` (checked in Step 2) | `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | 1 | AC-1 | `tools/check_adr_invariant_matrix.py` live run | Confirmed by repository evidence |
| REQ-001 | Required Changes; ADR-017 header (checked in Step 2) | `docs/10_adr/adr_02_03_017_mcp-authentication.md` | 1 | AC-1 | `tools/check_adr_invariant_matrix.py` live run | Derived from confirmed evidence |
| REQ-002 | ADR-016 bullet Verification (checked in Step 2) | `docs/10_adr/adr_02_07_016_adr-authority-model.md` | 2 | AC-1, AC-3 | `tools/check_adr_invariant_matrix.py` live run | Derived from confirmed evidence |
| REQ-002 | Index ADR-015 INV-01 has no body table (checked in Step 2) | `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md` | 2 | AC-3 | `tools/check_adr_invariant_matrix.py` live run | Derived from confirmed evidence |
| REQ-003 | Reason for Change; Index lacks ADR-016 and ADR-017 rows | `docs/10_adr/adr_01_index.md` | 4 | AC-1 | `tools/check_adr_invariant_matrix.py`, `tools/check_adr_reference.py` | Confirmed by repository evidence |
| REQ-003 | Reason for Change; ADR-004 INV-14 cited only in the Index | `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | 1 | AC-3 | `tools/check_adr_invariant_matrix.py` live run | Confirmed by repository evidence |
| REQ-003 | ADR-017 has no Index row | `docs/10_adr/adr_02_03_017_mcp-authentication.md` | 1 | AC-1 | `tools/check_adr_invariant_matrix.py` live run | Confirmed by repository evidence |
| REQ-003 | ADR-016 has no Index row | `docs/10_adr/adr_02_07_016_adr-authority-model.md` | 2 | AC-1 | `tools/check_adr_invariant_matrix.py` live run | Confirmed by repository evidence |
| REQ-003 | ADR-007 INV-06 cited only in the Index (checked in Step 2) | `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | 3 | AC-3 | `tools/check_adr_invariant_matrix.py` live run | Confirmed by repository evidence |
| REQ-003 | Reason for Change; ADR-012 INV-04 has no body row | `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | 3 | AC-3 | `tools/check_adr_invariant_matrix.py` live run | Confirmed by repository evidence |
| REQ-003 | Reason for Change; ADR-003 INV-03 `Confirmed` versus body `Not verified` | `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | 3 | AC-1 | `tools/check_adr_invariant_matrix.py` live run | Confirmed by repository evidence |
| REQ-004 | Reason for Change; `_body_automated_tests_rows` (checked in Step 2) | `tools/check_adr_invariant_matrix.py` | 5 | AC-2 | `tests/tools/test_check_adr_invariant_matrix.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes; skip locked by an existing test | `tests/tools/test_check_adr_invariant_matrix.py` | 5 | AC-2 | the new fixtures | Confirmed by repository evidence |
| REQ-005 | Reason for Change; `check_body_index_agreement` skips empty `body_files` | `tools/check_adr_invariant_matrix.py` | 6 | AC-3 | `tests/tools/test_check_adr_invariant_matrix.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes; Index-only fixture | `tests/tools/test_check_adr_invariant_matrix.py` | 6 | AC-3 | the new fixtures | Explicit in issue |
| REQ-006 | Reason for Change; `_CADENCE_RULE_SEVERITY` | `tools/check_adr_invariant_matrix.py` | 7 | AC-4 | `tests/tools/test_check_adr_invariant_matrix.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes; `TestManualPartialCadence` expects warnings | `tests/tools/test_check_adr_invariant_matrix.py` | 7 | AC-4 | `TestManualPartialCadence` | Confirmed by repository evidence |
| REQ-006 | Index vocabulary "migration window" | `docs/10_adr/adr_01_index.md` | 7 | AC-4 | `rg -n "migration window"` | Confirmed by repository evidence |
| REQ-007 | Docstring cites GV-012 Follow-up Work; `governance_04` records none (checked in Step 2) | `tools/check_adr_invariant_matrix.py` | 7 | AC-4 | `rg -n "GV-012 Follow-up"` | Confirmed by repository evidence |
| REQ-008 | Reason for Change; grammar differs from `governance_03`, applicability open (UNK-01) | `tools/check_adr_invariant_matrix.py` | 9 | AC-4 | `tests/tools/test_check_adr_invariant_matrix.py` | Needs confirmation |
| REQ-008 | Required Changes; `test_exception_marker_suppresses_skip_error` and `test_malformed_exception_reference_is_reported` lock the current grammar (checked in Step 3) | `tests/tools/test_check_adr_invariant_matrix.py` | 9 | AC-4 | the grammar fixtures | Needs confirmation |
| REQ-008 | Index vocabulary "Approved exceptions" | `docs/10_adr/adr_01_index.md` | 9 | AC-4 | `tools/check_adr_invariant_matrix.py` live run | Needs confirmation |
| REQ-009 | Reason for Change; ADR-012 INV-04 Not verified pending UNK-03 | `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | 11 | AC-5 | `tools/check_adr_structure.py` | Derived from confirmed evidence |
| REQ-009 | Reason for Change; rows 254, 256, 259 | `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | 11 | AC-5 | `tools/check_adr_structure.py` | Confirmed by repository evidence |
| REQ-009 | Reason for Change; rows 232, 233 | `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | 11 | AC-5 | `tools/check_adr_structure.py` | Confirmed by repository evidence |
| REQ-009 | `governance_01` pending form needs a ledger entry (checked in Step 3) | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | 10 | AC-5 | `tools/check_adr_structure.py` | Needs confirmation |
| REQ-009 | Acceptance Criteria; no Not verified plus Blocking row | `tools/check_adr_invariant_matrix.py` | 12 | AC-5 | `tests/tools/test_check_adr_invariant_matrix.py` | Derived from confirmed evidence |
| REQ-009 | Acceptance Criteria; fixture for the rule | `tests/tools/test_check_adr_invariant_matrix.py` | 12 | AC-5 | the new fixtures | Derived from confirmed evidence |
| REQ-010 | Documentation Impact; AGENTS.md Global Rule 9 | `tools/TOOL_DESCRIPTIONS.md` | 8 | AC-6 | `tools/check_tool_descriptions_sync.py` | Derived from confirmed evidence |
| REQ-010 | Documentation Impact; section 12 states two body rules | `docs/00_governance/governance_04_documentation-checks.md` | 8 | AC-6 | `tools/check_docs_consistency.py` | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261120-111659 -->