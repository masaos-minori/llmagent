## Goal

Migrate `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md` per the target ADR
structure: remove the body `## Related Documents` block, promote `Implementation References`
to a top-level `## ` section before `## Completion Checklist`, drop the `Specifications`/
`Known Issues` subsections (their targets are in `related:`), keep context-bearing links as
prose where needed, and tidy headings/blank lines/file endings. Report links moved to
`related:` and invalid links removed (REQ-002 / AC-2).

## Scope

- **In-Scope**: `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md` only. And its
  link-set baseline (compare before/after so no still-needed link is lost, AC-2).
- **Out-of-Scope**: the other 19 ADRs; the rule/tool/test changes (separate rows).

## Assumptions

- The recommended target structure (UNK-01) is adopted.
- `rel001` has landed (prerequisite for the whole plan).

## Design decisions

- Remove the entire `## Related Documents` heading + subsection body.
- Promote the old `### Implementation References` bullets to a new top-level `## Implementation
  References`.
- Drop `### Specifications`, `### Known Issues` (their targets are already in `related:`).
  Fold any context phrase still needed into `## Implementation Notes` or the relevant section
  as ordinary prose — only where the phrase adds information (UNK-02). This ADR has no
  `### Related ADRs` / `### Operations` / `### Companion Document` subsections.
- Keep `## Known Deviations` (with its Known Issue IDs) untouched.
- Update the stale "See Related Documents > Implementation References" prose (line 205) to
  point at the new top-level `## Implementation References` (the old section name is being
  removed).

## Alternatives considered

- Moving every block link wholesale into `related:` — rejected: the plan forbids bulk moves
  (Constraints); each body-only link is judged individually (UNK-02).
- Keeping the subsections as `### ` — rejected: the standard header list promotes
  `Implementation References` to top-level `## ` (UNK-01).

## Implementation

### Target file

`docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md`

### Procedure

1. **Baseline link set.** Record every link in the block (lines 236-255): markdown
   `[text](path)` and fenced `` `path` `` references, plus the `related:` front-matter entry.
   Save this for the before/after comparison (AC-2).
2. **Link triage.** For each block link not present in `related:`, judge necessity: move to
   `related:` if still needed, delete if invalid/obsolete, or register Needs Confirmation if
   unjudgeable. Do not move links wholesale (Constraints).
3. **Remove the block.** Delete the `## Related Documents` heading (line 236) and its
   subsection body through the end of `### Implementation References` (line 253), just before
   `## Completion Checklist` (line 255).
4. **Promote `## Implementation References`.** Insert a top-level `## Implementation
   References` section (before `## Completion Checklist`) carrying the scripts/tests references
   formerly under `### Implementation References` (lines 247-253).
5. **Drop `### Specifications` / `### Known Issues`.** Their targets are already in
   `related:`; fold any still-needed context phrase into prose (UNK-02); otherwise omit.
6. **Tidy.** Update the "See Related Documents > Implementation References" prose (line 205)
   to the new top-level `## Implementation References`; ensure exactly one blank line between
   the promoted section and surrounding headings; ensure the file ends with a single trailing
   newline.

### Method

- Read `ADR-012` lines 234-256 (block + surrounding).
- Apply steps 1-6.
- Confirm no `## Related Documents` (or any `Related Documents`) heading remains at any
  level.

### Details

- Adversarial verification (20261007): Already applied in commit `4316bc537`; the line numbers in this procedure (236-255) did not match the pre-migration file either. Link-set diff: all Specifications targets are in `related:`; no file link lost; top-level `## Related ADRs`/`## Implementation References` sit before `## Completion Checklist`; all Implementation References kept. All referenced symbols/files/tests and `related:` targets exist. Pre-migration block was lines 214-233; the line numbers below are historical.
- Block layout (current): `## Related Documents`(236) → `### Specifications`(238),
  `### Known Issues`(243), `### Implementation References`(246); `## Completion
  Checklist`(255).
- `## Implementation Notes`(203) and `## Known Deviations`(211) are outside the block; leave
  them.

## Compatibility considerations

- After migration this ADR must still pass `tools/check_docs_structure.py` (no body
  `Related Documents` at any level) and `tools/check_adr_structure.py` (reads the new
  top-level `## Implementation References`; `## Known Deviations` presence intact).
- `adr-index.md`'s dependency graph is unrelated; leave it.

## Security considerations

N/A: documentation restructuring only.

## Rollback considerations

Revert this file to the pre-this-change commit.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `ADR-012` | Link-set comparison | Diff block links vs `related:` before/after | No still-needed link removed |
| `ADR-012` | Structure | Read removed-block region + grep `Related Documents` | No body `Related Documents` at any level; `## Implementation References` present as top-level |
| Repo | Integration | `uv run python tools/check_docs_structure.py`, `check_adr_structure.py` | Pass |

## Completion criteria

- The body `## Related Documents` block is removed.
- `## Implementation References` exists as a top-level section before `## Completion
  Checklist`.
- No still-needed link was lost (per-ADR diff); links moved to `related:` and invalid links
  removed are reported.
- The repo passes its own structure checks.

## Out of scope

- The other 19 ADRs; rule/tool/test changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261007-145500 | 20261007-145500 | REQ-002 / AC-2 adversarial verification: already applied in 4316bc537, no link lost; no edit needed |
| 2 | Add or update tests per Validation plan | Completed | 20261007-145500 | 20261007-145500 | N/A: doc-only migration adversarial verification: already applied in 4316bc537, no link lost; no edit needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261007-145500 | 20261007-145500 | check_docs_structure.py + check_adr_structure.py adversarial verification: already applied in 4316bc537, no link lost; no edit needed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261007-145500 | 20261007-145500 | adversarial verification: already applied in 4316bc537, no link lost; no edit needed |

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
- **Requirement ID**: `REQ-002` — migrate this ADR: block removed, sections promoted, no link lost (AC-2)
- **Source issue**: `issues/20261005-144150_rel002_remove-the-adr-body-related-documents-block-and-update-adr-rules-and-tools.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-084759_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-130122
- **Related target files**: `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md`