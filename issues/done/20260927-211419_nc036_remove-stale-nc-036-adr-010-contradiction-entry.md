# Remove stale NC-036 ADR-010 contradiction entry

## Priority
Medium

## Summary
Remove NC-036 from `governance_03`'s Needs Confirmation inventory — the ADR-010 Decision #9 contradiction it describes has already been fixed in code — and clean up one leftover misleading log message from before the fix.

## Background
NC-036 asked whether `call_rag_service()`'s parse-error-triggers-fallback behavior was an intentional refinement of ADR-010 Decision #9, or an unintended deviation, citing the test `test_json_parse_error_calls_set_fallback_reason` as evidence the deviation was actively defended. A deep-dive investigation (2026-09-27) found this is already resolved in code: commits `ba82419b` ("fix(pipeline_service): return empty string instead of None on JSON parse errors per ADR-010 Decision #9; update docstring and test") and `4ee51b8d` ("fix: remove spurious _set_fallback_reason call on JSON parse error (ADR-010 INV-07 compliance)", 2026-09-25) both directly fixed this. Current code in `scripts/rag/pipeline_service.py`'s `except ValueError` branch returns `""` and does not call `set_fallback_reason`, matching Decision #9 exactly. The test cited in NC-036 no longer exists — it was renamed to `test_json_parse_error_does_not_call_set_fallback_reason` and now asserts the opposite (`assert len(reasons) == 0`).

## Problem
NC-036's entry describes a contradiction and a test that no longer exist — the entry is stale, not an open question requiring `@data-eng`'s judgment as currently recorded.

## Reason for Change
Per `rules/coding.md`'s Current-Specification-Only Policy, a resolved item must be removed from the active inventory, not retained with a closed-out status or left describing pre-fix behavior.

## Implementation Intent
Remove the NC-036 entry from `governance_03`. Separately, fix the one leftover misleading log message the deep-dive found in the same `except ValueError` branch — it still says "falling back to in-process," text left over from before the fix, now inaccurate since the branch returns an empty string rather than triggering fallback.

## Target Files or Areas
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (remove NC-036 entry)
- `scripts/rag/pipeline_service.py` (fix the leftover log message in the `except ValueError` branch)

## Required Changes
- Remove the `#### NC-036` block from `governance_03` Part 2.
- Update the log message in `call_rag_service()`'s `except ValueError` branch to accurately describe returning an empty result, not "falling back to in-process."

## Constraints
No behavior change — only the log message text changes; the actual return-empty-string-on-parse-error behavior is already correct and must not be altered.

## Acceptance Criteria
- NC-036 no longer appears in `governance_03`.
- The `except ValueError` branch's log message accurately reflects current behavior (no mention of falling back).
- Full test suite passes with no regression (existing `test_json_parse_error_does_not_call_set_fallback_reason` continues to pass unchanged).

## Testing Expectations
No new test required for the log-message wording fix (not behavior-affecting); run the existing targeted test plus the full suite once to confirm no regression, per `rules/toolchain.md`.

## Documentation Impact
`governance_03`'s NC-036 entry removed; no other documentation is affected.

## Out of Scope
- Re-verifying ADR-010 Decision #9 compliance itself (already confirmed fixed by the cited commits).
- Any other `pipeline_service.py` behavior beyond the one log message.

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none — confirmed resolved-in-code by the 2026-09-27 deep-dive investigation; no `@data-eng`/architect judgment is actually needed anymore, contrary to what NC-036's current entry states.

## AI Implementation Instruction
Verify via `git show`/`rg` that the cited commits and current code state genuinely match Decision #9 before removing the entry (do not trust the investigation summary alone). Keep the log-message fix to the exact line identified — do not rewrite the surrounding function.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260927-211419
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md, scripts/rag/pipeline_service.py
