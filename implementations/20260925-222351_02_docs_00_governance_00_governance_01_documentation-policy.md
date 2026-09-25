# Implementation Procedure: Fix `[ADR Index]` hyperlink in `docs/00_governance/00_governance_01_documentation-policy.md`

## Goal

Replace the broken link target `(../adr-index.md)` with `(../10_adr/adr-index.md)` on line 545 of `docs/00_governance/00_governance_01_documentation-policy.md`, restoring navigation to the ADR Index and satisfying the link-reachability check. Driven by REQ-002.

## Scope

- Modify exactly one hyperlink target string on one line in `docs/00_governance/00_governance_01_documentation-policy.md`.
- No changes to front matter, headings, content, or any other file.

## Assumptions

- The correct relative path from `docs/00_governance/` to `docs/10_adr/adr-index.md` is `../10_adr/adr-index.md` (verified against the existing file).
- Line 545 currently contains `- [ADR Index](../adr-index.md)`.
- `check_docs_structure.py` reports `broken link -> '../adr-index.md'` for this file.

## Design decisions

- Minimal surgical text replacement: only the link target string changes, preserving all surrounding characters.
- No restructuring of the document, no front-matter changes, no content additions.

## Alternatives considered

- Moving `docs/adr-index.md` back to `docs/adr-index.md` (rejected: the file was moved during a prior reorganization; `docs/10_adr/adr-index.md` is the established canonical location).
- Updating both links simultaneously in a single edit (not applicable: two separate files, two separate edits).

## Implementation

### Target file

`docs/00_governance/00_governance_01_documentation-policy.md`

### Procedure

1. Locate line 545 in `docs/00_governance/00_governance_01_documentation-policy.md`.
2. Replace the link target `(../adr-index.md)` with `(../10_adr/adr-index.md)` on that line.
3. Preserve every other character on the line.

### Method

Edit-only: use the Write tool to replace the exact line content. The line before:

```
- [ADR Index](../adr-index.md)
```

The line after:

```
- [ADR Index](../10_adr/adr-index.md)
```

### Details

- The `..` component climbs one level from `docs/00_governance/` to `docs/`, then `10_adr/adr-index.md` enters the ADR directory.
- This is a Path A change (≤ 3 files, no public/runtime interface change, no DB schema change).
- No other occurrence of `(../adr-index.md)` exists on line 545 — it appears exactly once as the link target.
- After editing, verify the line reads: `- [ADR Index](../10_adr/adr-index.md)`.

## Compatibility considerations

- This change does not affect runtime behavior, API contracts, or data formats.
- It only affects markdown link resolution within the documentation set.
- The link target `../10_adr/adr-index.md` resolves correctly from `docs/00_governance/` regardless of the working directory used to invoke `check_docs_structure.py`.

## Security considerations

N/A: documentation-only change; no code execution, no user input, no authentication.

## Rollback considerations

- Revert the single-line edit: restore `(../adr-index.md)` on line 545.
- No data loss risk; no downstream dependencies affected.
- No migration or schema rollback needed.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/00_governance_01_documentation-policy.md` | Static link-reachability check | `uv run python tools/check_docs_structure.py docs/00_governance/00_governance_01_documentation-policy.md` | No `broken link -> '../adr-index.md'` (size-limit Warning may remain, pre-existing) |

## Completion criteria

- AC-1: Line 545 of `docs/00_governance/00_governance_01_documentation-policy.md` contains `[ADR Index](../10_adr/adr-index.md)`.
- AC-2: `check_docs_structure.py` no longer reports `broken link -> '../adr-index.md'` for this file.
- AC-3: No other content in the file is modified.

## Out of scope

- Fixing other broken links reported by `check_docs_structure.py` (e.g., `21_rag/03_rag_00_document-guide.md`, `22_mcp/04_mcp_00_document-guide.md`, etc.).
- Modifying `docs/10_adr/adr-index.md` itself.
- Adding automated link-checking to CI.
- Backtick-wrapped inline code spans that mention `adr-index.md` (textual references, not links).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Doc-only change; no tests added |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: REQ-002 — fix `[ADR Index]` hyperlink to resolve to `docs/10_adr/adr-index.md`
- **Source issue**: issues/20260925-120301_gov003_fix_missing_adr_index_paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260925-174307_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260925-222351
- **Related target files**: docs/00_governance/00_governance_01_documentation-policy.md
