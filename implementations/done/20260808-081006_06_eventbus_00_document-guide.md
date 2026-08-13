## Goal
- Restructure `docs/06_eventbus_00_document-guide.md` into a navigation-only chapter, removing content mechanically derivable from code (HTTP parameter tables, response field lists, DDL, function signatures).

## Scope
- **In-Scope**: `docs/06_eventbus_00_document-guide.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other eventbus chapters (`docs/06_eventbus_*.md`), source code changes, tests

## Assumptions
- `memo-doc-eventbus-review.md` exists and its guidance is valid (independently verified)
- Enterprise navigation purpose should be maintained; not a record of design or operational judgments
- Existing internal links and cross-references must remain valid after editing

## Design decisions
- Compress or remove exhaustive file indexes that duplicate what readers can derive from directory listings
- Simplify AI query routing tables to high-level patterns rather than exhaustive endpoint mappings
- Remove keyword enumeration that duplicates search-index functionality
- Remove mechanical per-file content descriptions that read like auto-generated summaries
- Preserve: docset role, high-level guide, Canonical Source Rule, known issues/deferred items handling, Reference API separation note

## Alternatives considered
- Keeping full file index but adding a note pointing to directory listing as canonical
- Converting routing table to prose descriptions instead of tabular format
- Moving detailed content descriptions to an appendix rather than removing them

## Implementation
### Target file
- `docs/06_eventbus_00_document-guide.md`

### Procedure
#### Phase 1: Preparation
1. Read `memo-doc-eventbus-review.md` §「06_eventbus_00_document-guide」keep/remove guidance
2. Analyze current document structure to identify navigation-functioning sections

#### Phase 2: Core Logic Implementation
1. Compress or remove excessive file index
   - Replace with brief summary of docset organization
2. Simplify AI query routing table
   - Reduce to high-level routing patterns (e.g., "search → RAG docs", "config → shared config")
3. Remove keyword enumeration
   - Delete keyword list sections that duplicate search functionality
4. Remove mechanical per-file content descriptions
   - Delete auto-generated-style file-by-file content summaries
5. Keep navigation-critical information:
   - Docset role and purpose
   - High-level navigation guide
   - Canonical Source Rule statement
   - Known issues/deferred items handling approach
   - Reference API separation note

#### Phase 3: Deployment & Verification
1. Validate internal Markdown links and cross-references
2. Confirm chapter follows standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」

### Method
- Document restructuring only; no source code changes
- Use grep to verify link integrity before and after editing
- Manual verification of cross-references post-edit

### Details
- Focus on reducing implementation-derived detail while preserving design intent
- Ensure navigation remains functional for both human and AI consumers
- Maintain Canonical Source Rule as architectural constraint

## Compatibility considerations
- No API changes — documentation-only update
- Internal cross-references must remain valid after restructuring
- Navigation functionality must be preserved for enterprise use cases

## Security considerations
- N/A — documentation-only change

## Rollback considerations
- Preserve pre-edit backup of critical navigation sections
- If navigation breaks, revert to previous structure temporarily while fixing

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」 |
| Navigation Functionality | Manual | Navigation remains usable |
| Detail Reduction | Manual | No exhaustive file index, routing table, keyword list, or per-file descriptions remain |

## Out of scope
- Other eventbus chapters (`docs/06_eventbus_*.md`)
- Source code changes
- Test updates

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-172511_require.md
- Source plan: plans/20260807-203315_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-081006
- Related target files: docs/06_eventbus_00_document-guide.md
