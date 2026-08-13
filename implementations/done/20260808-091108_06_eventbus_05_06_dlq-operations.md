## Goal
- Restructure `docs/06_eventbus_05_06_dlq-operations.md` to remove implementation details like complete log message quotes and duplicated interval value explanations while explicitly preserving meaning of non-zero sweep count, that requeue does not reset failure count, and immediate DLQ return conditions.

## Scope
- **In-Scope**: `docs/06_eventbus_05_06_dlq-operations.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other eventbus chapters (`docs/06_eventbus_*.md`), Reference API chapter (`docs/06_eventbus_06_02_reference-api-route-handlers.md`), source code changes, tests

## Assumptions
- `memo-doc-eventbus-review.md` was deleted but issue claims remain valid via independent verification against source code
- The note that requeue does not reset failure count and immediate DLQ return condition must not be deleted
- Existing internal links and cross-references must remain valid after editing

## Design decisions
- Compress or remove complete log message quotes ("dlq_loop: swept %d orphan(s) missed by inline promotion")
- Remove repetition of 60-second interval explanation across multiple sections
- Remove mechanical endpoint usage procedures
- Preserve: DLQ file creation meaning, inline promotion vs background sweep role division, what to investigate when non-zero sweep count occurs, requeue does not reset failure count, conditions under which requeued events can immediately return to DLQ, DLQ monitoring requires log analysis

## Alternatives considered
- Keeping complete log messages but adding a note pointing to dlq.py as canonical
- Converting operational procedures to prose descriptions instead of removing them
- Moving detailed DLQ operations to an appendix rather than removing them

## Implementation
### Target file
- `docs/06_eventbus_05_06_dlq-operations.md`

### Procedure
#### Phase 1: Preparation
1. Analyze current document structure to identify where DLQ operations design judgments are distributed
2. Identify all log message quotes, interval repetitions, and endpoint procedures

#### Phase 2: Core Logic Implementation
1. Compress or remove complete log message quotes
   - Replace with high-level description of what the log indicates
2. Remove repetition of 60-second interval explanation across sections
   - Keep single authoritative statement about sweep interval
3. Remove mechanical endpoint usage procedures
   - Delete step-by-step endpoint interaction instructions
4. Preserve operationally critical information:
   - DLQ file creation meaning
   - Inline promotion vs background sweep role division
   - What to investigate when non-zero sweep count occurs
   - Requeue does NOT reset failure count (explicit caveat)
   - Conditions under which requeued events can immediately return to DLQ
   - DLQ monitoring requires log analysis

#### Phase 3: Deployment & Verification
1. Confirm requeue caveat and immediate DLQ return condition were not lost
2. Confirm cross-reference to dlq.py and dlq_route.py exists for all removed details
3. Validate internal Markdown links and cross-references
4. Confirm chapter follows standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」

### Method
- Document restructuring only; no source code changes
- Use grep to verify link integrity before and after editing
- Manual verification of cross-references post-edit
- Explicitly preserve requeue caveat and immediate DLQ return condition during trimming

### Details
- Focus on reducing implementation-derived detail while preserving design intent
- Requeue caveat is critical operational distinction — must survive unchanged
- Immediate DLQ return condition is critical — must survive unchanged
- Ensure navigation remains functional for both human and AI consumers

## Compatibility considerations
- No API changes — documentation-only update
- Internal cross-references must remain valid after restructuring
- Requeue caveat and immediate DLQ return condition must survive unchanged

## Security considerations
- N/A — documentation-only change

## Rollback considerations
- Preserve pre-edit backup of requeue caveat and immediate DLQ return condition sections
- If operational statements are accidentally weakened, revert immediately

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Requeue Caveat | Manual | Explicitly preserved |
| Immediate Re-DLQ Condition | Manual | Explicitly preserved |
| Cross-references | Manual | All removed details point to dlq.py / dlq_route.py |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」 |
| Detail Reduction | Manual | No complete log quotes or interval repetitions remain |

## Out of scope
- Other eventbus chapters (`docs/06_eventbus_*.md`)
- Reference API chapter (`docs/06_eventbus_06_02_reference-api-route-handlers.md`)
- Source code changes
- Test updates

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-174731_require.md
- Source plan: plans/20260807-204731_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-091108
- Related target files: docs/06_eventbus_05_06_dlq-operations.md
