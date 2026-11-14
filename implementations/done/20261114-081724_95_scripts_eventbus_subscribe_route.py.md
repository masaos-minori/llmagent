## Goal

Remove the 13 remaining historical comment and docstring reference(s) in `scripts/eventbus/subscribe_route.py` (REQ-003 / AC-3).

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
`scripts/eventbus/subscribe_route.py`
### Procedure
Re-run the pattern searches for this file, then remove or rewrite every match listed in Details.
### Method
Comment and docstring edits only; no code change.
### Details
Current matches (live sweep 2026-11-14):
- Line 82: "# REQ-003: Read Last-Event-ID header as additional resume-position input" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 91: "# REQ-003: Stale reconnect rejection" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 106: "# REQ-004: Implement precedence: since_seq > resume position > Last-Event-ID." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 120: "# REQ-003: Fallback to Last-Event-ID only if both since_seq and consumer" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 174: "# REQ-002: Emit id: field alongside data: field" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 189: "# REQ-001: Heartbeat tracking for idle connection keepalive" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 193: "# REQ-001: Timeout-based disconnect detection as fallback" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 215: "# REQ-004: Evaluate heartbeat deadline in timeout branch" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 220: "# REQ-005: Emit heartbeat if deadline reached (independent of event arrival)" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 225: "# REQ-006: Heartbeat activity resets idle timeout" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 242: "# REQ-002: Emit id: field alongside data: field" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 244: "# REQ-001: Update last event time after successful delivery" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 246: "# REQ-001: Periodic heartbeat during active delivery" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Keep each module docstring's first line (the path header verified by `check_docstrings.py`) and all ADR markers unchanged.

## Compatibility considerations
- No runtime, configuration, or schema surface change; deployed copies are refreshed by deploy.sh.

## Security considerations
- N/A: comments only.

## Rollback considerations
- Revert the comment and docstring edits; there is no code change to roll back.

## Validation plan
- `rg -n "Extracted from|Refactored:|RAGCORPUS001|EBAUTHGEN001|crawl003|REQ-[0-9]+" scripts/eventbus/subscribe_route.py` returns nothing.
- `uv run pytest tests/eventbus` continues to pass.
- Comment-only guarantee: `git diff -U0` shows no changed line other than comment and docstring lines.

## Completion criteria
- The file-level acceptance search is clean and the phase test directory passes.

## Out of Scope
- The other rows of the Plan table are handled by their own procedures; test files citing these identifiers are out of scope (UNK-01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261114-185249 | 20261114-185516 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261114-185517 | 20261114-185517 | N/A: no test change needed; targeted run pass (testmon selected 0 for this file, module-path scope used; tests/eventbus 525) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261114-185516 | 20261114-185517 | 3e: ruff/mypy/bandit(0 High/Med; pre-existing nosec B608 warnings only)/gates Pass, lint-imports skipped (no import change); full suite skipped per memo3 directive |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261114-185519 | 20261114-185519 | N/A: no docs/00_index.md task-scope mapping for scripts/eventbus/subscribe_route.py |

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
- **Related target files**: `scripts/eventbus/subscribe_route.py`