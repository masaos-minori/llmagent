## Goal

Migrate `docs/10_adr/adr_02_config-isolation-supporting-sections.md` per the target ADR
structure: remove the body `## Related Documents` block (lines 158-161), keeping both links
that are already present in `related:`; tidy headings/blank lines/file endings. Report links
moved to `related:` and invalid links removed (REQ-002 / AC-2).

## Scope

- **In-Scope**: `docs/10_adr/adr_02_config-isolation-supporting-sections.md` only. And its
  link-set baseline (compare before/after so no still-needed link is lost, AC-2).
- **Out-of-Scope**: the other 19 ADRs; the rule/tool/test changes (separate rows).

## Assumptions

- `rel001` has landed (prerequisite for the whole plan).

## Design decisions

- Remove the entire `## Related Documents` heading + body (lines 158-161). This block is a
  flat two-basename-link list with no `### Related ADRs` / `### Implementation References`
  subsections, so there is nothing to promote to top-level sections.
- Both links (`ADR-002-config-isolation.md`, `adr_00_document-guide.md`) are already present
  in `related:` (front matter lines 11-12) — no move needed.

## Alternatives considered

- Adding the two links to `related:` — rejected: they are already there; the block is simply
  redundant with the front matter.

## Implementation

### Target file

`docs/10_adr/adr_02_config-isolation-supporting-sections.md`

### Procedure

1. **Baseline link set.** Record every link in the block (lines 158-161): fenced `` `path` ``
   references, plus the `related:` front-matter entries. Save this for the before/after
   comparison (AC-2).
2. **Link triage.** Confirm both links are already in `related:` (front matter lines 11-12) —
   no move.
3. **Remove the block.** Delete the `## Related Documents` heading (line 158) and its two body
   lines (160-161), just before `## Keywords` (line 163).
4. **No section promotion.** This block has no `### Related ADRs` / `### Implementation
   References` subsections; do not create any promoted top-level section.
5. **Tidy.** Ensure exactly one blank line between the preceding `## Known Deviations` section
   and `## Keywords`; ensure the file ends with a single trailing newline.

### Method

- Read `adr_02_config-isolation-supporting-sections.md` lines 156-164 (block + surrounding).
- Apply steps 1-5.
- Confirm no `## Related Documents` (or any `Related Documents`) heading remains at any
  level.

### Details

- Block layout (current): `## Related Documents`(158) → two flat links (160-161);
  `## Keywords`(163).
- `## Known Deviations`(154) is outside the block; leave it.

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
| `adr_02_config-isolation-supporting-sections.md` | Link-set comparison | Diff block links vs `related:` before/after | No still-needed link removed |
| `adr_02_config-isolation-supporting-sections.md` | Structure | Read removed-block region + grep `Related Documents` | No body `Related Documents` at any level |
| Repo | Integration | `uv run python tools/check_docs_structure.py` | Pass |

## Completion criteria

- The body `## Related Documents` block is removed.
- Both links remain in `related:`; no still-needed link was lost.
- The repo passes its own structure checks.

## Out of scope

- The other 19 ADRs; rule/tool/test changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-002 / AC-2 |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: doc-only migration |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | check_docs_structure.py |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | |

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
- **Requirement ID**: `REQ-002` — migrate `adr_02_config-isolation-supporting-sections.md`: block removed, links kept in `related:`, no link lost (AC-2)
- **Source issue**: `issues/20261005-144150_rel002_remove-the-adr-body-related-documents-block-and-update-adr-rules-and-tools.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-084759_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-130122
- **Related target files**: `docs/10_adr/adr_02_config-isolation-supporting-sections.md`
