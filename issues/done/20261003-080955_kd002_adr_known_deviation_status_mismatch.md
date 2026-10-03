# Resolve ADR Known Deviations status-mismatch findings (CI-001, CI-016)

## Priority
Low

## Summary
`tools/check_known_deviation_sync.py` reports `[ERROR]` status mismatches for `CI-001`
(`ADR-002`) and `CI-016` (`ADR-004`). Investigate why the checker flags these as
mismatches and resolve the finding so the checker passes without misrepresenting the true
(resolved) status.

## Background
`check_known_deviation_sync.py` cross-checks each ADR's Known Deviations references against
the Status field of the same Known Issue ID in its canonical document
(`docs/00_governance/governance_03_issue-and-uncertainty-management.md`; no
`*_90_inconsistencies_and_known_issues.md` files remain post-reorg). An `[ERROR]` is
emitted when an ADR's `## Known Deviations` labeled bullet marks an ID open-like while the
canonical Status marks it resolved-like (or vice versa).

## Problem
- `adr/ADR-002-config-isolation.md:370`: `CI-001` — canonical marks it `resolved`, but this
  ADR's Known Deviations bullet marks it `open-like`.
- `adr/ADR-004-environment-failure-handling-policy.md:537`: `CI-016` — canonical marks it
  `Resolved`, but this ADR's Known Deviations bullet marks it `open-like`.

Reading the ADRs shows each `### CI-001` / `### CI-016` subsection already records
`**Status**: resolved` (with a resolution description). The mismatch appears
self-referential: the checker reads the subsection's own `- **Known Issue**: CI-001`
labeled bullet as an independent "open" claim while simultaneously parsing the same
subsection's `**Status**: resolved` as the canonical value.

## Reason for Change
The checker exits non-zero on these `[ERROR]` lines, keeping CI noisy and masking
genuinely actionable findings. The reported inconsistency looks like a structural artifact
rather than a real open deviation, but this must be confirmed and resolved rather than
suppressed.

## Implementation Intent
High level only. Inspect how `check_known_deviation_sync.py` parses the `## Known
Deviations` section and why the internal `- **Known Issue**: <ID>` bullet collides with the
canonical Status. Determine the minimal, honest resolution, which is one of:
- restructure the affected `### CI-001` / `### CI-016` subsection format so the checker no
 longer double-reads it (without changing the documented decision or marking the status
 incorrectly), or
- confirm the finding is a checker artifact and resolve it through an accepted mechanism.

Do not change any ADR decision, invariant ID, or true status. Do not modify
`check_known_deviation_sync.py`'s `_ID_LOOKAHEAD_RE` lookahead behavior (see Constraints).

## Target Files or Areas
- `docs/10_adr/ADR-002-config-isolation.md`
- `docs/10_adr/ADR-004-environment-failure-handling-policy.md`
- Reference: `tools/check_known_deviation_sync.py` (read-only, to understand parsing)

## Required Changes
- Investigate the root cause of both `[ERROR]` findings.
- Resolve each so `check_known_deviation_sync.py` no longer reports a status mismatch for
  `CI-001` and `CI-016`.
- Preserve the documented resolution information currently in each subsection.

## Constraints
- Do not alter ADR decisions, invariant IDs, or the true resolved status.
- Do not reformat IDs to evade `_ID_LOOKAHEAD_RE`.
- Do not change the lookahead/cross-check semantics of `check_known_deviation_sync.py` —
  fix the doc representation, not the checker.
- Keep ADR text in English.

## Acceptance Criteria
- `uv run python tools/check_known_deviation_sync.py` reports no `[ERROR]` for `CI-001` or
  `CI-016`.
- No new `[ERROR]`/`[WARNING]` findings are introduced by the change.
- Each subsection still documents that the deviation is resolved.

## Testing Expectations
Documentation-only. Run `uv run python tools/check_known_deviation_sync.py` and
`uv run pytest tests/tools/test_check_known_deviation_sync.py`.

## Documentation Impact
Yes. ADR `## Known Deviations` subsection formatting, if a structural fix is required.

## Out of Scope
- Any Known Issue other than `CI-001` and `CI-016`.
- The pre-existing dangling `[WARNING]` findings (tracked separately).
- Changing `check_known_deviation_sync.py` lookahead/cross-check behavior.

## Dependencies
- Follows the kdref001 dangling-reference resolution (already completed).

## Unresolved Questions
- Is the mismatch a genuine stale update or purely a checker double-read artifact? Evidence
  currently points to the latter, but confirmation is needed before editing.
- Which minimal doc change resolves it without altering documented intent?

## AI Implementation Instruction
Read `tools/check_known_deviation_sync.py::parse_adr_references` and `cross_check` to see
how the internal `- **Known Issue**: <ID>` bullet is matched. Confirm both deviations are
resolved in the ADR text, then apply the smallest doc-only change that makes the checker
stop reporting the mismatch without misrepresenting status. Verify with the checker and
unit tests.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261003-080955
- **Related target files**: docs/10_adr/ADR-002-config-isolation.md, docs/10_adr/ADR-004-environment-failure-handling-policy.md
