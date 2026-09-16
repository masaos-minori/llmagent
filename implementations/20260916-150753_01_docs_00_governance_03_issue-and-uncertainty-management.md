## Goal

Correct RAG-005's wrong table reference (`chunks_fts` → `chunks_vec`), resolve DESIGN-2's speculative bypass claim with a literal, cited grep result and a corrected `Type`, and remove RAG-005 from the active inventory as a prose placeholder pointing to ADR-005's existing documentation of the same limitation.

## Scope

- Replace RAG-005 entry (lines ~109-126) with a prose placeholder citing `chunks_vec`, `scripts/rag/ingestion/document_manager.py::delete_document_chain()`, and ADR-005's Known Deviations section.
- Update DESIGN-2 entry (lines ~149-166): rewrite `Observed Implementation` to state the literal grep result and citation, remove the "may"/"could" hedge, and change `Type` to `operational-gap`.
- Run `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` after all edits and confirm it passes.

## Assumptions

- The two entries exist at approximately the line ranges specified in the Plan.
- `grep -rn "chunks_fts" scripts/` found matches only in: (a) `scripts/mcp_servers/mdq/*.py` (distinct table in separate database `/opt/llm/db/mdq.sqlite`); (b) `scripts/db/schema_sql.py` (schema/trigger definition); (c) sanctioned rebuild path; (d) read-only SELECT queries. Zero bypasses found.
- ADR-005's Known Deviations section (lines 342-350) already documents the `chunks_vec` FK-enforcement limitation and deletion-ordering mitigation.

## Design decisions

- Use the existing prose-placeholder pattern verbatim — do not introduce a new format.
- Each placeholder must cite concrete evidence so a future reader does not need Git history to understand why each was closed/corrected.
- Do not modify any other document — ADR-005 is read-only for this Plan.

## Alternatives considered

- Creating a new "Resolved Entries" section — rejected because the Plan's intent is to use the existing prose-placeholder convention already established by RAG-003, RAG-004, DESIGN-1.

## Implementation
### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Locate the RAG-005 entry (approximately lines 109-126).
2. Replace the RAG-005 full entry with a prose placeholder following the established pattern.
3. Locate the DESIGN-2 entry (approximately lines 149-166).
4. Update the DESIGN-2 entry: rewrite `Observed Implementation` to state the literal grep result, remove the "may"/"could" hedge, and change `Type` to `operational-gap`.
5. Run `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` and confirm it passes.

### Method

#### RAG-005 Placeholder (replace lines ~109-126)

Current entry structure:
```markdown
- **RAG-005**: [full entry with wrong table name chunks_fts, Status: open]
```

Required replacement:
```markdown
**RAG-005**: Resolved. sqlite-vec lacks FK constraints — `chunks_vec` has no foreign key pointing to `chunks`; mitigation enforced via deletion ordering (`chunks_vec` deleted before `documents`) confirmed in `scripts/rag/ingestion/document_manager.py::delete_document_chain()` (confirmed: lines 19-35). This limitation is documented in `docs/adr/ADR-005-rag-source-derived-index-relationships.md`'s Known Deviations section (lines 342-350). Its absence from the active list is the correct, policy-compliant state — do not create a `#### RAG-005` heading.
```

#### DESIGN-2 Entry Correction (update lines ~149-166)

Current entry structure:
```markdown
- **DESIGN-2**: [entry with Type: missing-documentation, Observed Implementation containing "may bypass"]
```

Required update:
```markdown
Change `Type` from `missing-documentation` to `operational-gap`.

Rewrite `Observed Implementation`:
```
Zero direct-write bypasses of ADR-005's rebuild-path restriction found. All non-wrapper, non-schema hits on `chunks_fts` outside `scripts/mcp_servers/mdq/` belong to the sanctioned `/session rag-rebuild-fts` path (invoked via `scripts/agent/commands/cmd_session.py`). Read-only `SELECT`/`bm25`/consistency-check queries against `chunks_fts` appear in `scripts/rag/repository.py` and `scripts/db/rag_consistency.py`. MDQ's `chunks_fts` references target a separate database (`/opt/llm/db/mdq.sqlite`, confirmed: `scripts/mcp_servers/mdq/mdq_service.py` line 67) and are out of ADR-009's RAG-boundary scope.
```

Remove all instances of "may", "could", "might" from the `Observed Implementation` field — replace with definitive statements based on the grep result.

### Details

Each placeholder follows the same four-part structure:
1. "Resolved." statement
2. Evidence citation (specific function, test, or document with line references)
3. Contextual note (legacy migration only / re-evaluation trigger)
4. "Its absence from the active list is the correct, policy-compliant state — do not create a `#### {ID}` heading."

The exact line numbers should be verified at edit time against the current file content before making replacements.

## Compatibility considerations

- This is a documentation-only change — no code compatibility impact.
- The placeholders preserve enough context from the original entries so that a future reader can understand why each was closed without consulting Git history.

## Security considerations

- No security impact — documentation-only change.

## Rollback considerations

- If a placeholder is found to omit critical context, revert to the original entry and correct the placeholder text. No behavioral rollback needed since there is none.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance_03_issue-and-uncertainty-management.md` | Documentation quality | `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` | Passes with no new findings |
| `docs/00_governance_03_issue-and-uncertainty-management.md` | Manual re-scan for the corrected error | `grep -n "chunks_fts" docs/00_governance_03_issue-and-uncertainty-management.md` | No hit inside a RAG-005 entry (entry removed) |
| `docs/00_governance_03_issue-and-uncertainty-management.md` | Manual re-scan for Type consistency | `grep -n "DESIGN-2" -A 12 docs/00_governance_03_issue-and-uncertainty-management.md` | `Type: operational-gap`, `Observed Implementation` has no "may"/"could" |

## Completion criteria

- RAG-005 contains no reference to `chunks_fts`.
- RAG-005's table naming is consistent with CI-011's description of ADR-005.
- The table-name correction is verified against the schema (`scripts/db/schema_sql.py`), not inferred from surrounding prose.
- DESIGN-2's `Observed Implementation` states a verified result with no "may" or "could".
- The grep command and its literal output are cited in DESIGN-2.
- DESIGN-2's `Type` is `operational-gap`.
- `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` passes clean.

## Out of scope

- Implementing orphan-vector cleanup.
- Migrating to a vector store with FK support.
- Implementing the ADR-009 enforcement lint rule or integration test.
- Retuning RAG retrieval behavior.
- Editing `docs/adr/ADR-005-rag-source-derived-index-relationships.md` — its existing "Known Deviations" section already documents the `chunks_vec` FK-enforcement limitation and the deletion-ordering mitigation.
- Filing a separate live-violation Known Issue entry — the grep run under this Plan's own investigation found zero bypasses.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20260915-200136_rag01_correct-the-rag-entries-table-naming-and-classification.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-150753_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-150753
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
