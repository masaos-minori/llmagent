## Goal
Add an ERROR to `tools/check_known_deviation_sync.py` for a `## Known Deviations` bullet that cites no Known Issue ID, and pin the existing behaviors with tests (`REQ-004`, `REQ-006` / `AC-4`, `AC-6`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Size (checked): 21410 bytes, 3166 bytes under the 24576 gate, not in the tools baseline; the new check must stay under the gate.
- Existing helpers: `_section_body(lines, heading, level)`, `_LABELED_BULLET_RE` (`- **Known Issue**: ...`), `_ID_LOOKAHEAD_RE`, `_RESOLVED_BULLET_RE`, `find_resolved_bullets`; `collect_issues()` aggregates them.
- Corpus: after `adrrev009`, ADR-008 cites `SHARED-001` and `SHARED-002`; other ADRs read `Not applicable`; a labeled bullet without an ID is the only new failure (verify with a smoke run).
- The exempt text is the `Not applicable` marker only.

## Design decisions
- Add `find_bullets_without_id(files)` beside `find_resolved_bullets` and call it from `collect_issues()`; reuse the existing regexes.
- Message tells the author the fix: cite a ledger ID or remove the bullet.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`tools/check_known_deviation_sync.py`

### Procedure
1. Write the failing tests first (companion).
2. Add `find_bullets_without_id` (new) and call it from `collect_issues()`.
3. Update the module docstring's failure-mode list.
4. Smoke-run the tool against real `docs/`.

### Method
- For each doc, for each line of `_section_body(doc.lines, "## Known Deviations", 2)`: if it is a top-level bullet (`^\s*-\s`) that is not `Not applicable` and has no ID matched by `_ID_LOOKAHEAD_RE.search` after the label, add `Issue(file=f"adr/{doc.rel_path}", line_no=n, severity="ERROR", message=...)`.
- Keep existing behavior: a dangling ID stays a WARNING, an uncited target ADR stays a WARNING, a resolved bullet stays an ERROR; exit 1 only on ERROR.

### Details
- Do not treat continuation lines or sub-bullets as bullets; test an indented continuation.
- Module docstring numbering stays consistent (a fifth failure mode).

### Companion test files
- `tests/tools/test_check_known_deviation_sync.py`
  - Procedure: Add tests: a bullet without an ID gives an ERROR (exit 1); `Not applicable` gives none; pin the existing dangling-ID WARNING, uncited-target WARNING, and resolved-bullet ERROR behaviors; written before the change.
  - Validation: `uv run pytest tests/tools/test_check_known_deviation_sync.py -q`; show the new ERROR test failing before the change.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_known_deviation_sync.py -q`.
- `uv run ruff format <file>`, `uv run ruff check <file>`, `uv run mypy <file>`, `uv run bandit <file>` — clean.
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` — pass.
- `uv run python tools/check_known_deviation_sync.py` on real `docs/` — pass.

## Completion criteria
- A Known Deviations bullet without a ledger ID fails with exit 1; `Not applicable` does not; the existing behaviors are pinned; the tool stays under the size gate.

## Out of Scope
- Changing the ledger format; editing ADR Known Deviations sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the failing test first and confirm it fails against the unmodified tool | Pending | — | — | |
| 2 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the tests, then the validation sequence (`rules/toolchain.md`) for the changed tool | Pending | — | — | |
| 4 | Smoke-run the tool against the real `docs/` corpus and record the result | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` / `REQ-006` — ERROR for a Known Deviations bullet without a ledger ID
- **Source issue**: issues/20261109-113351_adrrev018_docs-checker-harden.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-111505_adrrev018_docs-checker-harden.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-124203
- **Related target files**: `tools/check_known_deviation_sync.py`, `tests/tools/test_check_known_deviation_sync.py`
