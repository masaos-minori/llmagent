## Goal

Remove the 14 remaining historical comment and docstring reference(s) in `scripts/agent/workflow/state_store.py` (REQ-001 / AC-1).

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
`scripts/agent/workflow/state_store.py`
### Procedure
Re-run the pattern searches for this file, then remove or rewrite every match listed in Details.
### Method
Comment and docstring edits only; no code change.
### Details
Current matches (live sweep 2026-11-14):
- Line 36: "# REQ-003; the 30-day value is the plan UNK-01 choice, not the dedup default)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 231: "lease-less legacy age rule was removed (adrrev005 REQ-004): the sole" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 235: "is never recovered, including by another process (REQ-006 / AC-4). This" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 241: "(REQ-007): ``rowcount == 0`` means another recoverer won the race and" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 245: "permanently skipped (REQ-001). After the loop, every claimed task with" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 249: "(REQ-002). The classification and reconciliation counts land in" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 284: "# same transaction as the attempt failover (REQ-001)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 298: "# Parent-task reconciliation (wfaudit007 REQ-001): a claimed task" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 302: "# attempt are skipped outright (REQ-002)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 339: "Startup-only retention purge (REQ-003): tasks whose status is terminal" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 372: "removed (adrrev005 REQ-004) and the sole attempts writer always stamps a" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 374: "host-local time anywhere (REQ-002 / AC-2). Unparseable ``started_at`` or" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 377: "skipped (REQ-003 / AC-3)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 421: "# adrrev005 REQ-004: no lease means no expiry evidence; the row" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Keep each module docstring's first line (the path header verified by `check_docstrings.py`) and all ADR markers unchanged.

## Compatibility considerations
- No runtime, configuration, or schema surface change; deployed copies are refreshed by deploy.sh.

## Security considerations
- N/A: comments only.

## Rollback considerations
- Revert the comment and docstring edits; there is no code change to roll back.

## Validation plan
- `rg -n "Extracted from|Refactored:|RAGCORPUS001|EBAUTHGEN001|crawl003|REQ-[0-9]+" scripts/agent/workflow/state_store.py` returns nothing.
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Related target files**: `scripts/agent/workflow/state_store.py`
