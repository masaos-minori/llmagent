## Goal
- Restructure `docs/06_eventbus_05_07_validation-status.md` to remove environment-specific details like specific CI output and test counts while explicitly preserving the existence of CI validation, quality gates that should be maintained (linting, type checking, testing), and the reason why health/DLQ regression testing is particularly important due to past DLQ loop issues.

## Scope
- **In-Scope**: `docs/06_eventbus_05_07_validation-status.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other eventbus chapters (`docs/06_eventbus_*.md`), source code changes, tests

## Assumptions
- `memo-doc-eventbus-review.md` was deleted but issue claims remain valid through independent verification against source code
- Health/DLQ regression coverage prioritization rationale must not be deleted
- Existing internal links and cross-references must remain valid after editing

## Design decisions
- Compress or remove exact execution commands (`uv run ruff check scripts/eventbus/`, `uv run mypy scripts/eventbus/`, `uv run pytest tests/test_eventbus*.py`)
- Compress or remove test count ("148 passed")
- Compress or remove last validation date ("2026-07-13")
- Compress or remove detailed FAIL/ERROR counts ("test_health_ok系5件がFAIL、97件がERROR")
- Compress or remove implementation-level fix history notes (_dlq_loop() function name change, etc.)
- Preserve: CI validation existence, quality gates that should be maintained (linting, type checking, testing), past DLQ loop defects, importance of health/DLQ regression testing

## Alternatives considered
- Keeping exact CI output but adding a note pointing to CI pipeline as canonical
- Converting CI status descriptions to prose instead of removing them
- Moving detailed validation specifications to an appendix rather than removing them

## Implementation
### Target file
- `docs/06_eventbus_05_07_validation-status.md`

### Procedure
#### Phase 1: Preparation
1. Analyze current document structure to identify where validation status design judgments are distributed

#### Phase 2: Core Logic Implementation
1. Compress or remove exact execution commands
   - Replace with brief description of validation types
2. Compress or remove test count
   - Delete specific number listings
3. Compress or remove last validation date
   - Delete timestamp information
4. Compress or remove detailed FAIL/ERROR counts
   - Delete failure breakdown numbers
5. Compress or remove implementation-level fix history notes
   - Delete function name change references
6. Preserve design-critical information:
   - CI validation existence
   - Quality gates that should be maintained (linting, type checking, testing)
   - Past DLQ loop defects
   - Importance of health/DLQ regression testing

#### Phase 3: Deployment & Verification
1. Confirm health/DLQ regression coverage prioritization rationale was not silently dropped or weakened
2. Confirm cross-reference to CI pipeline exists
3. Validate internal Markdown links and cross-references
4. Confirm chapter follows standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」

### Method
- Document restructuring only; no source code changes
- Use grep to verify link integrity before and after editing
- Manual verification of cross-references post-edit
- Explicitly preserve health/DLQ regression prioritization statement during trimming

### Details
- Focus on reducing implementation-derived detail while preserving design intent
- Health/DLQ regression prioritization is critical — must survive unchanged
- Quality gate definitions are critical — must survive unchanged
- Ensure navigation remains functional for both human and AI consumers

## Compatibility considerations
- No API changes — documentation-only update
- Internal cross-references must remain valid after restructuring
- Health/DLQ regression and quality gate statements must survive unchanged

## Security considerations
- N/A — documentation-only change

## Rollback considerations
- Preserve pre-edit backup of health/DLQ regression and quality gate sections
- If these statements are accidentally weakened, revert immediately

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Health/DLQ Regression Rationale | Manual | Explicitly preserved |
| Cross-references | Manual | All removed details point to CI pipelines |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」 |

## Out of scope
- Other eventbus chapters (`docs/06_eventbus_*.md`)
- Source code changes
- Test updates

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-175300_require.md
- Source plan: plans/20260807-204826_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-082121
- Related target files: docs/06_eventbus_05_07_validation-status.md
