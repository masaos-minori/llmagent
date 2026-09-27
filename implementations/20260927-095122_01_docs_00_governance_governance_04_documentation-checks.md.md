## Goal

Add a brief clarifying note at the start of the `## Manual Checks` section in `docs/00_governance/governance_04_documentation-checks.md`, explaining that its numbering (9-14) continues a single scheme shared with the preceding `## Automated Checks` section (items 1-8, plus 15-16 added later) — confirmed via Plan verification that items 1-8 are not missing/deleted, only located in a different section (REQ-004).

## Scope

In scope: adding one clarifying note immediately before or within `### 9. Canonical Source Verification` (the first Manual Checks entry). Out of scope: renumbering any existing item (would break the confirmed creation-order numbering scheme); restoring/adding any content for items 1-8 (they already exist, under Automated Checks); modifying any check's content (REQ-005).

## Assumptions

- The Plan's own confirmed evaluation outcome (recorded in its Background section) is authoritative: items 1-8 exist in `## Automated Checks`; the numbering is continuous-by-creation-order across both sections; REQ-002/REQ-003 (explain-if-deleted / restore-if-omitted) do not apply; only REQ-004's minimal clarifying note is warranted.
- A concurrent process was observed (via `git status`/`git diff`) to have made large, unrelated-but-uncommitted edits to this same file's Governance Verification Matrix and Follow-up Work Needed sections during this session — those sections are physically distant from `## Manual Checks` (which this document edits), but re-confirm the exact current line numbers for `## Manual Checks`/`### 9.` immediately before editing regardless, since the file is under active concurrent modification.

## Design decisions

- Add the note as a single introductory sentence/paragraph directly under the `## Manual Checks` heading (before `### 9. Canonical Source Verification`), rather than as a footnote or a change to the `## Automated Checks` section — keeps the clarification exactly where a reader encountering the apparent gap would look.

## Alternatives considered

- Renumbering `## Manual Checks`'s items to start at 1 (making it 1-6 locally): rejected per the Plan's confirmed finding — the current numbers (9-14) are meaningful as part of a repository-wide creation-order allocation shared with `## Automated Checks`'s 1-8 and 15-16; renumbering would break that scheme and could desynchronize any external reference to a specific check by number (none currently found, but the risk is unnecessary given a lower-risk alternative exists).
- Reordering `## Automated Checks` so items 15-16 physically follow item 8 immediately (right before `## Manual Checks` begins), making the whole document read in strict ascending numeric order: rejected — larger diff than necessary (moves 2 existing entries), and out of scope per REQ-006 ("keep changes isolated"); the numbering itself is not broken, only non-obvious without the note.

## Implementation

### Target file

`docs/00_governance/governance_04_documentation-checks.md`

### Procedure

1. Re-confirm the current `## Manual Checks` heading's line number and the exact content of `### 9. Canonical Source Verification` via `grep -n "^## Manual Checks\|^### 9\." docs/00_governance/governance_04_documentation-checks.md` (adversarial re-verification — this file is under active concurrent edit elsewhere in the same session).
2. Insert one clarifying sentence immediately after the `## Manual Checks` heading and before `### 9. Canonical Source Verification`, e.g.: "Numbering continues from `## Automated Checks` above (items 1-8); items 15-16 were added to that section after items 9-14 below had already been assigned, so the full 1-16 sequence appears across both sections in creation order, not strict document order."

### Method

Single-paragraph insertion at one location — no renumbering, no content change to any existing check.

### Details

- Insertion point: immediately after the `## Manual Checks` line (confirmed at line 192 as of this Plan's investigation — re-confirm exact line at implementation time per Procedure step 1), before `### 9. Canonical Source Verification`.
- Confirmed via this Plan's investigation: `## Automated Checks` contains `### 1.` through `### 8.` (lines 19-149) then `### 15.`/`### 16.` (lines 164, 178); `## Manual Checks` contains `### 9.` through `### 14.` (lines 194-271 as of investigation) — the full 1-16 sequence has no duplicate and no true gap when both sections are considered together.

## Compatibility considerations

- Documentation-only, additive change (one new sentence); no existing content is removed or renumbered, so no external reference to an existing check number is affected.

## Security considerations

N/A: documentation clarity change, no security-relevant behavior change.

## Rollback considerations

- `git revert` the commit, or manually remove the added sentence. Given a concurrent process is independently editing this same file elsewhere, coordinate any rollback with awareness that other, unrelated sections may have changed since this edit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `docs/00_governance/governance_04_documentation-checks.md` | Manual verification | Read the `## Manual Checks` section | The clarifying note is present and accurately describes the cross-section numbering scheme; no existing check's number or content changed |

## Completion criteria

- A reader of `## Manual Checks` in isolation can determine, from the note alone, that items 1-8 are not missing but live in the preceding `## Automated Checks` section.
- No existing check's number, heading, or content is altered.

## Out of scope

- Renumbering any check in either section.
- Reordering `## Automated Checks`'s items 15-16 relative to items 1-8.
- Any Governance Verification Matrix or Follow-up Work Needed content (a different section of this same file, under concurrent, unrelated edit elsewhere in this session).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only, manual verification per Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | N/A: documentation-only change; no code validation sequence applies |
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
- **Requirement ID**: REQ-004: add a clarifying note about the continuous cross-section numbering
- **Source issue**: issues/20260926-183302_manual_checks_numbering_mismatch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260926-200158_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-095122
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md
