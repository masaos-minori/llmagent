## Goal

Remove the 7 remaining historical comment and docstring reference(s) in `scripts/eventbus/app.py` (REQ-003 / AC-3).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Comment-only change: no code, import, or behavior edit; the rewrite keeps the information and changes only tense and identifiers (Plan Assumptions).

## Design decisions
- N/A: comment-only change (Plan Design rewrite rules).

## Alternatives considered
- Keeping the provenance notes: rejected; AC-3 requires the whole tree free of these identifiers.

## Implementation
### Target file
`scripts/eventbus/app.py`
### Procedure
Re-run the pattern searches for this file, then remove or rewrite every match listed in Details.
### Method
Comment and docstring edits only; no code change.
### Details
Current matches (live sweep 2026-11-14):
- Line 20: "attach_auth_middleware,  # noqa: PLC0415 — new module, REQ-002" -- suppression comment: keep the pragma and its error code, and keep the justification text; strip only the plan/requirement identifier reference.
- Line 21: "build_and_publish_generation,  # noqa: PLC0415 — new module, REQ-004" -- suppression comment: keep the pragma and its error code, and keep the justification text; strip only the plan/requirement identifier reference.
- Line 76: "# Restart-baseline audit record (REQ-006): documents the baseline generation" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 119: "so they exercise one lifecycle sequence (REQ-005). Never closes a connection" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 120: "another worker may still own (REQ-001); the close-on-timeout fallback is gone." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 124: "#    this point on (REQ-004, seq 03)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 198: "# Repair lost artifacts and report outbox inconsistencies (REQ-007)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Keep each module docstring's first line (the path header verified by `check_docstrings.py`) and all ADR markers unchanged.

## Compatibility considerations
- No runtime, configuration, or schema surface change; deployed copies are refreshed by deploy.sh.

## Security considerations
- N/A: comments only.

## Rollback considerations
- Revert the comment and docstring edits; there is no code change to roll back.

## Validation plan
- `rg -n "Extracted from|Refactored:|RAGCORPUS001|EBAUTHGEN001|crawl003|REQ-[0-9]+" scripts/eventbus/app.py` returns nothing.
- `uv run pytest tests/eventbus` continues to pass.
- Comment-only guarantee: `git diff -U0` shows no changed line other than comment and docstring lines.
- `uv run python tools/check_suppression_justification.py` reports no finding for this file.

## Completion criteria
- The file-level acceptance search is clean and the phase test directory passes.

## Out of Scope
- The other rows of the Plan table are handled by their own procedures; test files citing these identifiers are out of scope (UNK-01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261114-175716 | 20261114-175928 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261114-175930 | 20261114-175930 | N/A: no test change needed; targeted run pass (testmon 7, tests/eventbus 525) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261114-175928 | 20261114-175930 | 3e: ruff/mypy/bandit(0 High/Med)/gates Pass, lint-imports skipped (no import change); full suite skipped per memo3 directive |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261114-175931 | 20261114-175931 | N/A: no docs/00_index.md task-scope mapping for scripts/eventbus/app.py |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/done/20261110-171040_rmcompat007_history-comment-sweep.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-122030_rmcompat007_history-comment-sweep.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261114-081724
- **Related target files**: `scripts/eventbus/app.py`