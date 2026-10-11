# Correct stale nack_event docstring and generated reference description

## Priority
Low

## Summary
The `nack_event` docstring in `scripts/eventbus/delivery_repo.py` says it increments `delivery_failure_count` and `cycle_failure_count` for an event. Under the per-consumer model only the per-consumer counter in `consumer_delivery` is written. Correct the docstring so that the auto-generated description in the eventbus reference API document is accurate.

## Background
- The auto-generated block of `eventbus_08_reference_api.md` takes each function description from the first line of its docstring.
- While regenerating that block for `plans/done/20261011-204704_plan.md`, the `nack_event` row was found to still read "Increment delivery_failure_count and cycle_failure_count for an event." This could not be fixed on the documentation side because the block is generated.
- An inline comment in `nack_event` already states that the events-level counters are kept for backward compatibility and are no longer written under the per-consumer model.

## Problem
- Evidence (`Explicit in code`): the `nack_event` docstring summary line and the opening of its description describe incrementing the events-level counters, while the function body only upserts `consumer_delivery_failure_count` and `consumer_last_nack_attempt`, and reads the events-level counters back for the return value.
- Evidence (`Explicit in documentation`): the generated row in `eventbus_08_reference_api.md` repeats the stale summary line.
- A reader of the reference API is told the NACK path mutates event-level counters, which contradicts the per-consumer failure model used for DLQ promotion.

## Reason for Change
- Documentation/code mismatch caused by a stale docstring, surfaced in a generated public reference.
- Non-critical: behavior is correct; only the description misleads.

## Implementation Intent
- Rewrite the `nack_event` docstring summary and description to state that NACK records a per-consumer failure and attempt marker when a consumer is given, that the events-level counters are not modified, and that the returned values reflect the stored counters.
- Keep the existing statements about DLQ'd events, already-acked consumers and per-attempt idempotency, which remain accurate.
- Refresh the generated block with the repository's generator rather than editing it by hand.
- Check whether the `NackResult` docstring and the field comments have the same drift, and fix only wording that is stale.

## Target Files or Areas
- `scripts/eventbus/delivery_repo.py` (docstrings only)
- `docs/24_eventbus/eventbus_08_reference_api.md` (generated block only)

## Required Changes
- Update the `nack_event` docstring as described in Implementation Intent.
- Regenerate the eventbus reference table with `tools/generate_reference_table.py --type eventbus`.

## Constraints
- No behavior change: do not alter code statements, return values, or SQL.
- Do not edit the generated block manually.
- Keep the documentation-side content policy (no line numbers, concrete config values or implementation counts).

## Acceptance Criteria
- The `nack_event` docstring no longer claims that events-level counters are incremented.
- The generated `nack_event` row in `eventbus_08_reference_api.md` matches the new docstring summary.
- Regenerating the table a second time produces no further diff.
- The eventbus tests under `tests/eventbus` and the type and lint checks named in `rules/toolchain.md` pass unchanged.
- The documentation checkers named in `routing.md` "When to run which tool" report no findings for the edited document.

## Testing Expectations
- Docstring-only change: run `tests/eventbus`, `ruff` and `mypy` per `rules/toolchain.md` to confirm nothing else moved.
- Run the documentation checkers for the regenerated document and a second regeneration to confirm idempotence.

## Documentation Impact
The reference API document changes only through regeneration. No hand-written documentation is expected to change; if a hand-written passage describes NACK as updating events-level counters, record it as a finding rather than editing it here.

## Out of Scope
- Removing or repurposing the legacy `delivery_failure_count` and `cycle_failure_count` columns or the corresponding `NackResult` fields.
- Any change to NACK, DLQ promotion or ACK behavior.
- Other docstring drift in `scripts/eventbus/` not related to `nack_event`.

## Dependencies
- Follows `plans/done/20261011-204704_plan.md`, where this was recorded as out of scope. No blocking dependency.

## Unresolved Questions
- Are the events-level counters still read by any consumer of `NackResult` (so that the return-value wording should keep mentioning them)? `Needs confirmation`; the function body still reads them back, and the default is to describe them as legacy values that are returned but not modified.

## AI Implementation Instruction
- Edit only docstrings in `scripts/eventbus/delivery_repo.py`; do not change executable statements.
- Regenerate the reference block with the generator; do not hand-edit it.
- Stop and report if the generator produces differences in rows unrelated to `nack_event`.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261011-204704_plan.md` (out-of-scope note on the `nack_event` description)
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261011-215944
- **Related target files**: `scripts/eventbus/delivery_repo.py`, `docs/24_eventbus/eventbus_08_reference_api.md`
