## Goal

Migrate `docs/10_adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` per the target ADR
structure: remove the body `## Related Documents` block, promote `Related ADRs` and
`Implementation References` to top-level `## ` sections before `## Completion Checklist`,
drop the `Specifications`/`Known Issues` subsections (targets in `related:` /
`## Known Deviations`), keep context-bearing links as prose where needed, and tidy
headings/blank lines/file endings. Report links moved to `related:` and invalid links
removed (REQ-002 / AC-2).

## Scope

- **In-Scope**: `docs/10_adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` only. And
  its link-set baseline (compare before/after so no still-needed link is lost, AC-2).
- **Out-of-Scope**: the other 19 ADRs; the rule/tool/test changes (separate rows).

## Assumptions

- The recommended target structure (UNK-01) is adopted.
- `rel001` has landed (prerequisite for the whole plan).

## Design decisions

- Remove the entire `## Related Documents` heading + subsection body.
- Promote the old `### Related ADRs` bullets to a new top-level `## Related ADRs`; promote
  the old `### Implementation References` bullets to a new top-level `## Implementation
  References`.
- Drop `### Specifications`, `### Known Issues` (their targets are already in `related:` /
  `## Known Deviations`). Fold any context phrase still needed into `## Implementation Notes`
  or the relevant section as ordinary prose — only where the phrase adds information
  (UNK-02). This ADR has no `### Operations` / `### Companion Document` subsections.
- Keep `## Known Deviations` (with its Known Issue IDs) untouched.

## Alternatives considered

- Moving every block link wholesale into `related:` — rejected: the plan forbids bulk moves
  (Constraints); each body-only link is judged individually (UNK-02).
- Keeping the subsections as `### ` — rejected: the standard header list promotes
  `Related ADRs`/`Implementation References` to top-level `## ` (UNK-01).

## Implementation

### Target file

`docs/10_adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md`

### Procedure

1. **Baseline link set.** Record every link in the block (lines 391-424): markdown
   `[text](path)` and fenced `` `path` `` references, plus the `related:` front-matter entry.
   Save for the before/after comparison (AC-2).
2. **Link triage.** For each block link not in `related:`, judge necessity: move to
   `related:` if still needed, delete if invalid/obsolete, or register Needs Confirmation if
   unjudgeable. Do not move links wholesale (Constraints).
3. **Remove the block.** Delete the `## Related Documents` heading (line 391) and its
   subsection body through the end of `### Implementation References`, just before
   `## Completion Checklist` (line 425).
4. **Promote `## Related ADRs`.** Insert a top-level `## Related ADRs` section (before
   `## Completion Checklist`) carrying the ADR-to-ADR links formerly under `### Related ADRs`.
5. **Promote `## Implementation References`.** Insert a top-level `## Implementation
   References` section carrying the scripts/tests/config references formerly under
   `### Implementation References`.
6. **Drop `### Specifications` / `### Known Issues`.** Fold any still-needed context phrase
   into prose (UNK-02); otherwise omit.
7. **Tidy.** One blank line between promoted sections and surrounding headings; single
   trailing newline.

### Method

- Read `ADR-007` lines 389-426 (block + surrounding).
- Apply steps 1-7.
- Confirm no `## Related Documents` (or any `Related Documents`) heading remains at any level.

### Details

- Adversarial verification (20261007): Already applied in commit `4316bc537`; the line numbers in this procedure match the pre-migration file, but the block no longer exists (file is now 411 lines). Link-set diff: all Specifications targets are in `related:`; Related ADRs are top-level; no file link lost. Implementation Reference `HttpTransport.call_tool()` was corrected to `HttpTransport.call()` in a later commit (`call_tool` does not exist in `scripts/shared/http_transport.py`). All referenced symbols/files/tests and `related:` targets exist (except the ADR-008 note above). Pre-migration block was lines 391-425; the line numbers below are historical.
- Block layout (current): `## Related Documents`(391) → `### Related ADRs`(393),
  `### Specifications`(398), `### Known Issues`(411), `### Implementation References`(415);
  `## Completion Checklist`(425).
- `## Implementation Notes`(338) and `## Known Deviations`(346) are outside the block; leave
  them.

## Compatibility considerations

- After migration this ADR must still pass `tools/check_docs_structure.py` (no body
  `Related Documents` at any level) and `tools/check_adr_structure.py` (reads the new
  top-level `## Implementation References`; `## Known Deviations` presence intact).

## Security considerations

N/A: documentation restructuring only.

## Rollback considerations

Revert this file to the pre-this-change commit.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `ADR-007` | Link-set comparison | Diff block links vs `related:` before/after | No still-needed link removed |
| `ADR-007` | Structure | Read removed-block region + grep `Related Documents` | No body `Related Documents` at any level; `## Related ADRs`/`## Implementation References` present as top-level |
| Repo | Integration | `uv run python tools/check_docs_structure.py`, `check_adr_structure.py` | Pass |

## Completion criteria

- The body `## Related Documents` block is removed.
- `## Related ADRs` and `## Implementation References` exist as top-level sections before
  `## Completion Checklist`.
- No still-needed link was lost (per-ADR diff); links moved to `related:` and invalid links
  removed are reported.
- The repo passes its own structure checks.

## Out of scope

- The other 19 ADRs; rule/tool/test changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261007-145313 | 20261007-145313 | REQ-002 / AC-2 adversarial verification: already applied in 4316bc537, no link lost; no edit needed |
| 2 | Add or update tests per Validation plan | Completed | 20261007-145313 | 20261007-145313 | N/A: doc-only migration adversarial verification: already applied in 4316bc537, no link lost; no edit needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261007-145313 | 20261007-145313 | check_docs_structure.py + check_adr_structure.py adversarial verification: already applied in 4316bc537, no link lost; no edit needed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261007-145313 | 20261007-145313 | adversarial verification: already applied in 4316bc537, no link lost; no edit needed |

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
- **Related target files**: `docs/10_adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md`