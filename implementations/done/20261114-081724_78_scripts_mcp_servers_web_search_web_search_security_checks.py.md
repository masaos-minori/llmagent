## Goal

Remove the 2 remaining historical comment and docstring reference(s) in `scripts/mcp_servers/web_search/web_search_security_checks.py` (REQ-002 / AC-2).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Comment-only change: no code, import, or behavior edit; the rewrite keeps the information and changes only tense and identifiers (Plan Assumptions).

## Design decisions
- N/A: comment-only change (Plan Design rewrite rules).

## Alternatives considered
- Keeping the provenance notes: rejected; AC-2 requires the whole tree free of these identifiers.

## Implementation
### Target file
`scripts/mcp_servers/web_search/web_search_security_checks.py`
### Procedure
Re-run the pattern searches for this file, then remove or rewrite every match listed in Details.
### Method
Comment and docstring edits only; no code change.
### Details
Current matches (live sweep 2026-11-14):
- Line 4: "Self-validation layer for the Web Search MCP server (REQ-015). This module owns every" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 12: "Extracted from web_search_models.py, whose declared scope is config loading, Pydantic" -- provenance note: delete this sentence (and its continuation lines) and keep the remaining text in current tense.
- Keep each module docstring's first line (the path header verified by `check_docstrings.py`) and all ADR markers unchanged.

## Compatibility considerations
- No runtime, configuration, or schema surface change; deployed copies are refreshed by deploy.sh.

## Security considerations
- N/A: comments only.

## Rollback considerations
- Revert the comment and docstring edits; there is no code change to roll back.

## Validation plan
- `rg -n "Extracted from|Refactored:|RAGCORPUS001|EBAUTHGEN001|crawl003|REQ-[0-9]+" scripts/mcp_servers/web_search/web_search_security_checks.py` returns nothing.
- `uv run pytest tests/mcp_servers` continues to pass.
- Comment-only guarantee: `git diff -U0` shows no changed line other than comment and docstring lines.

## Completion criteria
- The file-level acceptance search is clean and the phase test directory passes.

## Out of Scope
- The other rows of the Plan table are handled by their own procedures; test files citing these identifiers are out of scope (UNK-01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261114-174319 | 20261114-174612 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261114-174613 | 20261114-174613 | N/A: no test change needed; targeted run pass (testmon 8, tests/mcp_servers 2615) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261114-174612 | 20261114-174613 | 3e: ruff/mypy/bandit(0 High/Med)/gates Pass, lint-imports skipped (no import change); full suite skipped per memo3 directive |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261114-174615 | 20261114-174615 | N/A: no docs/00_index.md task-scope mapping for scripts/mcp_servers/web_search/web_search_security_checks.py |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/done/20261110-171040_rmcompat007_history-comment-sweep.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-122030_rmcompat007_history-comment-sweep.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261114-081724
- **Related target files**: `scripts/mcp_servers/web_search/web_search_security_checks.py`