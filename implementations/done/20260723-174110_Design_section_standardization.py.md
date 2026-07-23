## Goal

Improve readability and reduce ambiguity in major design documents by standardizing section structure with Japanese headings for current behavior, design intent, responsibility boundaries, failure behavior, and unresolved items.

## Scope

**In**:
- Apply Japanese section headings (`## 現在の実装挙動`, `## 設計意図`, `## 責務境界`, `## 失敗時の挙動`, `## 未確認事項`) to 9 major design documents where appropriate
- Reorganize existing content under these headings where it improves clarity
- Link unresolved items to the Needs Confirmation inventory

**Out**:
- Rewriting any document from scratch
- Forcing all five sections into every document when irrelevant
- Creating new evidence labels
- Changing technical content meaning

## Assumptions

1. All nine target documents exist at their expected paths.
2. Evidence labels defined in `00_governance_03_evidence-labels.md` are the canonical reference.
3. The Needs Confirmation inventory exists and is accessible.

## Design decisions

- Only apply sections where they materially improve readability; skip irrelevant sections.
- Preserve original content verbatim; only reorganize under new headings.
- Use exact Japanese section headings as specified in the requirement.
- Link unresolved items to the Needs Confirmation inventory using relative links.

## Alternatives considered

- Force all five sections into every document: adds noise to documents that don't need them.
- Create a separate metadata file for section organization: fragments the document unnecessarily.
- Use English section headings: inconsistent with project's Japanese-first convention.

## Implementation

### Target file

9 major design documents: `docs/01_overview-arch-01-process.md`, `docs/01_overview-arch-02-pipelines.md`, `docs/01_overview-arch-03-features.md`, `docs/03_rag_01_system_overview-part1.md`, `docs/03_rag_03_01_query_pipeline-overview.md`, `docs/04_mcp_00_document-guide.md`, `docs/05_agent_00_document-guide.md`, `docs/06_eventbus_00_document-guide.md`, `docs/90_shared_00_document-guide.md`

### Procedure

1. Verify all nine target documents exist at expected paths
2. For each document:
   a. Read the document and assess which of the five section types are relevant
   b. Where relevant, insert the Japanese section heading before the first paragraph that belongs there
   c. Move existing content under the appropriate new heading if it improves clarity
   d. Ensure unresolved items link to the Needs Confirmation inventory

### Method

Insert Japanese section headings where appropriate and reorganize existing content.

### Details

For each document, assess relevance of the five sections:

| Section | When to apply |
|---|---|
| `## 現在の実装挙動` | Document describes implementation details or code behavior |
| `## 設計意図` | Document contains design rationale or architectural decisions |
| `## 責務境界` | Document describes component responsibilities or boundaries |
| `## 失敗時の挙動` | Document describes error handling, failure modes, or recovery |
| `## 未確認事項` | Document has unresolved questions or assumptions |

Example modification for Agent document-guide:

```markdown
# Before:

## Purpose of This Document Set

これらのファイルはLLM Agent REPLシステムを文書化するものである...

---

## Recommended Reading Order (Human)

...

# After:

## 設計意図

### ドキュメントセットの目的

これらのファイルはLLM Agent REPLシステムを文書化するものである...

---

## 現在の実装挙動

### 推奨読書順序（人間向け）

...
```

Link unresolved items example:

```markdown
## 未確認事項

- [NC-001](00_governance_07_needs-confirmation-inventory.md#nc-001): UTF8_PARTIAL_DECODE_ERROR と PREMATURE_EOF の区別
- [NC-004](00_governance_07_needs-confirmation-inventory.md#nc-004): 距離計測のcosine/L2判定不能
```

## Compatibility considerations

None — documentation-only change; no behavioral impact.

## Security considerations

N/A — documentation-only change.

## Rollback considerations

Remove inserted section headings and restore original content placement; no data migration or config changes required.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Markdown rendering | Manual review | Correct rendering |
| Content preservation | Manual review | No content loss |
| Section relevance | Manual review | Only relevant sections applied |

## Out of scope

- Rewriting any document from scratch
- Forcing all five sections into every document when irrelevant
- Creating new evidence labels
- Changing technical content meaning

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260723-165321_plan.md
- Source implementation procedure: N/A
- Generated at: 20260723-174110
- Related target files: Implementation-dependent — major design documents
