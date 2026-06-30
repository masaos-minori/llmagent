## Goal
- Confirm RAG documentation inconsistencies catalog (`docs/03_rag_90_inconsistencies_and_known_issues.md`) is accurate — no need to add 4 new "Active Issues" since the proposed issues are either already resolved or not real inconsistencies.

## Scope
- **In-Scope**:
  - Verify DOC-1 (.txt/.json mix): already resolved as ARTIFACT-01
  - Verify DOC-2 (RAG/Agent DB boundary): already documented at L89-L93 of data model doc
  - Verify DOC-3 (/db command naming): already verified consistent across all docs
  - Verify SPEC-4 (remote_empty semantics): already verified correct across all channels
  - Confirm no additional inconsistencies need to be added
- **Out-of-Scope**:
  - Root cause code fixes (handled by separate plans)
  - DESIGN-2/DESIGN-3 body changes

## Findings

### DOC-1: .txt/.json artifact drift — Already resolved
ARTIFACT-01 in `docs/03_rag_90_inconsistencies_and_known_issues.md:L43-L46` documents this resolution. No active `.txt` artifact references remain in the codebase (confirmed by plan 204658).

### DOC-2: RAG DB / Agent DB session table boundary — Not an inconsistency
`docs/03_rag_04_data_model_and_interfaces.md:L89-L93` explicitly states:
```
**RAG-owned tables:** `documents`, `chunks`, `chunks_fts`, `chunks_vec` — all in `rag.sqlite`.

Agent session tables (`sessions`, `messages`, `tool_results`, `memories`, etc.) reside in a separate SQLite file (`session.sqlite`) and are owned exclusively by the Agent layer.
```
This is clear ownership documentation, not an inconsistency. Confirmed by plan 204720.

### DOC-3: /db command naming — Already consistent
All references use `/db rag rebuild-fts` as canonical form. `/db rebuild-fts` is documented as removed alias at L277 of CLI docs. No `fts-rebuild` or `fts.rebuild` CLI command references exist. Confirmed by plan 204850.

### SPEC-4: remote_empty diagnosis semantics — Already correct
`remote_empty` (HTTP 200 but empty response) is correctly diagnosed as success with `fallback_reason=None`, `result_source=REMOTE`, `http_result_kind=EMPTY`. All observability channels (diagnostics, debug output, docs) accurately reflect this. Confirmed by plan 205020.

### Current state of `docs/03_rag_90_inconsistencies_and_known_issues.md`
- `## Active Issues` section: empty (just header and ---)
- `## Resolved Issues` section: 1 entry (ARTIFACT-01)
- `## Design Notes`: 2 entries (DESIGN-2, DESIGN-3)

## Conclusion
No changes needed. The proposed 4 "Active Issues" are either already resolved (DOC-1 → ARTIFACT-01) or not real inconsistencies (DOC-2, DOC-3, SPEC-4). The Active Issues section is correctly empty.
