## Goal
Make the ADR structure checker reject an unknown Status value (REQ-009) and a pending approval bullet that cites no resolving ledger ID (REQ-010), with tests.

## Scope
**Release unit**: N/A: not part of a release unit
- Two new checks, their constants and helpers, the `collect_issues` wiring, and the module docstring.
- Rows 01 to 15 must be done first, otherwise the live run fails by design.

## Assumptions
- The allowed Status set equals the values the policy governance document lists after its procedure: Proposed, Accepted, Withdrawn.
- The ledger ID pattern `AAL-NNN` and the ledger location are the Source plan's proposed defaults (UNK-01); a different maintainer decision changes only the ID-pattern constant and the ledger-path constant.
- Every pending bullet is one physical line (checked in the live ADRs); a wrapped bullet is out of scope.

## Design decisions
- Two pure checks take parsed inputs (docs, ledger IDs); `collect_issues` is the only place that reads the ledger document, so the unit tests need no file system access.
- Status is the first non-empty stripped line after `## Status`, reimplemented locally with the same rule as `_find_status_section` in `tools/check_canonical_source_registry.py` (that name is private to another tool); a test pins the ADR-010 shape (value line followed by a paragraph).

## Alternatives considered
Importing `_find_status_section` from another tool was rejected (private cross-tool dependency). Matching the whole Status body was rejected (ADR-010 keeps an explanatory paragraph).

## Implementation
### Target file
`tools/check_adr_structure.py`
### Procedure
1. Add constants `_ALLOWED_STATUSES` (new), `_LEDGER_ID_RE` (new), `_LEDGER_HEADING_RE` (new), `_PENDING_BULLET_RE` (new), and the ledger path constant `_LEDGER_DOC` (new).
2. Add `_status_value` (new): (line number, value) of the first non-empty line after `## Status`, or None.
3. Add `check_status_values` (new): ERROR for a Status value outside the allowed set and for an empty Status.
4. Add `_ledger_ids_from_lines` (new): the IDs of every `#### AAL-NNN` heading.
5. Add `check_pending_approval_form` (new): within `### Approval Record`, each `Current Decision Approval (pending)` bullet must contain a ledger ID found in the given set; ERROR otherwise.
6. Add `_load_ledger_ids` (new) reading the ledger document, and wire both checks into `collect_issues`.
7. Update the module docstring (two more checks) and the `argparse` description.
### Method
Same shape as `check_section_headings`: skip non-ADR files with `_ADR_FILE_RE`, ignore fenced code via the fence rule of `_top_level_headings`, emit `Issue` records with severity ERROR. Signatures: `check_status_values(docs: list[DocFile]) -> list[Issue]` (new); `check_pending_approval_form(docs: list[DocFile], ledger_ids: frozenset[str]) -> list[Issue]` (new).
### Details
- `### Withdrawal Approval Record` and bullets outside `### Approval Record` are not subject to the pending check.
- Messages name the missing or unknown value and the ledger ID so a failure is actionable.
- Module size stays well under the 24576 B tools gate (about 11 KB now).

### Companion test files
- `tests/tools/test_check_adr_structure.py`
  - Procedure: add cases for an unknown Status, each allowed value, a Status value followed by a paragraph, an empty Status, a pending bullet with a resolving ID, without an ID, with an unresolved ID, a withdrawal record that is not checked, and a parity test that each allowed value appears in the policy document's status definitions.
  - Validation: `uv run pytest tests/tools/test_check_adr_structure.py`.

## Compatibility considerations
New ERROR findings only; the exit-code rule, `--format json` shape, the `adr-structure` hook, and the gate definition are unchanged. The live run must be clean before the commit.

## Security considerations
N/A: reads fixed repository paths only; no user-controlled path, no subprocess, no network.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/tools/test_check_adr_structure.py`
- `uv run ruff format tools/check_adr_structure.py tests/tools/test_check_adr_structure.py`, `uv run ruff check tools/check_adr_structure.py tests/tools/test_check_adr_structure.py`, `uv run mypy tools/check_adr_structure.py tests/tools/test_check_adr_structure.py`, `uv run bandit tools/check_adr_structure.py`
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`
- `uv run python tools/check_adr_structure.py` (live run, no ERROR)

## Completion criteria
- An unknown Status value and a pending bullet without a resolving ID are each rejected by a test (AC-6, AC-7).
- The live run over `docs/10_adr/` reports no ERROR and the lint, type, security, and size checks pass.

## Out of Scope
- Editing ADRs or governance documents.
- Documentation and tool-description updates (rows 18 and 19).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the Status value check and the pending-form check to the checker (REQ-009, REQ-010) | Pending | — | — |  |
| 2 | Add the tests to the companion test file | Pending | — | — |  |
| 3 | Run the validation sequence listed in Validation plan | Pending | — | — |  |
| 4 | Hand the documentation sync to the procedures for the check documentation and the tool descriptions | Pending | — | — |  |

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
- **Requirement ID**: `REQ-009`: Status value check; `REQ-010`: pending-form and ledger-ID check
- **Source issue**: issues/20261117-123011_adrchk011_adr-approval-governance.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-092611_adrchk011_adr-approval-governance.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-093859
- **Related target files**: `tools/check_adr_structure.py`, `tests/tools/test_check_adr_structure.py`
