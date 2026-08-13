## Goal
- Restructure `docs/06_eventbus_05_05_delivery-operations.md` to remove environment-specific details like curl command examples and jq command examples while explicitly preserving live delivery verification purpose, operational actions after slow consumer detection, and reconnection guidance with stable consumer_id.

## Scope
- **In-Scope**: `docs/06_eventbus_05_05_delivery-operations.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other eventbus chapters (`docs/06_eventbus_*.md`), Reference API chapter (`docs/06_eventbus_06_02_reference-api-route-handlers.md`), source code changes, tests

## Assumptions
- `memo-doc-eventbus-review.md` was deleted but issue claims remain valid via independent verification against source code
- Slow consumer operational response and SQLite persistence fact must not be deleted
- Existing internal links and cross-references must remain valid after editing

## Design decisions
- Compress or remove detailed curl command examples
- Compress or remove jq command examples
- Remove localhost millisecond-level timing estimates ("typically under 1ms latency on localhost")
- Remove enumeration of simple verification commands
- Preserve: live delivery verification purpose, operational actions after slow consumer detection, recovery by replaying queue drop, reconnection with stable consumer_id, fact that events persist to SQLite even with zero subscribers

## Alternatives considered
- Keeping curl/jq examples but adding a note pointing to direct experimentation as canonical
- Converting command examples to prose descriptions instead of removing them
- Moving detailed operational procedures to an appendix rather than removing them

## Implementation
### Target file
- `docs/06_eventbus_05_05_delivery-operations.md`

### Procedure
#### Phase 1: Preparation
1. Analyze current document structure to identify where delivery operations design judgments are distributed
2. Identify all curl/jq command examples and timing estimate sections

#### Phase 2: Core Logic Implementation
1. Compress or remove detailed curl command examples
   - Replace with high-level description of what the command verifies
2. Compress or remove jq command examples
   - Delete specific field extraction patterns
3. Remove localhost millisecond-level timing estimates
   - Delete "under 1ms latency on localhost" type specifications
4. Remove enumeration of simple verification commands
   - Delete list of ad-hoc verification approaches
5. Preserve operationally critical information:
   - Live delivery verification purpose
   - Operational actions after slow consumer detection
   - Recovery by replaying queue drop
   - Reconnection with stable consumer_id
   - Fact that events persist to SQLite even with zero subscribers

#### Phase 3: Deployment & Verification
1. Confirm slow consumer operational response and SQLite persistence fact were not lost
2. Confirm cross-reference to direct experimentation exists
3. Validate internal Markdown links and cross-references
4. Confirm chapter follows standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」

### Method
- Document restructuring only; no source code changes
- Use grep to verify link integrity before and after editing
- Manual verification of cross-references post-edit
- Explicitly preserve slow consumer operational response during trimming

### Details
- Focus on reducing implementation-derived detail while preserving design intent
- Slow consumer operational response is critical — must survive unchanged
- SQLite persistence fact is critical — must survive unchanged
- Ensure navigation remains functional for both human and AI consumers

## Compatibility considerations
- No API changes — documentation-only update
- Internal cross-references must remain valid after restructuring
- Slow consumer operational response and SQLite persistence fact must survive unchanged

## Security considerations
- N/A — documentation-only change

## Rollback considerations
- Preserve pre-edit backup of slow consumer operational response and SQLite persistence sections
- If operational statements are accidentally weakened, revert immediately

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Slow Consumer Response | Manual | Explicitly preserved |
| SQLite Persists Fact | Manual | Explicitly preserved |
| Cross-references | Manual | All removed details point to direct experimentation |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」 |
| Detail Reduction | Manual | No curl/jq command examples or timing estimates remain |

## Out of scope
- Other eventbus chapters (`docs/06_eventbus_*.md`)
- Reference API chapter (`docs/06_eventbus_06_02_reference-api-route-handlers.md`)
- Source code changes
- Test updates

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-174638_require.md
- Source plan: plans/20260807-204638_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-090945
- Related target files: docs/06_eventbus_05_05_delivery-operations.md
