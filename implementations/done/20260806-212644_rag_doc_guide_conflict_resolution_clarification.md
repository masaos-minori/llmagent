## Goal

Add explicit trigger conditions, link to the Canonical Source Rule, and require recording the detection date in the conflict resolution section of `docs/03_rag_00_document-guide.md`.

## Scope

- **In-Scope**: Modifying `docs/03_rag_00_document-guide.md` to add clarifying sentences to the "コンフリクト解決" paragraph.
- **Out-of-Scope**: Modifying `docs/03_rag_90_inconsistencies_and_known_issues.md`, changing the actual conflict resolution logic, or restructuring the documentation.

## Assumptions

1. The new information must be added in Japanese to maintain consistency with the document.
2. The term "Canonical Source Rule" refers to the table in lines 58-65 of `docs/03_rag_00_document-guide.md`.

## Design decisions

- Treat additions as insert-only — do not modify existing text outside the target paragraph.
- Use grep-based verification rather than Markdown AST parsing since we only need string-level comparison.

## Alternatives considered

- Rewrite the entire conflict resolution section: rejected because scope is limited to adding clarifications.
- Create a separate document for conflict rules: rejected because scope is limited to this doc.

## Compatibility considerations

- Added sentences must use existing Japanese terminology conventions.
- Cross-references must use existing Markdown conventions within the document.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If added sentences cause formatting issues, revert to git history before edit.

## Implementation

### Target file

`docs/03_rag_00_document-guide.md`

### Procedure

1. Locate the "コンフリクト解決" paragraph in the document.
2. Identify insertion points for:
   - Explicit trigger conditions for when conflict resolution applies.
   - Link to the Canonical Source Rule table (lines 58-65).
   - Requirement to record the detection date when conflicts are found.
3. Insert clarifying sentences into the paragraph.

### Method

Direct file edit using sed or manual editing.

### Details

```bash
# Find the conflict resolution section
grep -n "コンフリクト解決\|Conflict.*Resolution" docs/03_rag_00_document-guide.md

# Verify Canonical Source Rule table location
sed -n '58,65p' docs/03_rag_00_document-guide.md
```

Insertion pattern:
- After existing conflict resolution description, add:
  - Trigger condition sentence (e.g., "このルールは、同一リソースに対する複数ドキュメントの差分が検出された場合に適用されます。")
  - Canonical Source Rule reference (e.g., "[See Canonical Source Rule](#canonical-source-rule)")
  - Detection date requirement (e.g., "コンフリクト検出日は記録する必要があります。")

### Target file

Verification

### Procedure

1. Manually verify the addition using `grep` to ensure trigger condition, canonical source link, and detection date requirement are present.
2. Run lint check on the modified file.

### Method

Manual verification + tool execution.

### Details

```bash
# Verify trigger condition added
grep -c "trigger\|トリガー\|条件" docs/03_rag_00_document-guide.md

# Verify canonical source link added
grep -c "Canonical.*Source\|canonical.*source" docs/03_rag_00_document-guide.md

# Verify detection date requirement added
grep -c "detection.*date\|検出.*日\|日付" docs/03_rag_00_document-guide.md

# Run lint check
ruff check docs/03_rag_00_document-guide.md
```

Expected outcomes:
- All three elements (trigger, canonical source link, detection date) present in the conflict resolution paragraph
- Zero lint errors on the file

## Validation plan

| Check | Tool | Target | Expected Outcome |
|---|---|---|---|
| Lint | `ruff check docs/03_rag_00_document-guide.md` | Docs file | 0 errors |
| Manual | `grep` | Paragraph content | Trigger, Canonical Source, and Date requirements found |

## Out of scope

- Modifications to `docs/03_rag_90_inconsistencies_and_known_issues.md`.
- Changes to the actual conflict resolution logic.
- Restructuring of the documentation.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260802-174715_require.md
- Source plan: plans/20260805-122800_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-212644
- Related target files: docs/03_rag_00_document-guide.md
