## Goal
- Restructure `docs/90_shared_00_document-guide.md` to remove overly detailed file indexes and AI query routing tables while explicitly preserving the navigation purpose, high-level chapter guidance, canonical source rule, known issues handling, and subset of safe-AI-usage guidance relevant to operational/design judgments.

## Scope
- **In-Scope**: `docs/90_shared_00_document-guide.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other shared/db chapters (`docs/90_shared_*.md`), source code changes, tests

## Assumptions
- `memo-doc-shared-review.md` is valid and this chapter should remain as a navigation guide
- LLMMessage field count has changed to 11 fields in current `scripts/shared/types.py`
- Existing internal links and cross-references must remain valid after editing

## Design decisions
- Compress or remove overly detailed file index (lines 68-117)
- Compress or remove overly granular AI query routing table (e.g., `...core-types.md §3-4 / ...reference.md(02) §10`)
- Compress or remove keyword enumeration outside YAML frontmatter tags (lines 150-158)
- Compress or remove mechanical full file name list
- Compress or remove overlapping safety memo near implementation details
- Preserve: shared/db doc set purpose, high-level chapter navigation, canonical source rule, how to handle known issues, subset of safe-AI-usage guidance relevant to operational/design judgments

## Alternatives considered
- Keeping complete file index but adding a note pointing to scripts/shared/ as canonical
- Converting edge case descriptions to prose instead of removing them
- Moving detailed validation specifications to an appendix rather than removing them

## Implementation
### Target file
- `docs/90_shared_00_document-guide.md`

### Procedure
#### Phase 1: Preparation
1. Analyze current document structure to identify where navigation guide design judgments are distributed

#### Phase 2: Core Logic Implementation
1. Compress or remove overly detailed file index
   - Replace with brief description of expected payload shape
2. Compress or remove overly granular AI query routing table
   - Delete exhaustive routing mappings
3. Compress or remove keyword enumeration outside YAML frontmatter tags
   - Delete keyword listings
4. Compress or remove mechanical full file name list
   - Delete specific filename references
5. Compress or remove overlapping safety memo near implementation details
   - Delete redundant safety text
6. Preserve design-critical information:
   - Shared/db doc set purpose
   - High-level chapter navigation
   - Canonical source rule
   - How to handle known issues
   - Subset of safe-AI-usage guidance relevant to operational/design judgments

#### Phase 3: Deployment & Verification
1. Confirm this chapter is not used as a substitute for design body
2. Confirm cross-reference to `scripts/shared/` and `scripts/db/` exists
3. Validate internal Markdown links and cross-references
4. Confirm chapter follows standard template from `memo-doc-shared-review.md` §「修正後の章構成テンプレート」

### Method
- Document restructuring only; no source code changes
- Use grep to verify link integrity before and after editing
- Manual verification of cross-references post-edit
- Explicitly preserve navigation purpose and canonical source rule during trimming

### Details
- Focus on reducing implementation-derived detail while preserving design intent
- Navigation purpose is critical — must survive unchanged
- Canonical source rule is critical — must survive unchanged
- Ensure navigation remains functional for both human and AI consumers

## Compatibility considerations
- No API changes — documentation-only update
- Internal cross-references must remain valid after restructuring
- Navigation purpose and canonical source rule must survive unchanged

## Security considerations
- N/A — documentation-only change

## Rollback considerations
- Preserve pre-edit backup of navigation purpose and canonical source rule sections
- If these statements are accidentally weakened, revert immediately

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Navigation Purpose | Manual | Explicitly preserved |
| Canonical Source Rule | Manual | Explicitly preserved |
| Cross-references | Manual | All removed details point to scripts/shared/ / scripts/db/ |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |

## Out of scope
- Other shared/db chapters (`docs/90_shared_*.md`)
- Source code changes
- Test updates

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260807-181210_require.md
- Source plan: plans/20260807-205926_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-083133
- Related target files: docs/90_shared_00_document-guide.md
