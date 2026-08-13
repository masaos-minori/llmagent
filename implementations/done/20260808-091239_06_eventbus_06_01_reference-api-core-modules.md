## Goal
- Separate eventbus design documentation Reference API chapter, removing implementation details like complete per-module API listings and function signature tables while recording the decision whether to retain only a minimal reference index or replace with auto-generation.

## Scope
- **In-Scope**: `docs/06_eventbus_06_01_reference-api-core-modules.md`, `docs/06_eventbus_06_02_reference-api-route-handlers.md`, `docs/06_eventbus_06_03_reference-api-broker-and-offsets.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other eventbus chapters (`docs/06_eventbus_*.md`), source code changes, tests

## Assumptions
- `memo-doc-eventbus-review.md` was deleted but issue claims remain valid via independent verification against source code
- Existing internal links and cross-references must remain valid after editing
- Document owner decision on whether to keep as minimal index or auto-generate is pending

## Design decisions
- Compress or remove complete per-module API listings (e.g., from `scripts/eventbus/app.py`)
- Compress or remove function signature tables
- Compress or remove response field tables per route handler
- Compress or remove complete DB schema tables
- Compress or remove `route_helpers.py` internal helper enumeration
- Compress or remove `_Subscriber` internal data structure explanation
- Compress or remove `offsets.py` function explanations
- If retaining: keep only minimal index — core (app/config/db/dlq), routes (publish/replay/subscribe/ack/nack/dlq/health), broker (EventBroker), offsets (read/write offset) — "see code for details"

## Alternatives considered
- Keeping complete API listings but adding a note pointing to source code as canonical
- Converting API listings to prose descriptions instead of removing them
- Moving detailed API information to an appendix rather than removing it
- Auto-generating API documentation from source code annotations

## Implementation
### Target files
- `docs/06_eventbus_06_01_reference-api-core-modules.md`
- `docs/06_eventbus_06_02_reference-api-route-handlers.md`
- `docs/06_eventbus_06_03_reference-api-broker-and-offsets.md`

### Procedure
#### Phase 1: Preparation
1. Analyze current document structure to identify where API design judgments are distributed
2. Obtain document owner decision: keep as minimal reference index OR replace with auto-generation
3. Identify all API listings, function signatures, and response field tables across all three files

#### Phase 2: Core Logic Implementation
1. Compress or remove complete per-module API listings
   - Replace with high-level module purpose description
2. Compress or remove function signature tables
   - Delete exhaustive parameter type/constraint listings
3. Compress or remove response field tables per route handler
   - Delete field-by-field HTTP status + field mapping
4. Compress or remove complete DB schema tables
   - Delete column list tables
5. Compress or remove `route_helpers.py` internal helper enumeration
   - Delete list of internal helper functions
6. Compress or remove `_Subscriber` internal data structure explanation
   - Delete internal class attribute listings
7. Compress or remove `offsets.py` function explanations
   - Delete function-by-function behavior descriptions
8. If retaining minimal index:
   - Keep only: core modules (app/config/db/dlq), routes (publish/replay/subscribe/ack/nack/dlq/health), broker (EventBroker), offsets (read/write offset)
   - Add "see code for details" note for each entry

#### Phase 3: Deployment & Verification
1. Audit other `06_eventbus_*.md` chapters for duplicate API/type/method details; replace with pointers here if found
2. Before deleting content, confirm it is not the sole documented source for any specific API's rationale
3. Validate internal Markdown links and cross-references
4. Confirm chapters follow standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」

### Method
- Document restructuring only; no source code changes
- Use grep to verify link integrity before and after editing
- Manual verification of cross-references post-edit
- Explicitly record document owner decision in Traceability section

### Details
- Focus on reducing implementation-derived detail while preserving design intent
- Document owner decision on minimal index vs auto-generation is critical — must be recorded
- Ensure navigation remains functional for both human and AI consumers

## Compatibility considerations
- No API changes — documentation-only update
- Internal cross-references must remain valid after restructuring
- Document owner decision must survive unchanged

## Security considerations
- N/A — documentation-only change

## Rollback considerations
- Preserve pre-edit backup of API listing sections before deletion
- If API references are accidentally weakened, revert immediately

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Decision Recorded | Manual | Whether to keep as minimal index or auto-generate |
| Cross-references | Manual | All removed details point to code |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」 |
| Detail Reduction | Manual | No complete API listings or function signature tables remain |

## Out of scope
- Other eventbus chapters (`docs/06_eventbus_*.md`)
- Source code changes
- Test updates

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-174924_require.md
- Source plan: plans/20260807-204924_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-091239
- Related target files: docs/06_eventbus_06_01_reference-api-core-modules.md, docs/06_eventbus_06_02_reference-api-route-handlers.md, docs/06_eventbus_06_03_reference-api-broker-and-offsets.md
