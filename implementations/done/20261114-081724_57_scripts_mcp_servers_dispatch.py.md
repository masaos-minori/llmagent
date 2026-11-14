## Goal

Remove the 18 remaining historical comment and docstring reference(s) in `scripts/mcp_servers/dispatch.py` (REQ-002 / AC-2).

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
`scripts/mcp_servers/dispatch.py`
### Procedure
Re-run the pattern searches for this file, then remove or rewrite every match listed in Details.
### Method
Comment and docstring edits only; no code change.
### Details
Current matches (live sweep 2026-11-14):
- Line 70: "``dedup_state`` carries the durable-dedup branch taken (REQ-005): ``""`` (no dedup" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 86: "# --- Idempotency cache (REQ-001..REQ-004) ---------------------------------" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 148: """"Store a successful result with TTL bookkeeping and eviction (REQ-003)."""" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 163: "# --- Durable dedup store (REQ-003) -------------------------------------------" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 167: "# overlay (the pre-REQ-003 shape). Tests replace the three globals below." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 198: """"Run the retention sweep at most once per process (REQ-009)."""" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 242: "same contract holds across processes (REQ-003): completed results with a" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 262: "# duplicate-check for side-effecting tools (REQ-001: a non-empty key is" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 264: "# executes). The durable store is the truth (REQ-003); the overlay is a" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 286: "# Expired: drop it; the store lookup below decides (REQ-003)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 289: "# REQ-002: same key reused with different content -> reject." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 306: "# REQ-001/REQ-002: a store that was lost or recreated cannot prove a" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 349: "# REQ-002/REQ-010: durable rows honor the same reuse rejection." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 388: "# fresh audited attempt under the same key (REQ-005)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 427: "# REQ-002: a failed pre-execution write leaves no proof the call" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 454: "# lookup-failure asymmetry (REQ-001/REQ-002/REQ-003)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 475: "# Cache only real, successful, non-dry-run results (REQ-004)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 492: "# REQ-004: error results are never cached, but the durable row must not" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Keep each module docstring's first line (the path header verified by `check_docstrings.py`) and all ADR markers unchanged.

## Compatibility considerations
- No runtime, configuration, or schema surface change; deployed copies are refreshed by deploy.sh.

## Security considerations
- N/A: comments only.

## Rollback considerations
- Revert the comment and docstring edits; there is no code change to roll back.

## Validation plan
- `rg -n "Extracted from|Refactored:|RAGCORPUS001|EBAUTHGEN001|crawl003|REQ-[0-9]+" scripts/mcp_servers/dispatch.py` returns nothing.
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261114-161954 | 20261114-162127 | changed: scripts/mcp_servers/dispatch.py |
| 2 | Add or update tests per Validation plan | Completed | 20261114-162401 | 20261114-162401 | N/A: no test change needed; targeted runs pass (testmon 43, tests/mcp_servers 2611) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261114-162127 | 20261114-162401 | 3e: ruff/mypy/bandit(0 High/Med)/gates Pass, lint-imports skipped (no import change); full suite skipped per memo3 directive |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261114-162401 | 20261114-162401 | N/A: no docs/00_index.md task-scope mapping for scripts/mcp_servers/dispatch.py |

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
- **Related target files**: `scripts/mcp_servers/dispatch.py`