## Goal

Remove the 17 remaining historical comment and docstring reference(s) in `scripts/agent/turn_persistence.py` (REQ-001 / AC-1).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Comment-only change: no code, import, or behavior edit; the rewrite keeps the information and changes only tense and identifiers (Plan Assumptions).

## Design decisions
- N/A: comment-only change (Plan Design rewrite rules).

## Alternatives considered
- Keeping the provenance notes: rejected; AC-1 requires the whole tree free of these identifiers.

## Implementation
### Target file
`scripts/agent/turn_persistence.py`
### Procedure
Re-run the pattern searches for this file, then remove or rewrite every match listed in Details.
### Method
Comment and docstring edits only; no code change.
### Details
Current matches (live sweep 2026-11-14):
- Line 5: "all-or-nothing (REQ-001). On any persistence failure inside a turn the" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 11: "(REQ-002, REQ-003, REQ-004)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 13: "Write routing (REQ-005) is realized at the repository: each phase-group (e.g. a" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 22: "(REQ-005). Each repository call opens its own short-lived connection, so the" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 48: "(REQ-003). Subclasses the plain ``Exception`` base, matching the" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 103: "The repository call runs on a worker thread (REQ-005); its" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 119: "The repository call runs on a worker thread (REQ-005); its" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 135: "rows (REQ-005, AC-005). The repository call runs on a worker thread" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 136: "(REQ-005); its ``sqlite3.Error`` propagates back to the caller unchanged." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 146: """"Persist a compressed snapshot back to DB (REQ-006)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 150: "turn-start rows instead of only deleting rows above the marker (REQ-001)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 151: "The repository call runs on a worker thread (REQ-005); its" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 172: "turn-start image (REQ-001, REQ-004). A capture failure propagates" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 185: """"Undo the turn's DB changes in one transaction (REQ-001, REQ-004)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 192: "Offloaded to a worker thread like the writes (REQ-005)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 216: ":class:`ConversationPersistenceError` chaining ``exc`` (REQ-002, REQ-003," -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 217: "REQ-004). A compensation-delete failure is logged and does not mask the" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Keep each module docstring's first line (the path header verified by `check_docstrings.py`) and all ADR markers unchanged.

## Compatibility considerations
- No runtime, configuration, or schema surface change; deployed copies are refreshed by deploy.sh.

## Security considerations
- N/A: comments only.

## Rollback considerations
- Revert the comment and docstring edits; there is no code change to roll back.

## Validation plan
- `rg -n "Extracted from|Refactored:|RAGCORPUS001|EBAUTHGEN001|crawl003|REQ-[0-9]+" scripts/agent/turn_persistence.py` returns nothing.
- `uv run pytest tests/agent` continues to pass.
- Comment-only guarantee: `git diff -U0` shows no changed line other than comment and docstring lines.

## Completion criteria
- The file-level acceptance search is clean and the phase test directory passes.

## Out of Scope
- The other rows of the Plan table are handled by their own procedures; test files citing these identifiers are out of scope (UNK-01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261114-131913 | 20261114-132012 | changed: scripts/agent/turn_persistence.py |
| 2 | Add or update tests per Validation plan | Completed | 20261114-132300 | 20261114-132300 | N/A: no test change needed; targeted runs pass (testmon 9, tests/agent 4257) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261114-132300 | 20261114-132148 | 3e: ruff/mypy/bandit(0 High/Med)/gates Pass, lint-imports skipped (no import change); full suite skipped per memo3 directive |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261114-132300 | 20261114-132300 | N/A: no docs/00_index.md task-scope mapping for scripts/agent/turn_persistence.py |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/done/20261110-171040_rmcompat007_history-comment-sweep.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-122030_rmcompat007_history-comment-sweep.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261114-081724
- **Related target files**: `scripts/agent/turn_persistence.py`