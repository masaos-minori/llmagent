## Goal
- Restructure `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md` to remove implementation details like filename sanitization rules and physical offset file format descriptions while explicitly preserving at-least-once delivery guarantee, consumer idempotency requirement, consumer_id collision risk, and offset-monotonicity limitation.

## Scope
- **In-Scope**: `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other eventbus chapters (`docs/06_eventbus_*.md`), Reference API chapter (`docs/06_eventbus_06_02_reference-api-route-handlers.md`), source code changes, tests

## Assumptions
- `memo-doc-eventbus-review.md` was deleted but issue claims remain valid via independent verification against source code
- Delivery semantics constraints must not be deleted
- consumer_id collision risk should be explicitly added to this chapter as authoritative consumer responsibility section
- Existing internal links and cross-references must remain valid after editing

## Design decisions
- Compress or remove filename sanitization rules (e.g., `..`, `.`, `/` → `_`)
- Remove physical offset file format explanation ("plain text, one integer per file")
- Remove mechanical delivery guarantee table
- Remove offset_checkpoint_interval history
- Preserve: delivery is at-least-once not exactly-once, reason for duplicate delivery, consumer must assume idempotent processing (explicit), consumer_id stability requirement, consumer_id collision risk (explicit addition), offset advances only on ack, ack-offset monotonicity limitation, DLQ requeue caution, JSONL/SQLite/DLQ file reliability role division

## Alternatives considered
- Keeping detailed filename sanitization rules but adding a note pointing to offsets.py as canonical
- Converting delivery guarantee table to prose descriptions instead of removing it
- Moving detailed offset mechanics to an appendix rather than removing them

## Implementation
### Target file
- `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`

### Procedure
#### Phase 1: Preparation
1. Analyze current document structure to identify where delivery semantics constraints are distributed
2. Identify all filename sanitization, offset file format, and delivery guarantee sections

#### Phase 2: Core Logic Implementation
1. Compress or remove filename sanitization rules
   - Replace with high-level description that filenames are sanitized for safety
2. Remove physical offset file format description
   - Delete "plain text, one integer per file" explanation
3. Remove mechanical delivery guarantee table
   - Delete exhaustive at-least-once/exactly-once/at-most-once mapping
4. Remove offset_checkpoint_interval history
   - Delete version-by-version checkpoint interval change descriptions
5. Preserve delivery-critical information:
   - Delivery is at-least-once, not exactly-once
   - Reason duplicate delivery occurs (crash between ack and offset commit)
   - Consumer must implement idempotent processing (explicit statement)
   - consumer_id stability requirement
   - consumer_id collision risk (explicit addition — new content)
   - Offset advances only on ack
   - Ack-offset monotonicity limitation (non-monotonic offset possible)
   - DLQ requeue caution
   - JSONL/SQLite/DLQ file reliability role division

#### Phase 3: Deployment & Verification
1. Confirm delivery semantics constraints were not weakened
2. Confirm consumer_id collision risk is explicitly stated
3. Confirm cross-reference to offsets.py and dlq.py exists for all removed details
4. Validate internal Markdown links and cross-references
5. Confirm chapter follows standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」

### Method
- Document restructuring only; no source code changes
- Use grep to verify link integrity before and after editing
- Manual verification of cross-references post-edit
- Explicitly preserve delivery semantics constraints during trimming
- Add consumer_id collision risk as new explicit section

### Details
- Focus on reducing implementation-derived detail while preserving design intent
- At-least-once delivery constraint is critical — must survive unchanged
- Consumer idempotency requirement is critical operational constraint — must survive unchanged
- consumer_id collision risk is new content that must be explicitly added
- Ensure navigation remains functional for both human and AI consumers

## Compatibility considerations
- No API changes — documentation-only update
- Internal cross-references must remain valid after restructuring
- Delivery semantics constraints must survive unchanged

## Security considerations
- N/A — documentation-only change

## Rollback considerations
- Preserve pre-edit backup of delivery semantics constraint sections
- If delivery constraints are accidentally weakened, revert immediately

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Delivery Semantics | Manual | All delivery constraints preserved |
| Consumer Idempotency | Manual | Explicitly stated |
| Consumer ID Collision | Manual | Explicitly stated |
| Cross-references | Manual | All removed details point to offsets.py / dlq.py |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」 |
| Detail Reduction | Manual | No filename sanitization rules or physical offset format descriptions remain |

## Out of scope
- Other eventbus chapters (`docs/06_eventbus_*.md`)
- Reference API chapter (`docs/06_eventbus_06_02_reference-api-route-handlers.md`)
- Source code changes
- Test updates

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-173735_require.md
- Source plan: plans/20260807-203735_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-090528
- Related target files: docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md
