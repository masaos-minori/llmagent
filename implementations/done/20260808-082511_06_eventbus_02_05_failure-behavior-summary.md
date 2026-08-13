## Goal
- Restructure `docs/06_eventbus_02_05_failure-behavior-summary.md` to remove implementation details like mechanical HTTP status→response mapping tables and error code enumeration while explicitly preserving what takes priority during failures, operational implications (publish success but JSONL-only failure afterward, slow consumer experiencing event drops, degraded health as alert signal, 409 on requeue).

## Scope
- **In-Scope**: `docs/06_eventbus_02_05_failure-behavior-summary.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other eventbus chapters (`docs/06_eventbus_*.md`), source code changes, tests

## Assumptions
- `memo-doc-eventbus-review.md` was deleted but issue claims remain valid through independent verification against source code
- Failure priority ordering and its operational consequences must not be deleted
- Existing internal links and cross-references must remain valid after editing

## Design decisions
- Compress or remove mechanical HTTP status→response mapping table
- Compress or remove filename-based justification memo
- Compress or remove simple error code enumeration
- Preserve: failure priority ordering (SQLite commit, JSONL archive, broker notification, consumer replay, DLQ promotion)
- Preserve: JSONL-only can fail after publish success
- Preserve: slow consumer can experience event drops
- Preserve: degraded health should be used as operational alert signal
- Preserve: meaning of 409 on requeue

## Alternatives considered
- Keeping complete error code listing but adding a note pointing to Reference API chapter as canonical
- Converting error mappings to prose instead of removing them
- Moving detailed validation specifications to an appendix rather than removing them

## Implementation
### Target file
- `docs/06_eventbus_02_05_failure-behavior-summary.md`

### Procedure
#### Phase 1: Preparation
1. Analyze current document structure to identify where failure behavior design judgments are distributed

#### Phase 2: Core Logic Implementation
1. Compress or remove mechanical HTTP status→response mapping table
   - Replace with brief description of expected payload shape
2. Compress or remove filename-based justification memo
   - Delete rationale text for specific filenames
3. Compress or remove simple error code enumeration
   - Delete exhaustive error code listings
4. Preserve design-critical information:
   - Failure priority ordering (SQLite commit, JSONL archive, broker notification, consumer replay, DLQ promotion)
   - JSONL-only can fail after publish success
   - Slow consumer can experience event drops
   - Degraded health should be used as operational alert signal
   - Meaning of 409 on requeue

#### Phase 3: Deployment & Verification
1. Confirm failure priority ordering was not silently dropped or weakened
2. Confirm cross-reference to relevant source files exists
3. Validate internal Markdown links and cross-references
4. Confirm chapter follows standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」

### Method
- Document restructuring only; no source code changes
- Use grep to verify link integrity before and after editing
- Manual verification of cross-references post-edit
- Explicitly preserve failure priority ordering and operational implications during trimming

### Details
- Focus on reducing implementation-derived detail while preserving design intent
- Failure priority ordering is critical — must survive unchanged
- Operational implications are critical — must survive unchanged
- Ensure navigation remains functional for both human and AI consumers

## Compatibility considerations
- No API changes — documentation-only update
- Internal cross-references must remain valid after restructuring
- Failure priority ordering and operational implications must survive unchanged

## Security considerations
- N/A — documentation-only change

## Rollback considerations
- Preserve pre-edit backup of failure priority ordering and operational sections
- If these statements are accidentally weakened, revert immediately

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Failure Priority Ordering | Manual | Explicitly preserved |
| Operational Implications | Manual | Explicitly preserved |
| Cross-references | Manual | All removed details point to publish_route.py / broker.py / dlq_route.py / health_route.py |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」 |

## Out of scope
- Other eventbus chapters (`docs/06_eventbus_*.md`)
- Source code changes
- Test updates

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-180235_require.md
- Source plan: plans/20260807-205237_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-082511
- Related target files: docs/06_eventbus_02_05_failure-behavior-summary.md
