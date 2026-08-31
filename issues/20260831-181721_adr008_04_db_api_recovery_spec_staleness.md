# `90_shared_05_04` sections 9.3/9.4/9.7 describe pre-fix recovery behavior that no longer matches code or ADR-008

## Priority
Medium

## Summary
`docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md` sections 9.3, 9.4, and
9.7 describe `recover_corruption()` behavior that predates the SHARED-001/SHARED-002 fixes and
no longer matches `scripts/db/recovery.py` or the consolidated `docs/adr/ADR-008-sqlite-4db-separation.md`.

## Background
Confirmed by reading `scripts/db/recovery.py` in full during the ADR-011 → ADR-008 merge
(2026-08-31) and comparing it against this Specification's text.

## Problem
(Evidence: Explicit in code vs. explicit in document)
- Section 9.3 states "the current implementation does not produce a structured classification,"
  but `_classify_error()`/`DbCondition` already implement one.
- Section 9.4 states `sqlite3.DatabaseError` "propagates uncaught instead of reaching the
  restore branch," but `_classify_error()` now catches it and classifies it as
  `DbCondition.CORRUPTION`.
- Section 9.7 states passing `target='workflow'`/`'eventbus'` is "unsafe" and callers "MUST NOT"
  do so because the display-path branch is mismatched, but current code explicitly supports and
  correctly handles both targets (returning `no_recovery_allowed`), per the SHARED-003 partial
  resolution and ADR-008 Decision Details #20.

## Reason for Change
A Specification describing already-fixed behavior as current will mislead a reader into
believing gaps exist that have been closed, or into avoiding a code path
(`target='workflow'/'eventbus'`) that is now safe to use exactly as ADR-008 describes.

## Implementation Intent
Update sections 9.3, 9.4, and 9.7 to describe the current, post-fix behavior, and cross-reference
ADR-008 as the canonical source for the recovery decision itself (per this repository's
Canonical Source Precedence, ADRs outrank Specifications for adopted architecture decisions).

## Target Files or Areas
`docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md` (sections 9.3, 9.4, 9.7)

## Required Changes
- Section 9.3: replace "does not produce a structured classification" with a description of the
  current `DbCondition` enum classification.
- Section 9.4: replace "propagates uncaught" with the current `_classify_error()` catch-and-
  classify behavior (the same section's 9.9 already carries a partial "corrected from prior
  wording" note — reconcile 9.4 with that correction).
- Section 9.7: replace the "MUST NOT pass 'workflow' or 'eventbus'" guidance with the current
  supported behavior (both targets are valid; both return `no_recovery_allowed` per ADR-008
  Decision Details #20).
- Add a cross-reference to ADR-008 as the canonical source for recovery policy.

## Constraints
- Do not change this Specification's scope beyond sections 9.3/9.4/9.7 and their immediate
  cross-references.
- Do not restate ADR-008's full Decision text here — reference it per `skills/DESIGN.md` Avoid
  implementation-reference duplication.

## Acceptance Criteria
- Sections 9.3, 9.4, and 9.7 accurately describe current `scripts/db/recovery.py` behavior.
- The document references ADR-008 for the recovery policy decision rather than restating it.
- `uv run python tools/check_docs_quality.py docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md` shows no new issues.

## Testing Expectations
Documentation-only change; not required beyond the validation command above.

## Documentation Impact
This issue is itself the documentation-accuracy fix.

## Out of Scope
- Sections of this document unrelated to 9.3/9.4/9.7.
- Changing recovery behavior in code.

## Dependencies
Follows the 2026-08-31 ADR-011 → ADR-008 consolidation.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Read `scripts/db/recovery.py` in full before editing this document, to avoid re-describing
another stale state. Reference ADR-008 rather than duplicating its Decision text.
