## Goal

Update `docs/90_shared_00_document-guide.md`'s AI Query Routing table and
Canonical Source Rules so a reader looking for recovery policy is routed to the
new ADR-008 recovery-policy matrix (`REQ-005`).

## Scope

- In scope: the `AI Query Routing` table's `Maintenance, Recovery` row (line
  48); the `Canonical Source Rules` section (lines 59-62).
- Out of scope: any other row of the AI Query Routing table; the `File Index`,
  `Governance`, `Guidance for Safe AI Use`, or `Related ADRs` sections; editing
  `docs/adr/ADR-008-sqlite-4db-separation.md` (row 1) or
  `docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md` (row
  2).

## Assumptions

- The ADR-008 matrix (row 1's output) and the rewritten section 9.7 pointer
  (row 2's output) both exist by the time this row's edit is verified — this
  row only adds a routing pointer to them, it does not itself define the
  matrix's location. If row 1 or row 2 is still pending when this row is
  processed, this row's edit remains valid regardless of processing order,
  since it references the matrix by its already-fixed target location
  (`docs/adr/ADR-008-sqlite-4db-separation.md`), not by content that could
  still change.

## Design decisions

- Extend, not replace, the existing `Maintenance, Recovery` row: keep
  `05_maintenance` / `05_recovery` (module-boundary/API-reference routing,
  still valid for non-policy maintenance questions) and add the ADR-008 matrix
  as an additional routing target specifically for recovery-*policy*
  questions — the row currently conflates "how do I call maintenance
  functions" with "what is the recovery policy for domain X", and only the
  second question is what this Plan's matrix answers.
- Add one new bullet to `Canonical Source Rules` (not a new section) — pointing
  to the ADR-008 matrix as the canonical source for persistence-domain recovery
  policy — since this section already exists specifically to tell a reader
  which document to trust when policy/content questions arise, matching the
  new matrix's canonical-source role stated in Plan Implementation intent.

## Alternatives considered

- Adding a new standalone "Recovery Policy" row/section instead of editing the
  existing `Maintenance, Recovery` row: rejected — would leave two
  routing entries for an overlapping question (recovery), risking a reader
  following the older, narrower entry and missing the new matrix; editing the
  existing row in place keeps one authoritative routing path per question
  type.

## Implementation

### Target file

`docs/90_shared_00_document-guide.md`

### Procedure

1. Edit the `AI Query Routing` table's `Maintenance, Recovery` row (line 48):
   append a reference to the ADR-008 recovery-policy matrix for
   policy-category questions, keeping the existing `05_maintenance` /
   `05_recovery` references for API/operational questions.
2. Add one bullet to `Canonical Source Rules` (after the existing two bullets,
   lines 61-62): state that `docs/adr/ADR-008-sqlite-4db-separation.md`'s
   recovery-policy matrix is the canonical source for persistence-domain
   recovery policy, superseding any per-domain policy prose duplicated
   elsewhere (cross-referencing row 2's section 9.7 rewrite, which now points
   to the same matrix rather than restating policy).

### Method

- Row edit: split the single "Maintenance, Recovery" question cell's answer
  into "maintenance API usage -> `05_maintenance`/`05_recovery`" and "recovery
  *policy* per persistence domain -> ADR-008 Recovery Policy Matrix", keeping
  the row as one table row (add the second reference inside the same
  "Reference Target" cell, comma- or slash-separated per this table's existing
  convention) rather than adding a new row, per Design decisions above.
- Canonical Source Rules bullet: follow the existing two bullets' terse,
  one-sentence style (see lines 61-62 for the pattern) — state the rule, name
  the canonical file, do not restate the matrix's content itself (per
  `skills/DESIGN.md` Avoid implementation-reference duplication).

### Details

- No code changes. This is a Markdown-only edit to one `docs/90_shared_*.md`
  file, touching only the two named locations.
- Do not alter the `Recommended Reading Order (Human)` diagram (lines 29-34) —
  it lists document-group traversal order, not per-question routing, and is
  not named in `REQ-005`.

## Compatibility considerations

- Table-row and bullet-list edits only — no heading is renamed or removed, so
  no inbound cross-reference to this document's own headings breaks.
- This document's own `related:` front-matter and `Related ADRs` section
  already list `docs/adr/ADR-008-sqlite-4db-separation.md` (line 93) — no
  front-matter change is needed to legitimize the new routing pointer.

## Security considerations

- No new secret, credential, or sensitive value introduced — routing-table and
  canonical-source-rule text only.

## Rollback considerations

- Revert is a single Markdown file edit; `git revert`/`git checkout` fully
  restores the prior row/bullet text, with no data-migration or runtime-state
  concern.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/90_shared_00_document-guide.md` | Documentation structure/quality check | `uv run python tools/check_docs_quality.py` | No new findings |
| `docs/90_shared_00_document-guide.md` | Documentation structure check | `uv run python tools/check_docs_structure.py docs/90_shared_00_document-guide.md` | Passes; routing table entry resolves to the new matrix location |

## Completion criteria

- The `Maintenance, Recovery` row routes a recovery-policy question to the
  ADR-008 matrix, in addition to its existing `05_maintenance`/`05_recovery`
  references.
- `Canonical Source Rules` states the ADR-008 matrix as canonical for
  persistence-domain recovery policy.
- `tools/check_docs_quality.py` and `tools/check_docs_structure.py` report no
  new findings for this file.

## Out of scope

- Editing `docs/adr/ADR-008-sqlite-4db-separation.md` (row 1) or
  `docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md` (row
  2).
- Any other row of the AI Query Routing table, or any other section of this
  document not named in Scope above.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit AI Query Routing table's Maintenance, Recovery row and add Canonical Source Rules bullet per Procedure/Method/Details | Pending | — | — | |
| 2 | No test changes required — documentation-only row (Plan Tests section) | N/A | — | — | Not applicable: no `pytest` target for this row |
| 3 | Run `check_docs_quality.py` / `check_docs_structure.py` per Validation plan | Pending | — | — | |
| 4 | N/A — this row's change is itself the documentation update | N/A | — | — | |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260903-110304_h0701_define-recovery-policy-per-sqlite-persistence-domain.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260905-162730_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-113622
- **Related target files**: docs/90_shared_00_document-guide.md
