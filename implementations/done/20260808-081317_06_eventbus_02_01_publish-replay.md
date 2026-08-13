## Goal
- Restructure `docs/06_eventbus_02_01_publish-replay.md` to remove implementation details like complete JSON examples and JSON Schema field tables while explicitly preserving pub idempotency, JSONL-append failure handling, and SSE vs JSON replay usage distinction.

## Scope
- **In-Scope**: `docs/06_eventbus_02_01_publish-replay.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other eventbus chapters (`docs/06_eventbus_*.md`), Reference API chapter (`docs/06_eventbus_06_02_reference-api-route-handlers.md`), source code changes, tests

## Assumptions
- `memo-doc-eventbus-review.md` exists and its guidance is valid (independently verified)
- Pub idempotency judgment and replay source object must not be deleted
- Existing internal links and cross-references must remain valid after editing

## Design decisions
- Compress or remove complete request body JSON examples
- Remove JSON Schema field tables
- Remove UUID regex patterns
- Remove complete response field enumeration
- Remove 422 validation details
- Remove mechanical explanations of limit/offset/format parameters
- Preserve: why pub is idempotent, duplicate event_id rejection decision, SQLite commit vs JSONL append priority, JSONL-append-failure-still-pub-success judgment, replay reads from SQLite as source-of-truth, SSE vs JSON replay usage distinction, SSE replay operational note about pagination continuation suitability

## Alternatives considered
- Keeping complete JSON examples but adding a note pointing to Reference API chapter as canonical
- Converting JSON examples to prose descriptions instead of removing them
- Moving detailed parameter specifications to an appendix rather than removing them

## Implementation
### Target file
- `docs/06_eventbus_02_01_publish-replay.md`

### Procedure
#### Phase 1: Preparation
1. Read `memo-doc-eventbus-review.md` §「06_eventbus_02_01_publish-replay」keep/remove guidance
2. Analyze current document structure to identify where pub/replay design judgments are distributed

#### Phase 2: Core Logic Implementation
1. Compress or remove complete request body JSON examples
   - Replace with brief description of expected payload shape
2. Remove JSON Schema field tables
   - Delete field-by-field type/default-value listings
3. Remove UUID regex patterns
   - Delete UUID format specification details
4. Remove complete response field enumeration
   - Delete exhaustive HTTP status code + field mappings
5. Remove 422 validation details
   - Delete specific validation error message formats
6. Remove mechanical explanations of limit/offset/format parameters
   - Delete parameter-by-parameter type/constraint descriptions
7. Preserve design-critical information:
   - Why pub is idempotent (duplicate event_id rejection)
   - SQLite commit vs JSONL append priority order
   - JSONL-append-failure-is-still-pub-success judgment
   - Replay reads from SQLite as trusted source
   - SSE vs JSON replay usage distinction
   - SSE replay operational note about pagination continuation suitability

#### Phase 3: Deployment & Verification
1. Confirm cross-reference to Reference API chapter exists for all removed details
2. Validate internal Markdown links and cross-references
3. Confirm chapter follows standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」

### Method
- Document restructuring only; no source code changes
- Use grep to verify link integrity before and after editing
- Manual verification of cross-references post-edit
- Explicitly preserve pub idempotency and replay source-of-truth statements during trimming

### Details
- Focus on reducing implementation-derived detail while preserving design intent
- Pub idempotency is critical architectural constraint — must survive unchanged
- Replay source-of-truth statement is critical — must survive unchanged
- Ensure navigation remains functional for both human and AI consumers

## Compatibility considerations
- No API changes — documentation-only update
- Internal cross-references must remain valid after restructuring
- Pub idempotency and replay source-of-truth statements must survive unchanged

## Security considerations
- N/A — documentation-only change

## Rollback considerations
- Preserve pre-edit backup of pub idempotency and replay source-of-truth sections
- If these statements are accidentally weakened, revert immediately

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Cross-references | Manual | All removed details point to Reference API chapter |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」 |
| Detail Reduction | Manual | No complete JSON examples or field tables remain |

## Out of scope
- Other eventbus chapters (`docs/06_eventbus_*.md`)
- Reference API chapter (`docs/06_eventbus_06_02_reference-api-route-handlers.md`)
- Source code changes
- Test updates

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-173252_require.md
- Source plan: plans/20260807-203527_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-081317
- Related target files: docs/06_eventbus_02_01_publish-replay.md
