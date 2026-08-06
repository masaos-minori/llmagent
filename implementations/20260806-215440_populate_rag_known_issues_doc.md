## Goal

Consolidate all currently open confirmed RAG domain errors and questions into `docs/03_rag_90_inconsistencies_and_known_issues.md` using the standardized 17-field template.

## Scope

- **In-Scope**:
    - Auditing the list of candidate issues provided in `requires/20260802-184051_require.md`.
    - Verifying each candidate against its sibling issue/requirement or current source code.
    - Updating `docs/03_rag_90_inconsistencies_and_known_issues.md` with validated open issues.
    - Adding a migration/history note to `docs/03_rag_90_inconsistencies_and_known_issues.md` regarding previous entry pruning.
- **Out-of-Scope**:
    - Fixing any underlying software bugs or documentation errors.
    - Creating new requirement documents for items already marked as resolved in `issues/done/`.

## Assumptions

1. The current highest `RAG-XXX` ID can be determined by inspecting existing `docs/03_rag_90*.md` files.
2. Items in `issues/done/` are considered resolved unless direct code inspection proves otherwise.
3. The project's convention of omitting fully-resolved entries from Known Issues files remains active.

## Design decisions

- Treat additions as insert-only — do not modify existing text outside the target section.
- Use grep-based verification rather than Markdown AST parsing since we only need string-level comparison.

## Alternatives considered

- Rewrite the entire known issues doc: rejected because scope is limited to populating with verified issues.
- Create a separate document for each issue: rejected because scope is limited to consolidating into this doc.

## Compatibility considerations

- Added sentences must use existing Japanese terminology conventions.
- Cross-references must use existing Markdown conventions within the document.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If added sentences cause formatting issues, revert to git history before edit.

## Implementation

### Phase 1: Audit & Verification

#### Procedure

1. Read `docs/03_rag_90_inconsistencies_and_known_issues.md` to identify the next available `RAG-` ID.
2. For each candidate in the requirement:
   - Locate corresponding sibling in `issues/`, `issues/done/`, or `requires/`.
   - If sibling is in `issues/done/`, verify via code/docs if it's truly resolved.
   - If sibling is in `issues/` or `requires/`, confirm it represents a genuine open issue.
   - Perform direct re-verification for items without clear siblings (e.g., `delete_existing_document()` naming).

#### Method

Manual verification + tool execution.

#### Details

```bash
# Find the next available RAG- ID
grep -oP 'RAG-\d+' docs/03_rag_90_inconsistencies_and_known_issues.md | sort -t'-' -k2 -n | tail -1

# List candidates from requires doc
grep -n "^- \[x\]" requires/20260802-184051_require.md

# Check for sibling issues
ls -la issues/ | grep -E "rag_|RAG-"

# Check for resolved issues
ls -la issues/done/ | grep -E "rag_|RAG-"

# Verify delete_existing_document() naming
grep -rn "delete_existing_document\|delete.*document" scripts/agent/services/document_manager.py
```

### Phase 2: Documentation Update

#### Procedure

1. Open `docs/03_rag_90_inconsistencies_and_known_issues.md`.
2. Append the required migration/history note explaining the `RAG-001`/`RAG-002` removal and the purpose of this population pass.
3. Add new entries for all verified open issues using the 17-field template from `docs/00_governance_04_known-issues-template.md`.
4. Link each entry to its relevant sibling issue/requirement path in the `Related` field.

#### Method

Direct file edit using sed or manual editing.

#### Details

```bash
# Find the template location
ls -la docs/00_governance_04_known-issues-template.md

# Read the template
cat docs/00_governance_04_known-issues-template.md
```

Insertion pattern:
- After the existing content in `docs/03_rag_90_inconsistencies_and_known_issues.md`, append:
  ```markdown
  ## Migration Note
  
  This document was populated on YYYY-MM-DD based on the audit of requirements. Previous entries (`RAG-001`, `RAG-002`) were removed as they were resolved. All remaining entries represent verified open issues.
  
  ---
  
  ### Verified Open Issues
  
  [Entry 1 following the 17-field template]
  [Entry 2 following the 17-field template]
  ...
  ```

### Phase 3: Cleanup

#### Procedure

1. Move `requires/20260802-184051_require.md` to `requires/done/`.

#### Method

File move operation.

#### Details

```bash
mv /home/sugimoto/llmagent/requires/20260802-184051_require.md /home/sugimoto/llmagent/requires/done/
```

### Target file

Verification

#### Procedure

1. Manually verify the reorganized structure and content accuracy.
2. Confirm that the "実装意図 (Implementation note)" section still aligns with the new layout.
3. Run lint check on modified file.

#### Method

Manual verification + tool execution.

#### Details

```bash
# Verify migration note present
grep -c "Migration.*Note\|移行.*ノート" docs/03_rag_90_inconsistencies_and_known_issues.md

# Verify new entries present
grep -c "RAG-\d+" docs/03_rag_90_inconsistencies_and_known_issues.md

# Verify template compliance
grep -c "ID\|Status\|Priority\|Severity\|Summary\|Description\|Root Cause\|Impact\|Workaround\|Resolution\|Evidence\|Siblings\|Related\|Created\|Updated\|Reporter\|Assignee\|Tags" docs/03_rag_90_inconsistencies_and_known_issues.md

# Verify requires doc moved
ls -la requires/done/ | grep 20260802-184051

# Run lint check
ruff check docs/03_rag_90_inconsistencies_and_known_issues.md

# Run format check
ruff format docs/03_rag_90_inconsistencies_and_known_issues.md
```

Expected outcomes:
- Migration note appended to known issues doc
- New entries added for all verified open issues
- All entries follow the 17-field template
- All entries have valid `Related` field references
- Requires doc moved to done directory
- Zero lint errors on the file
- Consistent formatting

## Validation plan

| Check | Tool | Target | Expected Outcome |
|---|---|---|---|
| Lint | `ruff check docs/` | Docs files | 0 errors |
| Format | `ruff format docs/` | Consistent formatting | Consistent formatting |
| Content | Manual Review | Verify all entries match current codebase state and follow template | All entries accurate |
| Traceability | Manual Review | Ensure all `Related` fields point to valid files | All links valid |

## Out of scope

- Modifications to `scripts/rag/pipeline.py`, `scripts/mcp_servers/rag_pipeline/`.
- Modifications to any other documentation files.
- Creating new documentation files.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-184051_require.md
- Source plan: plans/20260805-140129_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-215440
- Related target files: docs/03_rag_90_inconsistencies_and_known_issues.md
