## Goal

Remove the 9 remaining historical comment and docstring reference(s) in `scripts/agent/workflow/workflow_engine.py` (REQ-001 / AC-1).

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
`scripts/agent/workflow/workflow_engine.py`
### Procedure
Re-run the pattern searches for this file, then remove or rewrite every match listed in Details.
### Method
Comment and docstring edits only; no code change.
### Details
Current matches (live sweep 2026-11-14):
- Line 28: "# REQ-005, Plan UNK-03: named constant, not configuration). A normal stage" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 36: "# never imports the dispatcher's dedup config (REQ-004). orchestrator.py supplies" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 101: "to attempts.error_kind (REQ-007 / AC-7)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 143: "(REQ-004): sourced from AgentConfig, never from the dispatcher's" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 166: "Turn-entry detection (toolexec001 REQ-008): stale pending rows are first" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 175: "behavior (REQ-010). Fresh pending rows (within the timeout window) are not" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 262: "# Halts raised by the stage callback itself are terminal (REQ-006 / AC-6)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 273: "# run() writes the task status (REQ-003 / AC-3)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 360: "# deadline: kind exception, propagated unchanged (REQ-002 / AC-2)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Keep each module docstring's first line (the path header verified by `check_docstrings.py`) and all ADR markers unchanged.

## Compatibility considerations
- No runtime, configuration, or schema surface change; deployed copies are refreshed by deploy.sh.

## Security considerations
- N/A: comments only.

## Rollback considerations
- Revert the comment and docstring edits; there is no code change to roll back.

## Validation plan
- `rg -n "Extracted from|Refactored:|RAGCORPUS001|EBAUTHGEN001|crawl003|REQ-[0-9]+" scripts/agent/workflow/workflow_engine.py` returns nothing.
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261114-160831 | 20261114-160943 | changed: scripts/agent/workflow/workflow_engine.py |
| 2 | Add or update tests per Validation plan | Completed | 20261114-161113 | 20261114-161113 | N/A: no test change needed; targeted runs pass (testmon 21, tests/agent 4257) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261114-160943 | 20261114-161113 | 3e: ruff/mypy/bandit(0 High/Med)/gates Pass, lint-imports skipped (no import change); full suite skipped per memo3 directive |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261114-161113 | 20261114-161113 | N/A: no docs/00_index.md task-scope mapping for scripts/agent/workflow/workflow_engine.py |

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
- **Related target files**: `scripts/agent/workflow/workflow_engine.py`