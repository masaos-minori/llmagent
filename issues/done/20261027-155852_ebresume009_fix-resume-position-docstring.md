# Correct the get_resume_position docstring to match its behavior

## Priority
Low

## Summary
Fix the `get_resume_position()` docstring in `scripts/eventbus/delivery_repo.py`, which says the function returns the maximum of the stored offset and the lowest unacknowledged sequence, while the implementation returns the lowest unacknowledged sequence when one exists and `stored_offset + 1` otherwise.

## Background
Source: `memo-issue.md` Issue 12, re-verified against current source on 2026-10-27. The rest of the memo item (removed slash commands, obsolete Workflow descriptions, a malformed ADR dependency-graph line) was not confirmed: `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` passes on the current tree, and the malformed graph line was not located.

- Docstring: "Returns the maximum of: the stored offset ...; the lowest unacked seq among events with seq <= stored offset". `Explicit in code`.
- Implementation: returns `0` when no offset row exists; otherwise runs `MIN(e.seq)` over unacked or undelivered events with `seq <= stored_offset` and returns it when found, else `stored_offset + 1`. `Explicit in code`.
- The lowest unacked seq is at most the stored offset, so the "maximum" wording is wrong. Documentation under `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` already says the position is `lowest_unacked_seq` when an unacked event exists. `Documentation only` (docs not compared line by line).
- Related: `issues/done/20261007-164638_ebresume01_fix-off-by-one-in-eventbus-subscribe-resume-position.md` changed the behavior, not this docstring.

## Problem
The docstring describes behavior that contradicts the code and the documentation, which can mislead a reader implementing a consumer or a test.

## Reason for Change
Documentation/code mismatch that misleads understanding but cannot by itself cause a wrong operator action (Phase 7 tie-breaking: Low). Fixing it now avoids repeating the wrong statement in later issues.

## Implementation Intent
Change only the docstring so it states the three outcomes (no offset row: 0; unacked event at or below the stored offset: lowest such seq; otherwise: stored offset plus one). Do not change the function.

## Target Files or Areas
- `scripts/eventbus/delivery_repo.py` (docstring of `get_resume_position`)

## Required Changes
- Rewrite the docstring "Returns" description to match the implemented rule and the terminology of `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`.
- Verify the `Returns` section and the "ensures no unacked event is skipped" sentence still hold after the rewrite.

## Constraints
- No behavior change; no signature change.
- Keep the wording consistent with ADR-006 resume terminology.

## Acceptance Criteria
- The docstring describes exactly the behavior of the function, with no mention of a maximum.
- The existing resume-position tests and boundary tests still pass.

## Testing Expectations
- `uv run pytest tests/eventbus -q`, ruff on the changed file. A new test is not required because behavior is unchanged.

## Documentation Impact
No change expected in `docs/`, since the docs already state the rule; confirm with `uv run python tools/check_docs_consistency.py --domain eventbus`.

## Out of Scope
- The removed slash commands, Workflow bypass text and ADR dependency-graph formatting (not confirmed; file separately with evidence if found).
- Any change to resume or replay behavior.

## Dependencies
N/A: none.

## Unresolved Questions
- Where is the "malformed ADR dependency-graph line" mentioned in the memo? `Needs confirmation`; not found in this verification and excluded from this issue.

## AI Implementation Instruction
Edit the docstring only. Do not touch other functions or docs. If you find the docs also contradict the implementation, stop and report instead of editing them here.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-155852
- **Related target files**: `scripts/eventbus/delivery_repo.py`
