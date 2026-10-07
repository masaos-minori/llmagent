## Goal

Migrate `docs/10_adr/adr_00_document-guide.md` per the target ADR structure: remove the body
`## Related Documents` block (lines 70-73), keeping both links that are already present in
`related:`; keep the existing top-level `## Related ADRs` section (lines 66-68) untouched;
tidy headings/blank lines/file endings. Report links moved to `related:` and invalid links
removed (REQ-002 / AC-2).

## Scope

- **In-Scope**: `docs/10_adr/adr_00_document-guide.md` only. And its link-set baseline
  (compare before/after so no still-needed link is lost, AC-2).
- **Out-of-Scope**: the other 19 ADRs; the rule/tool/test changes (separate rows).

## Assumptions

- The recommended target structure (UNK-04) applies to `adr_00_document-guide.md` too: it is
  checked as an ADR because of its directory, so it follows the same block-removal structure.
- `rel001` has landed (prerequisite for the whole plan).

## Design decisions

- Remove the entire `## Related Documents` heading + body (lines 70-73). This block is a flat
  two-basename-link list with no `### Related ADRs` / `### Implementation References`
  subsections, so there is nothing to promote to top-level sections.
- Both links (`00_index.md`, `overview_00_document-guide.md`) are already present in
  `related:` (front matter lines 9-10) — no move needed.
- Keep the existing top-level `## Related ADRs` section (lines 66-68) as-is; it is already a
  top-level section and needs no promotion.

## Alternatives considered

- Adding the two links to `related:` — rejected: they are already there; the block is simply
  redundant with the front matter.
- Merging the block into `## Related ADRs` — rejected: the targets are non-ADR documents, not
  ADRs; the existing `## Related ADRs` header would be semantically wrong.

## Implementation

### Target file

`docs/10_adr/adr_00_document-guide.md`

### Procedure

1. **Baseline link set.** Record every link in the block (lines 70-73): fenced `` `path` ``
   references, plus the `related:` front-matter entries. Save this for the before/after
   comparison (AC-2).
2. **Link triage.** Confirm both links are already in `related:` (front matter lines 9-10) —
   no move.
3. **Remove the block.** Delete the `## Related Documents` heading (line 70) and its two body
   lines (72-73), just before `## Keywords` (line 75). Leave the existing `## Related ADRs`
   section (lines 66-68) untouched.
4. **No section promotion.** This block has no `### Related ADRs` / `### Implementation
   References` subsections; do not create any promoted top-level section.
5. **Tidy.** Ensure exactly one blank line between the preceding `## Reference API` section
   (`## Related ADRs` follows it) and `## Keywords`; ensure the file ends with a single
   trailing newline.

### Method

- Read `adr_00_document-guide.md` lines 64-76 (block + surrounding).
- Apply steps 1-5.
- Confirm no `## Related Documents` (or any `Related Documents`) heading remains at any
  level.

### Details

- Adversarial verification (20261007): Already applied in commit `4316bc537`; line numbers in this procedure (66-75) did not match the pre-migration file. Link-set diff: `00_index.md` and `overview_00_document-guide.md` are in `related:`. Superseded premise: this procedure keeps the existing top-level `## Related ADRs` section untouched, but that section is gone — its only link (ADR-015) is now in `related:` and the body Related sections are forbidden for non-ADR files by `tools/check_docs_structure.py`. The one-line context phrase (defines how ADRs relate to other document types) was dropped. No link lost. Pre-migration block was lines 66-73; the line numbers below are historical.
- Block layout (current): `## Related ADRs`(66) → one link (68); `## Related Documents`(70) →
  two flat links (72-73); `## Keywords`(75).
- The `## Related ADRs` section (66-68) is already top-level; leave it.

## Compatibility considerations

- After migration this file must still pass `tools/check_docs_structure.py` (no body
  `Related Documents` at any level).

## Security considerations

N/A: documentation restructuring only.

## Rollback considerations

Revert this file to the pre-this-change commit.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `adr_00_document-guide.md` | Link-set comparison | Diff block links vs `related:` before/after | No still-needed link removed |
| `adr_00_document-guide.md` | Structure | Read removed-block region + grep `Related Documents` | No body `Related Documents` at any level; `## Related ADRs` still present |
| Repo | Integration | `uv run python tools/check_docs_structure.py` | Pass |

## Completion criteria

- The body `## Related Documents` block is removed.
- Both links remain in `related:`; the existing `## Related ADRs` section is preserved.
- No still-needed link was lost; invalid links removed are reported.
- The repo passes its own structure checks.

## Out of scope

- The other 19 ADRs; rule/tool/test changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261007-150031 | 20261007-150031 | REQ-002 / AC-2 adversarial verification: already applied in 4316bc537, no link lost; no edit needed |
| 2 | Add or update tests per Validation plan | Completed | 20261007-150031 | 20261007-150031 | N/A: doc-only migration adversarial verification: already applied in 4316bc537, no link lost; no edit needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261007-150031 | 20261007-150031 | check_docs_structure.py adversarial verification: already applied in 4316bc537, no link lost; no edit needed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261007-150031 | 20261007-150031 | adversarial verification: already applied in 4316bc537, no link lost; no edit needed |

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
- **Requirement ID**: `REQ-002` — migrate `adr_00_document-guide.md`: block removed, links kept in `related:`, existing `## Related ADRs` preserved, no link lost (AC-2)
- **Source issue**: `issues/20261005-144150_rel002_remove-the-adr-body-related-documents-block-and-update-adr-rules-and-tools.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-084759_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-130122
- **Related target files**: `docs/10_adr/adr_00_document-guide.md`