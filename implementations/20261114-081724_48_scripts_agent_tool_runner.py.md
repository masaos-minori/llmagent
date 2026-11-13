## Goal

Remove the 17 remaining historical comment and docstring reference(s) in `scripts/agent/tool_runner.py` (REQ-001 / AC-1).

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
`scripts/agent/tool_runner.py`
### Procedure
Re-run the pattern searches for this file, then remove or rewrite every match listed in Details.
### Method
Comment and docstring edits only; no code change.
### Details
Current matches (live sweep 2026-11-14):
- Line 79: "completes and the round stays total (plans/20261023-004538_plan.md, REQ-001/" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 80: "REQ-007). Only *this* call's Exception is converted; BaseException (e.g." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 81: "asyncio.CancelledError) keeps propagating (REQ-002/AC-5), so a cancelled" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 85: "(plans/20261101-105136_toolstate001 plan.md, REQ-001..REQ-004): pending is" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 93: "except Exception as exc:  # noqa: BLE001 — per-call boundary: one raising call must not abort its siblings; C..." -- suppression comment: keep the pragma and its error code, and keep the justification text; strip only the plan/requirement identifier reference.
- Line 154: "tasks gets its own lifecycle row (wfaudit002 REQ-001). The wire key the" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 155: "transport sends stays the unscoped transport key (REQ-002); the audit-only" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 156: "_idempotency_key above stays separate (REQ-009)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 167: "Single source of truth is shared.tool_constants.RETRYABLE_TOOLS (REQ-006 /" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 171: "dispatcher's config/mcp_dedup.toml (REQ-004). Mirrors the dispatcher's own" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 178: """"Write the pending tool_call_state row before dispatch (REQ-001/REQ-008)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 181: "task context unwired, or the write failed (REQ-007: recording failure is" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 191: "except Exception as exc:  # noqa: BLE001 — recording failure must not break tool execution (REQ-007); args ar..." -- suppression comment: keep the pragma and its error code, and keep the justification text; strip only the plan/requirement identifier reference.
- Line 198: """"Move the tool_call_state row to its terminal state (REQ-002/REQ-003)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 202: "pending for classify_stale_pending (REQ-004)." -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Line 211: "except Exception as exc:  # noqa: BLE001 — recording failure must not break tool execution (REQ-007)" -- suppression comment: keep the pragma and its error code, and keep the justification text; strip only the plan/requirement identifier reference.
- Line 233: "# Classify once before execution (REQ-006): non-READ (incl. UNKNOWN) calls" -- remove the plan/requirement identifier reference and rewrite the remaining comment or docstring text in current tense.
- Keep each module docstring's first line (the path header verified by `check_docstrings.py`) and all ADR markers unchanged.

## Compatibility considerations
- No runtime, configuration, or schema surface change; deployed copies are refreshed by deploy.sh.

## Security considerations
- N/A: comments only.

## Rollback considerations
- Revert the comment and docstring edits; there is no code change to roll back.

## Validation plan
- `rg -n "Extracted from|Refactored:|RAGCORPUS001|EBAUTHGEN001|crawl003|REQ-[0-9]+" scripts/agent/tool_runner.py` returns nothing.
- `uv run pytest tests/agent` continues to pass.
- Comment-only guarantee: `git diff -U0` shows no changed line other than comment and docstring lines.
- `uv run python tools/check_suppression_justification.py` reports no finding for this file.

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
- **Related target files**: `scripts/agent/tool_runner.py`
