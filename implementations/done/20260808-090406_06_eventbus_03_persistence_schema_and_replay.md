## Goal
- Restructure `docs/06_eventbus_03_persistence_schema_and_replay.md` to remove implementation details like complete DDL text, column lists, index lists, and ALTER TABLE migration details while explicitly preserving SQLite source-of-truth status, JSONL auxiliary archive rationale, WAL justification, shared connection/lock serialization safety judgment.

## Scope
- **In-Scope**: `docs/06_eventbus_03_persistence_schema_and_replay.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other eventbus chapters (`docs/06_eventbus_*.md`), Reference API chapter (`docs/06_eventbus_06_02_reference-api-route-handlers.md`), source code changes, tests

## Assumptions
- `memo-doc-eventbus-review.md` was deleted but issue claims remain valid via independent verification against source code
- SQLite vs JSONL source-of-truth judgment must not be deleted
- Existing internal links and cross-references must remain valid after editing

## Design decisions
- Compress or remove complete DDL text blocks
- Remove column list tables
- Remove complete index lists
- Remove ALTER TABLE migration details
- Remove open_db()/_init_schema() implementation branching explanations
- Preserve: SQLite source-of-truth statement, JSONL auxiliary archive rationale (not query/recovery trust source), WAL usage intent, shared connection + lock serialization safety judgment, replay starts from SQLite, existing DB basic migration policy, brief note on retry_count removal due to lacking meaningful data

## Alternatives considered
- Keeping complete DDL but adding a note pointing to schema.sql as canonical
- Converting DDL to prose descriptions instead of removing it
- Moving detailed schema information to an appendix rather than removing it

## Implementation
### Target file
- `docs/06_eventbus_03_persistence_schema_and_replay.md`

### Procedure
#### Phase 1: Preparation
1. Analyze current document structure to identify where persistence design judgments are distributed
2. Identify all DDL, column list, index list, and ALTER TABLE sections

#### Phase 2: Core Logic Implementation
1. Compress or remove complete DDL text blocks
   - Replace with high-level description of schema purpose
2. Remove column list tables
   - Delete field-by-field type/default-value listings
3. Remove complete index lists
   - Delete exhaustive index definitions
4. Remove ALTER TABLE migration details
   - Delete migration version-by-version change descriptions
5. Remove open_db()/_init_schema() implementation branching explanations
   - Delete conditional branching logic descriptions
6. Preserve design-critical information:
   - SQLite source-of-truth statement
   - JSONL auxiliary archive rationale (not query/recovery trust source)
   - WAL usage intent
   - Shared connection + lock serialization safety judgment
   - Replay starts from SQLite
   - Existing DB basic migration policy
   - Brief note on retry_count removal due to lacking meaningful data

#### Phase 3: Deployment & Verification
1. Confirm SQLite vs JSONL source-of-truth statement was not weakened
2. Confirm cross-reference to schema.sql and db.py exists for all removed details
3. Validate internal Markdown links and cross-references
4. Confirm chapter follows standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」

### Method
- Document restructuring only; no source code changes
- Use grep to verify link integrity before and after editing
- Manual verification of cross-references post-edit
- Explicitly preserve SQLite source-of-truth and WAL justification during trimming

### Details
- Focus on reducing implementation-derived detail while preserving design intent
- SQLite source-of-truth is critical architectural constraint — must survive unchanged
- WAL justification is critical operational decision — must survive unchanged
- Ensure navigation remains functional for both human and AI consumers

## Compatibility considerations
- No API changes — documentation-only update
- Internal cross-references must remain valid after restructuring
- SQLite vs JSONL distinction must survive unchanged

## Security considerations
- N/A — documentation-only change

## Rollback considerations
- Preserve pre-edit backup of SQLite source-of-truth and WAL justification sections
- If these statements are accidentally weakened, revert immediately

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Source-of-truth Statement | Manual | SQLite vs JSONL distinction preserved |
| Cross-references | Manual | All removed details point to schema.sql / db.py |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」 |
| Detail Reduction | Manual | No complete DDL, column lists, index lists, or ALTER TABLE migrations remain |

## Out of scope
- Other eventbus chapters (`docs/06_eventbus_*.md`)
- Reference API chapter (`docs/06_eventbus_06_02_reference-api-route-handlers.md`)
- Source code changes
- Test updates

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-173631_require.md
- Source plan: plans/20260807-203631_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-090406
- Related target files: docs/06_eventbus_03_persistence_schema_and_replay.md
