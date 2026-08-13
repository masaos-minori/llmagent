## Goal
- Restructure `docs/06_eventbus_05_03_health-endpoint-semantics.md` to remove implementation details like complete JSON body examples and mechanical status value tables while explicitly preserving why HTTP status is used as primary monitoring signal, ok/degraded meaning, and that 503 indicates degradation not process-down.

## Scope
- **In-Scope**: `docs/06_eventbus_05_03_health-endpoint-semantics.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other eventbus chapters (`docs/06_eventbus_*.md`), Reference API chapter (`docs/06_eventbus_06_02_reference-api-route-handlers.md`), source code changes, tests

## Assumptions
- `memo-doc-eventbus-review.md` was deleted but issue claims remain valid via independent verification against source code
- The clarification "503 is degradation, not down" must not be deleted
- Existing internal links and cross-references must remain valid after editing

## Design decisions
- Compress or remove complete JSON body examples
- Remove mechanical status value table (e.g., `| HTTP Status | Status Value | Meaning |`)
- Remove internal degraded_reasons key enumeration
- Preserve: /health monitoring policy, ok and degraded meaning, HTTP 503 indicates degradation state not process-down, monitoring tools should treat HTTP status as primary signal, representative degradation causes to check (DB unavailable, DLQ task stopped, queue backlog, slow consumer)

## Alternatives considered
- Keeping complete JSON body examples but adding a note pointing to health_route.py as canonical
- Converting status value table to prose descriptions instead of removing it
- Moving detailed endpoint semantics to an appendix rather than removing them

## Implementation
### Target file
- `docs/06_eventbus_05_03_health-endpoint-semantics.md`

### Procedure
#### Phase 1: Preparation
1. Analyze current document structure to identify where health endpoint design judgments are distributed
2. Identify all JSON body examples, status value tables, and degraded_reasons sections

#### Phase 2: Core Logic Implementation
1. Compress or remove complete JSON body examples
   - Replace with high-level description of response shape
2. Remove mechanical status value table
   - Delete exhaustive HTTP status + value + meaning mapping
3. Remove internal degraded_reasons key enumeration
   - Delete list of internal reason keys
4. Preserve monitoring-critical information:
   - /health monitoring policy
   - ok and degraded meaning
   - HTTP 503 indicates degradation state NOT process-down (explicit clarification)
   - Monitoring tools should use HTTP status as primary signal
   - Representative degradation causes to check: DB unavailable, DLQ task stopped, queue backlog, slow consumer

#### Phase 3: Deployment & Verification
1. Confirm "503 is degradation not down" clarification was not lost
2. Confirm cross-reference to health_route.py exists for all removed details
3. Validate internal Markdown links and cross-references
4. Confirm chapter follows standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」

### Method
- Document restructuring only; no source code changes
- Use grep to verify link integrity before and after editing
- Manual verification of cross-references post-edit
- Explicitly preserve 503 degradation clarification during trimming

### Details
- Focus on reducing implementation-derived detail while preserving design intent
- "503 is degradation not down" is critical operational distinction — must survive unchanged
- Monitoring signal interpretation is critical — must survive unchanged
- Ensure navigation remains functional for both human and AI consumers

## Compatibility considerations
- No API changes — documentation-only update
- Internal cross-references must remain valid after restructuring
- 503 degradation clarification must survive unchanged

## Security considerations
- N/A — documentation-only change

## Rollback considerations
- Preserve pre-edit backup of 503 degradation clarification section
- If monitoring-related statements are accidentally weakened, revert immediately

## Validation plan
| Check | Tool | Target |
|---|---|---|
| 503 Clarification | Manual | Explicitly preserved |
| Cross-references | Manual | All removed details point to health_route.py |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」 |
| Detail Reduction | Manual | No complete JSON body examples or mechanical status tables remain |

## Out of scope
- Other eventbus chapters (`docs/06_eventbus_*.md`)
- Reference API chapter (`docs/06_eventbus_06_02_reference-api-route-handlers.md`)
- Source code changes
- Test updates

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-174054_require.md
- Source plan: plans/20260807-204054_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-090822
- Related target files: docs/06_eventbus_05_03_health-endpoint-semantics.md
