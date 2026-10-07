## Goal

Migrate `docs/10_adr/ADR-015-reference-document-class-disposition.md` per the target ADR
structure: remove the flat body `## Related Documents` block (no subsections), keep the
still-needed document link that is already in `related:`, drop the non-document tool links
already cited in the body, and tidy headings/blank lines/file endings. Report links moved to
`related:` and invalid links removed (REQ-002 / AC-2).

## Scope

- **In-Scope**: `docs/10_adr/ADR-015-reference-document-class-disposition.md` only. And its
  link-set baseline (compare before/after so no still-needed link is lost, AC-2).
- **Out-of-Scope**: the other 19 ADRs; the rule/tool/test changes (separate rows).

## Assumptions

- The recommended target structure (UNK-01) is adopted.
- `rel001` has landed (prerequisite for the whole plan).

## Design decisions

- Remove the entire `## Related Documents` heading + body (lines 140-145). This block is a
  flat three-link list with no `### Related ADRs` / `### Implementation References`
  subsections, so there is nothing to promote to top-level sections.
- The `[Documentation Policy](../00_governance/governance_01_documentation-policy.md)` link
  is a document link already present in `related:` (front matter line 9) — keep it there; no
  move needed.
- The two `tools/*.py` links (`tools/generate_reference_table.py`,
  `tools/check_docs_content_policy.py`) are non-document code references already cited in the
  body (Verification line 107; line 144) — drop them from the block rather than adding them
  to `related:` (which validates a basename document list).

## Alternatives considered

- Adding the two `tools/*.py` paths to `related:` — rejected: `related:` validates a basename
  document list (schemas/doc_front_matter.json); code references belong in
  `## Implementation References`, and this ADR has none by design.
- Moving every block link wholesale into `related:` — rejected: the plan forbids bulk moves
  (Constraints); each body-only link is judged individually (UNK-02).

## Implementation

### Target file

`docs/10_adr/ADR-015-reference-document-class-disposition.md`

### Procedure

1. **Baseline link set.** Record every link in the block (lines 140-145): markdown
   `[text](path)` and fenced `` `path` `` references, plus the `related:` front-matter entry.
   Save this for the before/after comparison (AC-2).
2. **Link triage.** Confirm the `[Documentation Policy]` link is already in `related:`
   (front matter line 9) — no move. Judge the two `tools/*.py` links as non-document code
   references already cited in the body (line 107, line 144) — delete from the block.
3. **Remove the block.** Delete the `## Related Documents` heading (line 140) and its three
   body lines (142-144), just before `## Completion Checklist` (line 146).
4. **No section promotion.** This block has no `### Related ADRs` / `### Implementation
   References` subsections; do not create any promoted top-level section.
5. **Tidy.** Ensure exactly one blank line between the preceding `## Approval` section and
   `## Completion Checklist`; ensure the file ends with a single trailing newline.

### Method

- Read `ADR-015` lines 138-147 (block + surrounding).
- Apply steps 1-5.
- Confirm no `## Related Documents` (or any `Related Documents`) heading remains at any
  level.

### Details

- Adversarial verification (20261007): Already applied in commit `4316bc537`; `stale_detector.py` reports clean only because it cannot detect an already-applied change. Link-set diff: the governance_01 link is in `related:`; the two `tools/*.py` links were kept as top-level `## Implementation References` (and remain cited in the body); the `(tracked separately)` remark on the GV-018 guard-comment mismatch is gone (untracked-issue wording removed). ADR-015 now also has the required top-level `## Related ADRs`. No link lost. Pre-migration block was lines 140-145; the line numbers below are historical.
- Block layout (current): `## Related Documents`(140) → three flat links (142-144);
  `## Completion Checklist`(146).
- `## Known Deviations`(116) is outside the block; leave it.

## Compatibility considerations

- After migration this ADR must still pass `tools/check_docs_structure.py` (no body
  `Related Documents` at any level) and `tools/check_adr_structure.py` (`## Known Deviations`
  presence intact).
- `adr-index.md`'s dependency graph is unrelated; leave it.

## Security considerations

N/A: documentation restructuring only.

## Rollback considerations

Revert this file to the pre-this-change commit.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `ADR-015` | Link-set comparison | Diff block links vs `related:` before/after | No still-needed link removed |
| `ADR-015` | Structure | Read removed-block region + grep `Related Documents` | No body `Related Documents` at any level |
| Repo | Integration | `uv run python tools/check_docs_structure.py`, `check_adr_structure.py` | Pass |

## Completion criteria

- The body `## Related Documents` block is removed.
- The still-needed `[Documentation Policy]` link remains in `related:`; the two non-document
  `tools/*.py` links are dropped (not added to `related:`).
- No still-needed link was lost (per-ADR diff); invalid links removed are reported.
- The repo passes its own structure checks.

## Out of scope

- The other 19 ADRs; rule/tool/test changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261007-145911 | 20261007-145911 | REQ-002 / AC-2 adversarial verification: already applied in 4316bc537, no link lost; no edit needed |
| 2 | Add or update tests per Validation plan | Completed | 20261007-145911 | 20261007-145911 | N/A: doc-only migration adversarial verification: already applied in 4316bc537, no link lost; no edit needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261007-145911 | 20261007-145911 | check_docs_structure.py + check_adr_structure.py adversarial verification: already applied in 4316bc537, no link lost; no edit needed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261007-145911 | 20261007-145911 | adversarial verification: already applied in 4316bc537, no link lost; no edit needed |

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
- **Requirement ID**: `REQ-002` — migrate this ADR: flat block removed, document link kept in `related:`, non-document tool links dropped, no link lost (AC-2)
- **Source issue**: `issues/20261005-144150_rel002_remove-the-adr-body-related-documents-block-and-update-adr-rules-and-tools.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-084759_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-130122
- **Related target files**: `docs/10_adr/ADR-015-reference-document-class-disposition.md`