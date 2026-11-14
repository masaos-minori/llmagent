## Goal

Remove the 2 remaining historical comment and docstring reference(s) in `scripts/shared/security/shadow_validation.py` (REQ-005 / AC-5).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Comment-only change: no code, import, or behavior edit; the rewrite keeps the information and changes only tense and identifiers (Plan Assumptions).

## Design decisions
- N/A: comment-only change (Plan Design rewrite rules).

## Alternatives considered
- Keeping the provenance notes: rejected; AC-5 requires the whole tree free of these identifiers.

## Implementation
### Target file
`scripts/shared/security/shadow_validation.py`
### Procedure
Re-run the pattern searches for this file, then remove or rewrite every match listed in Details.
### Method
Comment and docstring edits only; no code change.
### Details
Current matches (live sweep 2026-11-14):
- Line 22: """"The six comparison outcomes the Plan fixes for Shadow Validation (REQ-016)."""" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 70: """"Compare one old-audit outcome list with one server posture (REQ-016)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Keep each module docstring's first line (the path header verified by `check_docstrings.py`) and all ADR markers unchanged.

## Compatibility considerations
- No runtime, configuration, or schema surface change; deployed copies are refreshed by deploy.sh.

## Security considerations
- N/A: comments only.

## Rollback considerations
- Revert the comment and docstring edits; there is no code change to roll back.

## Validation plan
- `rg -n "Extracted from|Refactored:|RAGCORPUS001|EBAUTHGEN001|crawl003|REQ-[0-9]+" scripts/shared/security/shadow_validation.py` returns nothing.
- `uv run pytest tests/shared tests/db` continues to pass.
- Comment-only guarantee: `git diff -U0` shows no changed line other than comment and docstring lines.

## Completion criteria
- The file-level acceptance search is clean and the phase test directory passes.

## Out of Scope
- The other rows of the Plan table are handled by their own procedures; test files citing these identifiers are out of scope (UNK-01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261114-200956 | 20261114-200956 | changed: scripts/shared/security/shadow_validation.py |
| 2 | Add or update tests per Validation plan | Completed | 20261114-200956 | 20261114-200956 | N/A: no test change needed; targeted tests pass (tests/shared tests/db: 1649 passed) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261114-200956 | 20261114-200956 | 3e: ruff/mypy/bandit(0 High/Med)/gates Pass; lint-imports skipped (no import change); full suite skipped per memo3 directive |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261114-200956 | 20261114-200956 | N/A: no docs/00_index.md task-scope mapping for scripts/shared/security/shadow_validation.py |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/done/20261110-171040_rmcompat007_history-comment-sweep.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-122030_rmcompat007_history-comment-sweep.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261114-081724
- **Related target files**: `scripts/shared/security/shadow_validation.py`