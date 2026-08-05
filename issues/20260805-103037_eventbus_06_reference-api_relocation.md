# Separate docs/06_eventbus_06_{01,02,03}_reference-api-*.md from design-doc body content

## Priority
Low

## Summary
`memo-doc-eventbus-review.md` recommends considering separating the Reference API chapter out of the design-doc body entirely and treating it, at most, as a minimal "implementation reference index" — not part of the design narrative.

## Reason for Change
Full module-by-module API listings, function signatures, response-field tables, and internal data-structure descriptions mixed into the design-doc body increase maintenance burden without adding design/operational judgment. Other `06_eventbus_*.md` chapters should point here (or to code) rather than re-explaining API detail inline.

## Implementation Intent
Per `memo-doc-eventbus-review.md` §「06_eventbus_06_reference-api」: do not place this content in the design-doc body by default. If retained, keep only a minimal index (core: app/config/db/dlq; routes: publish/replay/subscribe/ack/nack/dlq/health; broker: EventBroker; offset: read/write offset) and point to code for detail.

## Target Files or Areas
- `docs/06_eventbus_06_01_reference-api-core-modules.md`
- `docs/06_eventbus_06_02_reference-api-route-handlers.md`
- `docs/06_eventbus_06_03_reference-api-broker-and-offsets.md`
- Cross-references from other `docs/06_eventbus_*.md` chapters that currently duplicate API/type/method detail instead of pointing here.

## Required Changes
- Decide (with the doc owner) whether this content should: (a) remain as a clearly separate minimal "implementation reference index," or (b) be replaced by an auto-generated reference.
- Remove: module-by-module API listings for files like `scripts/eventbus/app.py`, function-signature tables, per-route-handler response-field tables, full DB schema tables, `route_helpers.py` internal-helper listings, `_Subscriber` internal data-structure description, `offsets.py` function explanations.
- If retained, reduce to the minimal index only: core (app/config/db/dlq), routes (publish/replay/subscribe/ack/nack/dlq/health), broker (EventBroker), offset (read/write offset) — "see code for detail."
- Audit other `06_eventbus_*.md` chapters for inline API/type/method detail duplicating this content and replace with a pointer here.
- Do not delete content without confirming it is not the sole documented source for a given API's rationale.

## Acceptance Criteria
- A decision is recorded on whether these three files stay as a minimal reference index or are replaced by auto-generation.
- No full module-by-module API listing, function-signature table, or internal-data-structure description remains beyond the minimal index.
- No other `06_eventbus_*.md` chapter re-explains API/type/method detail that belongs here; each instead links to this chapter.

## Testing Expectations
Not required for behavior (documentation-only). No dedicated eventbus docs-consistency script exists; manually check internal links from other chapters that now point here.

## Documentation Impact
This issue is itself a documentation-only cleanup/relocation task.

## Out of Scope
- Generating new auto-generated API reference tooling (a separate, larger task if chosen as the direction).
- Other `docs/06_eventbus_*.md` chapters' non-API content.
- Any code under `scripts/eventbus/` — per AGENTS.md Global Rule 8, eventbus implementation changes are prohibited; this issue is documentation-only.

## AI Implementation Instruction
Follow `memo-doc-eventbus-review.md` §「06_eventbus_06_reference-api」. Do not touch any file under `scripts/eventbus/` — AGENTS.md Global Rule 8 forbids eventbus implementation changes (investigation only). This chapter has different treatment than the others (relocation/reference-index decision, not a keep/remove edit) — do not apply the standard 修正後の章構成テンプレート here unless the decision is to keep it as a design-doc chapter. Raise the (a)/(b) decision as an open question if it cannot be resolved unilaterally; mark unclear scope as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-eventbus-review.md` §「06_eventbus_06_reference-api」
- Generated at: 2026-08-05
