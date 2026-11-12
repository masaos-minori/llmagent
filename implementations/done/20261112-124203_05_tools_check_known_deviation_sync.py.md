## Goal
Add an ERROR to `tools/check_known_deviation_sync.py` for a `## Known Deviations` bullet that cites no Known Issue ID, and pin the existing behaviors with tests (`REQ-004`, `REQ-006` / `AC-4`, `AC-6`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Size (checked): 21410 bytes, 3166 bytes under the 24576 gate, not in the tools baseline; the new check must stay under the gate.
- Existing helpers: `_section_body(lines, heading, level)`, `_LABELED_BULLET_RE` (`- **Known Issue**: ...`), `_ID_LOOKAHEAD_RE`, `_RESOLVED_BULLET_RE`, `find_resolved_bullets`; `collect_issues()` aggregates them.
- Corpus (verified 2026-11-12): every ADR `## Known Deviations` section reads `Not applicable` except `adr_02_05_008_db-sqlite-4db-separation.md`, whose two bullets read `- **Known Issue:** SHARED-001 ...` and `- **Known Issue:** SHARED-002 ...` — the colon is inside the bold, so `_LABELED_BULLET_RE` (`- **Known Issue**: ...`) does not match them. `check_known_deviation_sync.py` reports `No issues found` today (the SHARED-001/002 ledger entries have no `Target` field, so the reverse check does not flag them either).
- Finding to report, not fixed by this row: because of that label form, ADR-008's citations are invisible to `parse_adr_references`, `cross_check`, and `reverse_cross_check`. The new check must therefore detect the ID in the bullet text itself, not through `_LABELED_BULLET_RE`.
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
- For each doc, for each line of `_section_body(doc.lines, "## Known Deviations", 2)`: if it is a top-level bullet (`^\s*-\s`) that is not the `Not applicable` marker and `_ID_LOOKAHEAD_RE.search` finds no ID token anywhere in the line, add `Issue(file=f"adr/{doc.rel_path}", line_no=n, severity="ERROR", message=...)`. Use `search` on the whole line, not `_LABELED_BULLET_RE` and not the anchored `match` used by `parse_adr_references`: the corpus uses both `- **Known Issue**: <ID>` and `- **Known Issue:** <ID>` label forms (see Assumptions).
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
| 1 | Write the failing test first and confirm it fails against the unmodified tool | Completed | 20261112-212054 | 20261112-213725 | 4 new TestBulletWithoutId tests added first; collection failed with ImportError (find_bullets_without_id missing) against the unmodified tool |
| 2 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112-213725 | 20261112-213725 | find_bullets_without_id added, called from collect_issues after find_resolved_bullets; docstring failure-mode list now five modes (intro count fixed Two -> Five) |
| 3 | Run the tests, then the validation sequence (`rules/toolchain.md`) for the changed tool | Completed | 20261112-213725 | 20261112-213725 | 20 targeted tests pass; full suite 12154 pass; ruff/mypy/bandit(-ll) clean; size 23492B under the 24576 gate |
| 4 | Smoke-run the tool against the real `docs/` corpus and record the result | Completed | 20261112-213725 | 20261112-213725 | check_known_deviation_sync.py: No issues found (exit 0); corpus ADR-008 colon-inside-label bullets pass via whole-line search |

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