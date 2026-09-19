## Goal
Add a short, section-specific cross-reference from
`docs/00_governance_01_documentation-policy.md` to the extended Guidelines
section in `docs/00_governance_02_documentation-metadata.md`, so no
independently-worded duplicate mechanical-content rule is ever added here
(`REQ-003`).

## Scope
In scope: adding one short cross-reference sentence/link near the most relevant
existing location in this file. Out of scope: any other content change to this
file; restating the Guidelines section's rules here.

## Assumptions
- No "Mechanically-Derivable Content Rule" (or any independently-worded
  mechanical-content rule) currently exists in this file — re-confirmed via a
  fresh `rg -i "mechanical|duplicat"` pass, no match beyond this row's own
  planned addition.
- A document-level link to `00_governance_02_documentation-metadata.md` already
  exists in this file's Related Documents section (line 539) and Claim Type
  Taxonomy (line 131), but no section-specific pointer to the Guidelines
  subsection exists elsewhere — re-confirmed by reading the full file's heading
  structure.

## Design decisions
Place the new cross-reference near the Claim Type Taxonomy's
`documentation-metadata` row (line 131), since that is the existing table row
whose "Canonical source kind" column already names
`docs/00_governance_02_documentation-metadata.md` for metadata-field claims —
extending that row's context (or the paragraph immediately following the table)
with a one-line pointer to its Guidelines subsection keeps the cross-reference
next to the one place this file already names that document as authoritative,
rather than introducing a new, disconnected mention elsewhere.

## Alternatives considered
Adding the cross-reference only to the existing Related Documents section (line
539) was considered, but rejected as insufficient on its own — that section
links to the whole document, not the specific Guidelines subsection a reader
would need when about to write a "what to delete" style rule; a
section-specific pointer next to the Claim Type Taxonomy row is more likely to
be seen at the point of temptation to duplicate.

## Implementation
### Target file
docs/00_governance_01_documentation-policy.md

### Procedure
1. Add one sentence near the `documentation-metadata` row of the Claim Type
   Taxonomy table (line 131) or in the prose immediately following that table,
   pointing to `00_governance_02_documentation-metadata.md`'s "Guidelines for
   Recording Information Verifiable via Implementation Reference" section by
   heading name, stating that any future mechanical-content/removability rule
   belongs there, not as a new rule in this file.

### Method
Direct text edit (`Edit` tool) — a single added sentence, no restructuring of
the Claim Type Taxonomy table itself.

### Details
- Example wording: "Any rule for deciding whether documentation content is
  mechanically removable (verifiable from code, config, or schema alone)
  belongs in `00_governance_02_documentation-metadata.md`'s 'Guidelines for
  Recording Information Verifiable via Implementation Reference' section — do
  not add a second, independently-worded rule here."
- Do not modify the Claim Type Taxonomy table's existing rows/columns — add the
  sentence as prose adjacent to the table, not as a new table row.
- Depends on seq 01's edit (`implementations/20260919-114337_01_docs_00_governance_02_documentation-metadata_md.md`)
  having landed first only in the sense that the Guidelines section's exact
  heading text should be re-confirmed unchanged before citing it here — the two
  edits are otherwise independent (different files, no shared line ranges).

## Compatibility considerations
Documentation-only, additive single-sentence change — no runtime, schema, or
code impact. No existing table row or heading in this file is altered.

## Security considerations
N/A: no code, credentials, or runtime behavior described or changed.

## Rollback considerations
Trivial: `git checkout -- docs/00_governance_01_documentation-policy.md`
reverts this single-sentence addition with no downstream dependency.

## Validation plan
- Run `uv run python tools/check_docs_quality.py` and `uv run python
  tools/check_docs_structure.py` — expect no new findings.
- Manual review: confirm no independently-worded "what to delete" rule exists
  anywhere in this file after the edit, and that the new cross-reference
  correctly names the Guidelines section's heading text.

## Completion criteria
- A short, section-specific cross-reference to
  `00_governance_02_documentation-metadata.md`'s Guidelines section is present
  in this file.
- No second, independently-worded mechanical-content rule exists in this file.
- `tools/check_docs_quality.py`/`tools/check_docs_structure.py` report no new
  findings.

## Out of scope
Restating the Guidelines section's content here; modifying the Claim Type
Taxonomy table's structure.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260919-120838 | 20260919-120838 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260919-120838 | 20260919-120838 | N/A: documentation-only — manual review + structural checks only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260919-120838 | 20260919-120838 | Pre-existing, unrelated findings confirmed via `git stash` comparison (present before this edit too): file-size-limit warning (29466→29795 bytes, already over 24576 before this 2-line addition) and 10 "Content similarity" warnings at lines 207-225 (RACI model section) — out of scope for this row |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260919-120838 | 20260919-120838 | N/A: this document's own Target file IS the documentation being updated |

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
- **Requirement ID**: REQ-003 (add a short cross-reference to the Guidelines section)
- **Source issue**: issues/done/20260918-130135_docspol01_extend-metadata-guidelines-not-duplicate-rule.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-104700_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-114337
- **Related target files**: docs/00_governance_01_documentation-policy.md