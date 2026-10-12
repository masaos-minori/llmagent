# Confirm external consumers of NACK response and NackResult counters

## Priority
Low

## Summary
Confirm with the eventbus owner whether any consumer outside this repository depends on the events-level meaning of `delivery_failure_count` and `cycle_failure_count`, either in the NACK HTTP response or in `eventbus.db.NackResult`. The answer decides whether the current "legacy value" contract is safe or needs a follow-up change.

## Background
- `plans/done/20261012-084200_plan.md` kept the legacy-value contract for the `NackResult` counters and resolved UNK-01 (no separation) on repository evidence only. Its UNK-02 stayed open because external use cannot be established from the repository.
- Repository evidence (`Explicit in code`): outside `scripts/eventbus/` no module calls the NACK endpoint or `nack_event`; the only non-test reader of `NackResult` is the NACK route. No in-repository HTTP client of `/nack` was found.
- The NACK response field `delivery_failure_count` carries the per-consumer failure count, not the events-level value; the endpoint reference now says so.
- The DLQ listing documents a per-entry `delivery_failure_count` that comes from the events-level column, which is a legacy value under the per-consumer model (`Derived from confirmed evidence`: the NACK path no longer writes it).

## Problem
- If an external client reads the NACK response `delivery_failure_count` expecting an event-level lifetime count, or reads the DLQ listing's `delivery_failure_count` expecting a live count, it receives per-consumer or stale legacy values.
- That cannot be ruled out from the repository, so the contract decision rests on an unverified assumption (`Needs confirmation`).

## Reason for Change
- Closing an open assumption behind a contract decision; no known defect.
- Low priority: no in-repository dependency exists, and behavior is covered by tests.

## Implementation Intent
- Obtain a recorded answer from the owner (or from the operators of known consumers) and write the outcome into the documentation and the plan trail.
- If no external consumer depends on the events-level meaning, state in the documentation that the fields are legacy values and finish.
- If one does, open a separate issue for the contract change; do not change code in this issue.

## Target Files or Areas
- `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` (NACK response field description)
- `docs/24_eventbus/eventbus_04_dlq_endpoint.md` (DLQ listing field `delivery_failure_count`)
- `plans/done/20261012-084200_plan.md` (record the resolution of UNK-02)

## Required Changes
- Ask the owner whether external consumers of the NACK response, the DLQ listing, or `NackResult` rely on the events-level counters, and record the answer with its date.
- Record the resolution of UNK-02 in the plan.
- Update the two documents only if the answer changes what they should say about these fields.

## Constraints
- Documentation and records only; do not change code, tests, the schema, or response shapes.
- Do not infer consumer behavior without an owner answer; if none is obtained, leave the item open.
- Follow the docs content policy (no line numbers, concrete config values or implementation counts).

## Acceptance Criteria
- A dated owner answer on external use is recorded, or the item is explicitly left open with the reason.
- UNK-02 in `plans/done/20261012-084200_plan.md` shows the outcome.
- The two documents agree with the recorded answer about the meaning of `delivery_failure_count`.
- The documentation checkers named in `routing.md` "When to run which tool" report no findings for any edited document.

## Testing Expectations
- Documentation-only; run the documentation checkers on edited documents.

## Documentation Impact
Possibly the two eventbus documents above: state that the DLQ listing and NACK response counters are legacy or per-consumer values, as the answer dictates. Record behavior and boundaries, not implementation counts.

## Out of Scope
- Any code, test, schema, or response-shape change.
- Dropping or migrating the events-level columns.
- Changes to DLQ promotion or ACK behavior.

## Dependencies
- Follows `plans/done/20261012-084200_plan.md` (UNK-02). Needs an answer from the eventbus owner; no other blocking dependency.

## Unresolved Questions
- Who is the eventbus owner able to answer? `Unknown`; ownership is not recorded in the repository evidence reviewed.
- Does the DLQ listing's `delivery_failure_count` need its own documentation caveat? `Needs confirmation`; default is to add one only if the owner confirms external readers.

## AI Implementation Instruction
- Do not guess the owner's answer; ask, or record the item as open.
- Edit only the listed documents and the plan's UNK-02 entry; do not touch code or tests.
- Run the documentation checkers before reporting completion.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261012-084200_plan.md` (Unknown UNK-02)
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261012-090140
- **Related target files**: `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`, `docs/24_eventbus/eventbus_04_dlq_endpoint.md`, `plans/done/20261012-084200_plan.md`
