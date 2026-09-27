## Goal

Reconcile `docs/21_rag/rag_05_8-rag-mcp-internal-operations-direct-db-access.md`'s body `## Related Documents` list to exactly match its front-matter `related:` list, per REQ-001 (owner ruling on NC-031: front-matter `related:` is authoritative).

## Scope

In scope: this file's body `## Related Documents` link list only. Out of scope: this file's front-matter `related:` list itself (already authoritative, not changed); any other file's `## Related Documents` section (separate rows in the same Plan).

## Assumptions

- Each front-matter `related:` target listed below resolves to an existing file — re-confirm via Read immediately before editing (per this Plan's UNK-01), since this was not path-resolved file-by-file at Plan-authoring time.

## Design decisions

Reconcile by set membership: add every front-matter target missing from the body, remove every body target not in front matter, keep entries already common to both. Preserve this file's own existing citation style (markdown link `[text](path)` vs. bare backtick `` `path` ``) and, for a kept/added entry that already has a title elsewhere in this file, reuse it; otherwise derive the link text from the target file's own title.

## Alternatives considered

Replacing the body list wholesale with a copy of the front-matter list (same paths, generic titles): rejected — this file's body list already contains context (some entries already correct, and for `mcp_03_01_dispatch-and-routing.md`/`mcp_03_02_tool-registry.md` specifically, the body already cites every front-matter sibling via backticks) that a wholesale replacement would discard unnecessarily; a set-reconciliation (add missing, remove extra, keep common) is the smaller, more faithful edit.

## Implementation

### Target file

`docs/21_rag/rag_05_8-rag-mcp-internal-operations-direct-db-access.md`

### Procedure

1. Re-confirm this file's current front-matter `related:` list and body `## Related Documents` list via Read immediately before editing — content may have changed since this Plan/procedure was generated (2026-09-27).
2. Remove any body entry whose target is not in the front-matter list: (none).
3. Add a body entry for any front-matter target missing from the body: `rag_00_document-guide.md`, using that target's own title for the link text (or the existing repository convention for a bare-backtick citation) and matching this file's existing citation style.
4. Leave unchanged any body entry already present in both lists: `rag_05_1-configuration-reference.md`.
5. Confirm the resulting body list's target set exactly equals the front-matter `related:` target set (AC-1).

### Method

Set-reconciliation edit of an existing Markdown list (add missing entries, remove extra entries, keep common entries) — no new section, no front-matter change, no code change.

### Details

- Confirmed via the Plan's corpus scan (2026-09-27): front-matter `related:` targets = `rag_00_document-guide.md`, `rag_05_1-configuration-reference.md`; current body `## Related Documents` targets = `rag_05_1-configuration-reference.md`.
- Re-verify this exact before-state via Read immediately before editing (Procedure step 1) — do not edit from this cached snapshot alone.

## Compatibility considerations

N/A: documentation-only change; affects only this file's own body list, not its front matter or any other file.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

`git revert` the commit, or manually restore the prior body `## Related Documents` list.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `docs/21_rag/rag_05_8-rag-mcp-internal-operations-direct-db-access.md` | Automated | `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_quality.py` | Pass, no new finding beyond the Plan's recorded baseline (300 structure issues, 0 quality errors / 1168 quality warnings) |
| `docs/21_rag/rag_05_8-rag-mcp-internal-operations-direct-db-access.md` | Manual | Re-run the corpus-comparison script (or equivalent `rg`, accounting for both `[text](path)` and bare `` `path` `` citation styles) against this file | Front-matter `related:` targets == body `## Related Documents` targets |

## Completion criteria

- This file's body `## Related Documents` list contains exactly the same target set as its front-matter `related:` list (AC-1).

## Out of scope

- This file's front-matter `related:` list itself.
- Any other file's `## Related Documents` section.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only, automated + manual checks per Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | N/A: documentation-only; docs checkers run instead |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: this document's own target file IS the documentation being updated |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/done/20260927-160936_relateddocsdrift_reconcile-front-matter-related-field-with-body-related-documents-headings.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-170338_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-173902
- **Related target files**: docs/21_rag/rag_05_8-rag-mcp-internal-operations-direct-db-access.md
