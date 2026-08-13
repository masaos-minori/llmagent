## Goal
- Restructure `docs/06_eventbus_02_01_publish-replay.md` to remove implementation details like complete JSON examples and JSON Schema field tables while explicitly preserving why publish is idempotent, why JSONL append failure does not become publish failure, and when to use SSE vs JSON replay.

## Scope
- **In-Scope**: `docs/06_eventbus_02_01_publish-replay.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other eventbus chapters (`docs/06_eventbus_*.md`), source code changes, tests

## Assumptions
- `memo-doc-eventbus-review.md` was deleted but issue claims remain valid through independent verification against source code
- SSE vs JSON replay usage guidance must not be deleted
- Existing internal links and cross-references must remain valid after editing

## Design decisions
- Compress or remove complete request body JSON example
- Compress or remove JSON Schema field table
- Compress or remove regex patterns
- Compress or remove complete response field enumeration
- Compress or remove 422 validation details
- Compress or remove mechanical explanation of `limit`/`offset`/`format`
- Preserve: why publish is idempotent, duplicate `event_id` is not redelivered, SQLite commit vs JSONL append priority order, JSONL append failure still counts as publish success, replay reads from SQLite as true source, SSE replay vs JSON replay usage scenarios, SSE replay operational note about pagination continuation suitability

## Alternatives considered
- Keeping complete JSON examples but adding a note pointing to Reference API chapter as canonical
- Converting edge case descriptions to prose instead of removing them
- Moving detailed validation specifications to an appendix rather than removing them

## Implementation
### Target file
- `docs/06_eventbus_02_01_publish-replay.md`

### Procedure
#### Phase 1: Preparation
1. Analyze current document structure to identify where publish/replay design judgments are distributed

#### Phase 2: Core Logic Implementation
1. Compress or remove complete request body JSON example
   - Replace with brief description of expected payload shape
2. Compress or remove JSON Schema field table
   - Delete field-by-field type/default-value listings
3. Compress or remove regex patterns
   - Delete UUID format specification details
4. Compress or remove complete response field enumeration
   - Delete exhaustive HTTP status code + field mappings
5. Compress or remove 422 validation details
   - Delete specific validation error message formats
6. Compress or remove mechanical explanation of `limit`/`offset`/`format`
   - Delete parameter-by-parameter constraint descriptions
7. Preserve design-critical information:
   - Why publish is idempotent
   - Duplicate `event_id` is not redelivered
   - SQLite commit vs JSONL append priority order
   - JSONL append failure still counts as publish success
   - Replay reads from SQLite as true source
   - SSE replay vs JSON replay usage scenarios
   - SSE replay operational note about pagination continuation suitability

#### Phase 3: Deployment & Verification
1. Confirm SSE vs JSON replay usage guidance was not silently dropped or weakened
2. Confirm cross-reference to OpenAPI schema and `publish_route.py` and `replay_route.py` exists
3. Validate internal Markdown links and cross-references
4. Confirm chapter follows standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」

### Method
- Document restructuring only; no source code changes
- Use grep to verify link integrity before and after editing
- Manual verification of cross-references post-edit
- Explicitly preserve idempotency rationale and SSE vs JSON replay guidance during trimming

### Details
- Focus on reducing implementation-derived detail while preserving design intent
- Publish idempotency is critical architectural constraint — must survive unchanged
- SSE vs JSON replay usage guidance is critical — must survive unchanged
- Ensure navigation remains functional for both human and AI consumers

## Compatibility considerations
- No API changes — documentation-only update
- Internal cross-references must remain valid after restructuring
- Publish idempotency and SSE vs JSON replay statements must survive unchanged

## Security considerations
- N/A — documentation-only change

## Rollback considerations
- Preserve pre-edit backup of publish idempotency and SSE vs JSON replay sections
- If these statements are accidentally weakened, revert immediately

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Idempotency Rationale | Manual | Explicitly preserved |
| SSE vs JSON Replay Guidance | Manual | Explicitly preserved |
| Cross-references | Manual | All removed details point to OpenAPI schema / publish_route.py / replay_route.py |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」 |

## Out of scope
- Other eventbus chapters (`docs/06_eventbus_*.md`)
- Source code changes
- Test updates

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-180654_require.md
- Source plan: plans/20260807-205446_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-082822
- Related target files: docs/06_eventbus_02_01_publish-replay.md
