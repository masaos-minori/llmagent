## Goal
- Restructure `docs/06_eventbus_02_03_nack-health-dlq.md` to remove implementation details like complete response JSON examples and internal reason name enumeration while explicitly preserving that nack represents delivery failure, max_retry DLQ promotion decision, DLQ promotion file-write-before-db-update order rationale, /health degradation semantics, and that requeue does not reset failure count.

## Scope
- **In-Scope**: `docs/06_eventbus_02_03_nack-health-dlq.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other eventbus chapters (`docs/06_eventbus_*.md`), source code changes, tests

## Assumptions
- `memo-doc-eventbus-review.md` was deleted but issue claims remain valid through independent verification against source code
- Health degraded semantics and requeue failure-count-non-reset behavior must not be deleted
- Existing internal links and cross-references must remain valid after editing

## Design decisions
- Compress or remove complete response JSON examples
- Compress or remove DLQ list response field enumeration
- Compress or remove endpoint-by-endpoint parameter table
- Compress or remove internal reason name enumeration (e.g., `broker_queue_backlog_high`, etc.)
- Compress or remove detailed implementation function names
- Compress or remove edge case table implementation-level details
- Preserve: nack represents delivery failure, max_retry DLQ promotion decision, DLQ promotion file-write-before-db-update intention, /health degradation semantics, how to use /health in operational monitoring, requeue does not reset failure count, requeue is not a "second chance", events not in DLQ cannot be requeued

## Alternatives considered
- Keeping complete JSON examples but adding a note pointing to Reference API chapter as canonical
- Converting edge case descriptions to prose instead of removing them
- Moving detailed validation specifications to an appendix rather than removing them

## Implementation
### Target file
- `docs/06_eventbus_02_03_nack-health-dlq.md`

### Procedure
#### Phase 1: Preparation
1. Analyze current document structure to identify where nack/health/DLQ design judgments are distributed

#### Phase 2: Core Logic Implementation
1. Compress or remove complete response JSON examples
   - Replace with brief description of expected payload shape
2. Compress or remove DLQ list response field enumeration
   - Delete field-by-field type/default-value listings
3. Compress or remove endpoint-by-endpoint parameter table
   - Delete parameter-by-parameter constraint descriptions
4. Compress or remove internal reason name enumeration
   - Delete specific reason string values
5. Compress or remove detailed implementation function names
   - Delete function-level naming references
6. Compress or remove edge case table implementation-level details
   - Delete exhaustive edge case mappings
7. Preserve design-critical information:
   - nack represents delivery failure
   - max_retry DLQ promotion decision
   - DLQ promotion file-write-before-db-update intention
   - /health degradation semantics
   - How to use /health in operational monitoring
   - Requeue does not reset failure count
   - Requeue is not a "second chance"
   - Events not in DLQ cannot be requeued

#### Phase 3: Deployment & Verification
1. Confirm health/DLQ operational judgments were not silently dropped or weakened
2. Confirm cross-reference to `dlq_route.py` and `health_route.py` exists
3. Validate internal Markdown links and cross-references
4. Confirm chapter follows standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」

### Method
- Document restructuring only; no source code changes
- Use grep to verify link integrity before and after editing
- Manual verification of cross-references post-edit
- Explicitly preserve health degraded semantics and requeue failure-count statement during trimming

### Details
- Focus on reducing implementation-derived detail while preserving design intent
- Health degraded semantics is critical — must survive unchanged
- Requeue failure-count non-reset is critical — must survive unchanged
- Ensure navigation remains functional for both human and AI consumers

## Compatibility considerations
- No API changes — documentation-only update
- Internal cross-references must remain valid after restructuring
- Health degraded semantics and requeue failure-count statements must survive unchanged

## Security considerations
- N/A — documentation-only change

## Rollback considerations
- Preserve pre-edit backup of health degraded semantics and requeue sections
- If these statements are accidentally weakened, revert immediately

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Health Degraded Semantics | Manual | Explicitly preserved |
| Requeue Failure Count Non-Reset | Manual | Explicitly preserved |
| Cross-references | Manual | All removed details point to dlq_route.py / health_route.py |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」 |

## Out of scope
- Other eventbus chapters (`docs/06_eventbus_*.md`)
- Source code changes
- Test updates

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-175953_require.md
- Source plan: plans/20260807-205133_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-082351
- Related target files: docs/06_eventbus_02_03_nack-health-dlq.md
