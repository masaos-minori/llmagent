## Goal

Remove the 16 remaining historical comment and docstring reference(s) in `scripts/eventbus/dlq.py` (REQ-003 / AC-3).

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
`scripts/eventbus/dlq.py`
### Procedure
Re-run the pattern searches for this file, then remove or rewrite every match listed in Details.
### Method
Comment and docstring edits only; no code change.
### Details
Current matches (live sweep 2026-11-14):
- Line 66: "None  # REQ-002: per-consumer failure count" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 116: """"Shared promotion logic for the sweep path. DB-only since dlqbox001 (REQ-003)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 118: "REQ-002 and ADR-006 INV-13: promotes events where every consumer with a delivery" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 163: "consumer_failure_count: Per-consumer failure count (REQ-002), logged only." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 204: "REQ-001, REQ-002, REQ-003: lists promoted events (dlq_at IS NOT NULL) whose" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 210: "dlqbox001 (REQ-007) adds three report-only classifications: ``orphans`` —" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 277: """"True when an existing DLQ file differs from the canonical DB state (REQ-007)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 302: """"Count DLQ files with no promoted event row and no done outbox row (REQ-007)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 330: "DB-only since dlqbox001 (REQ-003): the dlq_at stamp and the dlq_outbox request" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 337: "consumer_failure_count: Per-consumer failure count (REQ-002)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 429: "min(base * 2**(attempt-1), cap_seconds) with base/cap from cfg (REQ-005)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 433: "stays pending for the next cycle (REQ-006)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 454: """"Locked completion write: mark the outbox row done and commit (REQ-004)."""" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 467: "REQ-004: called once per dlq_loop cycle; a pending row is simply due again on" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 468: "the next cycle after a crash or restart (REQ-006). REQ-005: a failing artifact" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 498: "# defensive-only. Record a bounded failed attempt and continue (REQ-005)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Keep each module docstring's first line (the path header verified by `check_docstrings.py`) and all ADR markers unchanged.

## Compatibility considerations
- No runtime, configuration, or schema surface change; deployed copies are refreshed by deploy.sh.

## Security considerations
- N/A: comments only.

## Rollback considerations
- Revert the comment and docstring edits; there is no code change to roll back.

## Validation plan
- `rg -n "Extracted from|Refactored:|RAGCORPUS001|EBAUTHGEN001|crawl003|REQ-[0-9]+" scripts/eventbus/dlq.py` returns nothing.
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
- **Requirement ID**: REQ-003
- **Source issue**: issues/done/20261110-171040_rmcompat007_history-comment-sweep.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-122030_rmcompat007_history-comment-sweep.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261114-081724
- **Related target files**: `scripts/eventbus/dlq.py`
