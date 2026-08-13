## Goal
- Restructure `docs/06_eventbus_02_04_dlq-background-loop.md` to remove implementation details like SELECT/UPDATE condition details and function name explanations while explicitly preserving why the background loop is a safety net, what it detects, and why optimistic locking prevents double promotion.

## Scope
- **In-Scope**: `docs/06_eventbus_02_04_dlq-background-loop.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other eventbus chapters (`docs/06_eventbus_*.md`), source code changes, tests

## Assumptions
- `memo-doc-eventbus-review.md` was deleted but issue claims remain valid through independent verification against source code
- Background loop as safety net nature and optimistic locking explanation must not be deleted
- Existing internal links and cross-references must remain valid after editing

## Design decisions
- Compress or remove SELECT/UPDATE condition details
- Compress or remove `sweep_orphans()` function name explanation
- Compress or remove detailed call site description of `promote_to_dlq()`
- Compress or remove complete log message quotes
- Compress or remove verbose explanation of dual-pass implementation
- Preserve: DLQ background loop is a safety net (not primary path), purpose is detecting missed inline promotions and race conditions, optimistic locking prevents double promotion, operational meaning of non-zero sweep count, monitoring via logs is required

## Alternatives considered
- Keeping exact SQL conditions but adding a note pointing to dlq.py as canonical
- Converting function descriptions to prose instead of removing them
- Moving detailed validation specifications to an appendix rather than removing them

## Implementation
### Target file
- `docs/06_eventbus_02_04_dlq-background-loop.md`

### Procedure
#### Phase 1: Preparation
1. Analyze current document structure to identify where DLQ background loop design judgments are distributed

#### Phase 2: Core Logic Implementation
1. Compress or remove SELECT/UPDATE condition details
   - Replace with brief description of detection criteria
2. Compress or remove `sweep_orphans()` function name explanation
   - Delete function-level naming rationale
3. Compress or remove detailed call site description of `promote_to_dlq()`
   - Delete invocation chain details
4. Compress or remove complete log message quotes
   - Delete literal string examples
5. Compress or remove verbose explanation of dual-pass implementation
   - Delete step-by-step flow description
6. Preserve design-critical information:
   - DLQ background loop is a safety net (not primary path)
   - Purpose is detecting missed inline promotions and race conditions
   - Optimistic locking prevents double promotion
   - Operational meaning of non-zero sweep count
   - Monitoring via logs is required

#### Phase 3: Deployment & Verification
1. Confirm move `promote_to_dlq()` production-path-not-called note to Known Issues or Reference API chapter
2. Coordinate with Known Issues cleanup issue so `promote_to_dlq()` note does not duplicate across both locations
3. Confirm cross-reference to `dlq.py` and `app.py` exists
4. Validate internal Markdown links and cross-references
5. Confirm chapter follows standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」

### Method
- Document restructuring only; no source code changes
- Use grep to verify link integrity before and after editing
- Manual verification of cross-references post-edit
- Explicitly preserve safety net rationale and optimistic locking statement during trimming

### Details
- Focus on reducing implementation-derived detail while preserving design intent
- Safety net rationale is critical — must survive unchanged
- Optimistic locking explanation is critical — must survive unchanged
- Ensure navigation remains functional for both human and AI consumers

## Compatibility considerations
- No API changes — documentation-only update
- Internal cross-references must remain valid after restructuring
- Safety net rationale and optimistic locking statements must survive unchanged

## Security considerations
- N/A — documentation-only change

## Rollback considerations
- Preserve pre-edit backup of safety net rationale and optimistic locking sections
- If these statements are accidentally weakened, revert immediately

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Safety Net Rationale | Manual | Explicitly preserved |
| Optimistic Locking Explanation | Manual | Explicitly preserved |
| Cross-references | Manual | All removed details point to dlq.py / app.py |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」 |

## Out of scope
- Other eventbus chapters (`docs/06_eventbus_*.md`)
- Source code changes
- Test updates

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-175657_require.md
- Source plan: plans/20260807-205032_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-082236
- Related target files: docs/06_eventbus_02_04_dlq-background-loop.md
