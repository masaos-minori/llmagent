## Goal

Remove the 5 remaining historical comment and docstring reference(s) in `scripts/agent/context.py` (REQ-001 / AC-1).

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
`scripts/agent/context.py`
### Procedure
Re-run the pattern searches for this file, then remove or rewrite every match listed in Details.
### Method
Comment and docstring edits only; no code change.
### Details
Current matches (live sweep 2026-11-14):
- Line 205: "(REQ-004, AC-004). Untrusted DB restores keep using ``replace_history``." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 254: "# turn is persisted all-or-nothing (REQ-001, AC-001). None between turns." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 256: "# Per-attempt side-effect flag (wfretry001 REQ-006): set by tool_runner before a" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 340: "# REQ-001: enforce invariant — all required services must be non-None" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 386: "# REQ-001: unconditional restriction, matching every other process entry point" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Keep each module docstring's first line (the path header verified by `check_docstrings.py`) and all ADR markers unchanged.

## Compatibility considerations
- No runtime, configuration, or schema surface change; deployed copies are refreshed by deploy.sh.

## Security considerations
- N/A: comments only.

## Rollback considerations
- Revert the comment and docstring edits; there is no code change to roll back.

## Validation plan
- `rg -n "Extracted from|Refactored:|RAGCORPUS001|EBAUTHGEN001|crawl003|REQ-[0-9]+" scripts/agent/context.py` returns nothing.
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261114-101049 | 20261114-101114 | changed: scripts/agent/context.py |
| 2 | Add or update tests per Validation plan | Completed | 20261114-101300 | 20261114-101300 | N/A: no test change needed; targeted runs pass (testmon 5, tests/agent 4257) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261114-101300 | 20261114-102246 | 3e: ruff/mypy/bandit/gates Pass, lint-imports skipped (no import change); full suite serial-coverage 12166 passed, diff-cover N/A-comment lines only |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261114-101300 | 20261114-101300 | N/A: no docs/00_index.md task-scope mapping for scripts/agent/context.py |

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
- **Related target files**: `scripts/agent/context.py`