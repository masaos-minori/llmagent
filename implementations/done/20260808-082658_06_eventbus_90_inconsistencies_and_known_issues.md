## Goal
- Restructure `docs/06_eventbus_90_inconsistencies_and_known_issues.md` to remove implementation details like complete 17-field issue templates and unverified metadata fields while explicitly preserving each known issue's meaning, why it's a problem, operational notes, and fix decision criteria.

## Scope
- **In-Scope**: `docs/06_eventbus_90_inconsistencies_and_known_issues.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other eventbus chapters (`docs/06_eventbus_*.md`), source code changes, tests

## Assumptions
- `memo-doc-eventbus-review.md` was deleted but issue claims remain valid through independent verification against source code
- Agent integration unimplemented and ack-offset non-monotonicity operational impact must not be deleted
- Existing internal links and cross-references must remain valid after editing

## Design decisions
- Compress or remove complete 17-field issue template
- Compress or remove unverified metadata fields (Owner / First Found / Target / Related)
- Compress or remove Statement A/B style migration memo
- Compress or remove detailed implementation file/test names
- Compress or remove schema-vs-implementation difference table
- Preserve: each known issue's meaning, why it's a problem, operational notes, fix decision criteria
- Preserve: rationale for each deferred item, operational impact of agent integration being unimplemented, operational impact of ack-offset non-monotonicity not being guaranteed

## Alternatives considered
- Keeping complete issue template but adding a note pointing to Known Issues chapter as canonical
- Converting issue descriptions to prose instead of removing them
- Moving detailed validation specifications to an appendix rather than removing them

## Implementation
### Target file
- `docs/06_eventbus_90_inconsistencies_and_known_issues.md`

### Procedure
#### Phase 1: Preparation
1. Analyze current document structure to identify where known issue design judgments are distributed

#### Phase 2: Core Logic Implementation
1. Compress or remove complete 17-field issue template
   - Replace with brief description of expected payload shape
2. Compress or remove unverified metadata fields
   - Delete Owner / First Found / Target / Related field listings
3. Compress or remove Statement A/B style migration memo
   - Delete migration rationale text
4. Compress or remove detailed implementation file/test names
   - Delete specific filename references
5. Compress or remove schema-vs-implementation difference table
   - Delete exhaustive difference mappings
6. Preserve design-critical information:
   - Each known issue's meaning
   - Why each is a problem
   - Operational notes for each
   - Fix decision criteria for each
   - Rationale for each deferred item
   - Operational impact of agent integration being unimplemented
   - Operational impact of ack-offset non-monotonicity not being guaranteed

#### Phase 3: Deployment & Verification
1. Validate each entry against current code per `rules/coding.md` §「Documentation notes — "Current behavior" classification」
2. Classify all entries using five-way classification: Accept current specification / Implementation fix required / Documentation fix required / Issue already tracked / Obsolete and removable
3. Note that `promote_to_dlq()` production-path-not-called annotation can be kept concise as implementation detail
4. If new "Implementation fix required" item discovered, submit as separate issue without implementing fix
5. Validate internal Markdown links and cross-references
6. Confirm chapter follows standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」

### Method
- Document restructuring only; no source code changes
- Use grep to verify link integrity before and after editing
- Manual verification of cross-references post-edit
- Explicitly preserve operational meanings and fix decision criteria during trimming

### Details
- Focus on reducing implementation-derived detail while preserving design intent
- Operational meanings are critical — must survive unchanged
- Fix decision criteria are critical — must survive unchanged
- Ensure navigation remains functional for both human and AI consumers

## Compatibility considerations
- No API changes — documentation-only update
- Internal cross-references must remain valid after restructuring
- Operational meanings and fix decision criteria must survive unchanged

## Security considerations
- N/A — documentation-only change

## Rollback considerations
- Preserve pre-edit backup of operational meanings and fix decision criteria sections
- If these statements are accidentally weakened, revert immediately

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Operational Meaning | Manual | Explicitly preserved |
| Agent Integration Impact | Manual | Explicitly preserved |
| Ack Offset Non-Monotonicity Impact | Manual | Explicitly preserved |
| Five-Way Classification | Manual | All entries classified |
| Cross-references | Manual | All removed details point to appropriate sources |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」 |

## Out of scope
- Other eventbus chapters (`docs/06_eventbus_*.md`)
- Source code changes
- Test updates

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-180449_require.md
- Source plan: plans/20260807-205338_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-082658
- Related target files: docs/06_eventbus_90_inconsistencies_and_known_issues.md
