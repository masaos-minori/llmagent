## Goal

Remove the 8 remaining historical comment and docstring reference(s) in `scripts/mcp_servers/git/write_protection_pipeline.py` (REQ-002 / AC-2).

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
`scripts/mcp_servers/git/write_protection_pipeline.py`
### Procedure
Re-run the pattern searches for this file, then remove or rewrite every match listed in Details.
### Method
Comment and docstring edits only; no code change.
### Details
Current matches (live sweep 2026-11-14):
- Line 9: "Extracted from mcp_servers/git/repository_state.py so that module holds the" -- provenance note: delete this sentence (and its continuation lines) and keep the remaining text in current tense.
- Line 28: "# ── Per-repository-path write-serialization lock registry (REQ-005) ───────────" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 31: "# plans/20260904-192131_plan.md REQ-007." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 168: "# Destination-aware (REQ-002/003): pass the operation context so the" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 189: "# Serialize concurrent writes to the same canonical repo path (REQ-005)" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 194: "# only guarantee this pipeline made about that field before REQ-005/006" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 198: "# Git call (REQ-006) — reject if it drifted since authorization." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 213: "# (REQ-006). No separate post-state snapshot is taken — the pipeline" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Keep each module docstring's first line (the path header verified by `check_docstrings.py`) and all ADR markers unchanged.

## Compatibility considerations
- No runtime, configuration, or schema surface change; deployed copies are refreshed by deploy.sh.

## Security considerations
- N/A: comments only.

## Rollback considerations
- Revert the comment and docstring edits; there is no code change to roll back.

## Validation plan
- `rg -n "Extracted from|Refactored:|RAGCORPUS001|EBAUTHGEN001|crawl003|REQ-[0-9]+" scripts/mcp_servers/git/write_protection_pipeline.py` returns nothing.
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
- **Requirement ID**: REQ-002
- **Source issue**: issues/done/20261110-171040_rmcompat007_history-comment-sweep.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-122030_rmcompat007_history-comment-sweep.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261114-081724
- **Related target files**: `scripts/mcp_servers/git/write_protection_pipeline.py`
