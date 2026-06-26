## Goal

Update `03_rag_90_inconsistencies_and_known_issues.md` to capture current RAG documentation inconsistencies and open design questions — including `.txt/.json` drift, RAG/Agent DB boundary confusion, `/db` command name mismatch, and `remote_empty` diagnostics ambiguity.

## Scope

**In-Scope**:
- Add a DOC issue for `.txt/.json` mixed references
- Add a SPEC/DOC issue for RAG vs Agent session table boundary confusion
- Add a DOC issue for `/db` command name mismatch
- Add a SPEC issue for `remote_empty` diagnostics ambiguity
- Separate resolved issues from active issues clearly

**Out-of-Scope**:
- Fixing the underlying runtime behavior directly
- Rewriting all RAG docs

## Assumptions

1. All four inconsistencies identified in this session are valid and should be documented as active issues
2. The existing "Resolved Issues" section format should be preserved
3. A new "Active Issues" section should be added before "Resolved Issues"

## Implementation

### Target file: docs/03_rag_90_inconsistencies_and_known_issues.md

**Procedure**: Add Active Issues section with all four documented issues, separate resolved issues from active issues clearly.

**Method**: Modify the RAG inconsistencies document to add new section and entries.

**Details**:
1. Add Active Issues section before Resolved Issues (after DESIGN-3):
   - Follow same format as Design Notes: Type / Impact / Description / Safe interpretation / Recommended action / Source
2. Document .txt/.json mixed references issue:
   - DOC-01: `.txt`/`.json` mixed references in RAG ingestion docs and code comments (26 stale references across 7 files)
   - Safe interpretation: runtime code already uses `.json`; only docstrings/CLI help/docs need fixing
3. Document RAG vs Agent session table boundary confusion:
   - SPEC-01: RAG data model includes Agent-owned `sessions` and `messages` tables
   - Safe interpretation: RAG layer does not own Agent conversation history; sessions/messages belong to Agent REPL
4. Document /db command name mismatch:
   - DOC-02: `/db fts-rebuild` vs `/db rebuild-fts` — canonical is `/db rebuild-fts`
   - Safe interpretation: use `/db rebuild-fts`; only one stale reference in RAG ops docs
5. Document remote_empty diagnostics ambiguity:
   - SPEC-02: `status=success` with `fallback_reason="http_remote_empty"` is semantically confusing
   - Safe interpretation: `remote_empty` (HTTP 200 with no context) is a success case, not a fallback

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| 03_rag_90_inconsistencies_and_known_issues.md | Verify Active Issues section added with all four issues | Check document structure | Active Issues section present with DOC-01, SPEC-01, DOC-02, SPEC-02 |
| 03_rag_90_inconsistencies_and_known_issues.md | Verify resolved issues remain clearly separated | Check document structure | Resolved Issues section unchanged below Active Issues |

## Risks

- **Risk**: Adding too many active issues may overwhelm the known-issues document | **Likelihood**: Low (only 4 issues, all confirmed) | **Mitigation**: Keep issue descriptions concise; link to plan files for detailed resolution tracking | False
