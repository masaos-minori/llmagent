# Correct DLQ promotion conditions in eventbus_03 to per-consumer gating

## Priority
Medium

## Summary
`docs/24_eventbus/eventbus_03_dlq_operations.md` describes DLQ promotion in terms of the events-level `delivery_failure_count` reaching `max_retry`, for both inline promotion and the background sweep. The code and the other eventbus documents gate promotion on the per-consumer `consumer_delivery_failure_count`. Correct the document so that it agrees with the per-consumer model and with `eventbus_05_dlq_offsets_and_delivery_semantics.md`.

## Background
- `plans/done/20261012-093531_plan.md` found this drift while documenting the DLQ listing field and recorded it as out of scope, because the source issue limited edits to other documents.
- Under the per-consumer model the NACK path no longer writes the events-level counters; promotion uses `consumer_delivery_failure_count` (ADR-006 INV-13; `eventbus_05` Inline Promotion Path and Background Loop Promotion).
- `eventbus_03_dlq_operations.md` is the operations document for the DLQ and is likely read by operators.

## Problem
- Evidence (`Explicit in documentation`): the DLQ Promotion Paths section says inline promotion is triggered when a `POST /nack` call raises `delivery_failure_count` to `max_retry` or beyond, and the DLQ Background Sweep section says the sweep searches events where `delivery_failure_count >= max_retry AND dlq_at IS NULL`.
- Evidence (`Explicit in code`): the promotion query in the sweep joins `consumer_delivery` and filters on `consumer_delivery_failure_count`; the inline path in the NACK route compares the per-consumer count with `max_retry`; the events-level counters are not written by NACK, so the condition described in the document can never become true.
- An operator following the document would look at the wrong counter when diagnosing why an event was or was not promoted, and the "orphaned events" explanation built on the events-level counter would mislead.

## Reason for Change
- Documentation/code mismatch on a correctness-relevant operational behavior, in a document that contradicts `eventbus_05` and ADR-006 on the same topic.

## Implementation Intent
- Rewrite only the passages that state the promotion condition so that they describe per-consumer gating, and point to `eventbus_05_dlq_offsets_and_delivery_semantics.md` for the exact rule rather than restating it.
- Keep the description of the two paths, the shared promotion routine, and the optimistic `dlq_at IS NULL` guard, which remain accurate.
- Follow the docs content policy: describe behavior and intent, not line numbers or implementation counts.

## Target Files or Areas
- `docs/24_eventbus/eventbus_03_dlq_operations.md` (DLQ Promotion Paths and DLQ Background Sweep sections, and any other passage that uses the events-level counter as the promotion condition)

## Required Changes
- Replace the events-level `delivery_failure_count` promotion condition with the per-consumer `consumer_delivery_failure_count` condition in both sections.
- Review the explanation of orphaned events and of what a non-zero sweep count indicates, and correct it if it relies on the events-level counter.
- Add a pointer to the authoritative rule in `eventbus_05_dlq_offsets_and_delivery_semantics.md` instead of duplicating the multi-consumer condition.

## Constraints
- Documentation only; do not change code, tests, the schema, or ADR-006.
- Do not state the multi-consumer condition (any consumer versus every attempting consumer) in this document; see Unresolved Questions.
- Do not rewrite unrelated parts of the document.

## Acceptance Criteria
- No passage of `eventbus_03_dlq_operations.md` gives the events-level `delivery_failure_count` as the promotion condition.
- Both promotion paths are described in per-consumer terms consistent with `eventbus_05` and ADR-006 INV-13.
- The documentation checkers named in `routing.md` "When to run which tool" report no findings for the edited document.

## Testing Expectations
- Documentation-only; run the documentation checkers and search the document for `delivery_failure_count` to confirm the remaining mentions are intentional.
- Manual verification against the sweep query and the NACK route.

## Documentation Impact
Update `eventbus_03_dlq_operations.md` (promotion paths and background sweep). Record behavior and boundaries, not implementation counts or line numbers.

## Out of Scope
- Any code, test, schema, or ADR change.
- The multi-consumer promotion rule itself (see Unresolved Questions).
- Other eventbus documents.

## Dependencies
- Follows `plans/done/20261012-093531_plan.md` (Risks). No blocking dependency.

## Unresolved Questions
- The multi-consumer rule differs between sources: ADR-006 INV-13 and `eventbus_05` say an event promotes only when every attempting consumer has exhausted its budget and none has ACKed, while the sweep query promotes when any consumer's count reaches `max_retry` and the inline path promotes on the nacking consumer's count alone, with no check of other consumers or of ACKs (`Explicit in code`; a single-consumer test pins the single-consumer case only). Which source is authoritative is `Needs confirmation`. This issue avoids the question by pointing to `eventbus_05`; the mismatch needs its own issue and owner decision.
- Should the document keep the `delivery_failure_count` wording anywhere as a legacy value? `Needs confirmation`; default is to mention it only if needed to explain the field in the DLQ listing.

## AI Implementation Instruction
- Edit only `eventbus_03_dlq_operations.md`, and only the passages that state the promotion condition or depend on it.
- Do not assert the any-versus-every rule; link to `eventbus_05` instead.
- Run the documentation checkers before reporting completion.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261012-093531_plan.md` (Risks: drift found in eventbus_03)
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261012-095413
- **Related target files**: `docs/24_eventbus/eventbus_03_dlq_operations.md`
