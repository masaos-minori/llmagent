## Goal

Rewrite `docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md`
section 9.7 to point at the new ADR-008 recovery-policy matrix instead of
duplicating persistence-domain policy prose, and apply the six-term recovery
vocabulary substitution to the rest of section 9 (`REQ-003`, `REQ-004`).

## Scope

- In scope: rewriting section 9.7's body (keeping only API/parameter-mapping
  detail specific to this document); term-substituting "recovery"/"リカバリ"
  elsewhere in section 9 (9.1-9.6, 9.8, 9.9) where category-unqualified.
- Out of scope: editing `docs/adr/ADR-008-sqlite-4db-separation.md` (separate
  implementation procedure, row 1) or `docs/90_shared_00_document-guide.md`
  (separate implementation procedure, row 3); editing section 10-13 of this
  document (not named in Plan Requirements); any code change to
  `scripts/db/recovery.py`.

## Assumptions

- The new ADR-008 matrix (produced by this Plan's row-1 implementation
  procedure) will use the same six category terms this row substitutes into
  section 9 prose — both rows share the Plan's Design > Term-to-evidence
  grounding, so no separate vocabulary needs to be invented here.
- Section 9.7's heading text (`### 9.7 Persistence-domain policy`) is preserved
  verbatim — confirmed necessary because
  `docs/00_governance_03_issue-and-uncertainty-management.md`'s `SHARED-003`
  entry (line 416, confirmed present by Read) has `Target: 90_shared_05_04_db_api_and_operations-recovery-and-reference.md section 9.7 Persistence-domain policy` —
  changing the heading text or number would break that cross-reference.

## Design decisions

- Keep section 9.7's heading and its existing cross-reference sentence ("See
  ADR-008 Decision Details #20 for the canonical recovery policy across all
  four DB domains", confirmed present at line 73) — the rewrite adds a pointer
  to the new matrix immediately after this sentence rather than replacing it,
  since Decision Details #20 remains a valid citation after row 1's term
  substitution (the Decision Detail number does not change, only its wording).
- Retain the four per-domain bullets (lines 75-79: reconstructable derived
  data, session data, RAG data, workflow/approval data, event delivery state)
  only insofar as they state API/parameter-mapping detail not covered by the
  ADR matrix (which `recover_corruption(target=...)` value maps to which
  domain, which function performs the domain's derived-data rebuild) — remove
  the parts that restate policy already in decision-detail form (automatic
  restore permission per domain), per `skills/DESIGN.md` Avoid
  implementation-reference duplication applied to the ADR-vs-API-reference
  split.
- Do not change section 9.7's heading text or heading level — this is the
  binding design decision from Assumptions above (SHARED-003 Target
  preservation).

## Alternatives considered

- Deleting section 9.7 entirely and replacing it with a single "See ADR-008"
  sentence: rejected — this document's own stated purpose (API reference) still
  needs the `target=` parameter-to-domain mapping, which the ADR matrix (a
  policy table, not an API reference) is not the right place to state; some
  section 9.7 content must survive as API-reference detail (`REQ-004`).
  Rejected also because it would leave the document with a heading followed by
  a single line, and SHARED-003's Target still needs a resolvable heading with
  actual content under it.
- Renumbering or removing section 9.7 and merging it into 9.9 (Implementation
  references): rejected per the Assumptions above — would break SHARED-003's
  `Target` cross-reference, requiring an out-of-scope edit to
  `docs/00_governance_03_issue-and-uncertainty-management.md`'s Target field
  that this Plan's Reference Files treat as conditional, not committed, scope.

## Implementation

### Target file

`docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md`

### Procedure

1. Rewrite section 9.7's body: keep the opening sentence and the ADR-008
   cross-reference sentence; replace the four per-domain bullets' policy
   content (automatic-restore permission per domain) with a pointer to the new
   ADR-008 matrix; retain only the `target=` parameter-to-domain mapping and
   which function performs derived-data rebuild for the reconstructable-data
   bullet.
2. Term-substitute category-unqualified "recovery"/"リカバリ" in sections
   9.1-9.6, 9.8, 9.9 using the same six terms row 1 defines in ADR-008 (do not
   invent new wording here — reuse row 1's glossary once it exists).
3. After the section 9.7 rewrite, re-verify
   `docs/00_governance_03_issue-and-uncertainty-management.md`'s `SHARED-003`
   `Target` field (`90_shared_05_04_db_api_and_operations-recovery-and-reference.md section 9.7 Persistence-domain policy`)
   still resolves — the heading text/number is unchanged per Design decisions,
   so this is expected to pass; if it does not (e.g. the heading was
   inadvertently altered), this is a Plan-level discrepancy per
   `rules/workflow-lifecycle.md` Implementation Target Files Validation — do
   not silently edit `docs/00_governance_03_...` under this row's scope (that
   file is a Reference File, not a Target File, for this Plan); instead report
   `Plan Gap` and route the correction through a Plan amendment.

### Method

- Rewrite 9.7 as: [unchanged opening sentence] + [unchanged ADR-008
  cross-reference sentence] + a new sentence pointing to the ADR-008 matrix by
  name (e.g. "See ADR-008's Recovery Policy Matrix for the full per-domain
  policy comparison.") + the retained API/parameter-mapping bullets (trimmed of
  duplicated policy prose per Design decisions).
- For the term substitution pass, apply the same find-and-classify method as
  row 1's Method section: read each "recovery"/"リカバリ" occurrence in
  sections 9.1-9.6/9.8/9.9, classify against the six categories using row 1's
  Term-to-evidence grounding, substitute unless the sentence is genuinely
  category-spanning (e.g. the "## 9. Corruption Recovery" heading itself, or
  9.1 Purpose's opening sentence which spans multiple categories).
- Preserve all `Explicit in code` / `Confirmed by code` / `Verified by test`
  evidence labels exactly as they appear — term substitution changes the
  category word only, not the evidence classification.

### Details

- No code changes. This is a Markdown-only edit to one `docs/90_shared_*.md`
  file.
- Section 9.9 "Implementation references" is a bare symbol list (no prose) —
  confirmed no term substitution is needed there; skip it in Procedure step 2
  if inspection confirms no "recovery"/"リカバリ" word appears in prose form
  (only symbol names).
- The `## 10. Error Handling`, `## 11. DB Recreation Procedure`, `## 12.
  Verification Plan`, and `## 13. AI Reference Guide` sections are out of
  scope (not part of "section 9" the Plan's `REQ-003`/`REQ-004` target) — leave
  them unchanged even where they use "recovery"/"リカバリ" language (e.g.
  section 13's "How to recover from corruption" bullet), since the Plan scopes
  term substitution to sections 9 and the ADR only.

## Compatibility considerations

- Section 9.7's heading is preserved verbatim (Design decisions,
  Assumptions) — `docs/adr/ADR-008-sqlite-4db-separation.md`'s own `Related
  Documents > Specifications` entry linking to this document, and
  `docs/00_governance_03_...`'s `SHARED-003` `Target` field, both continue to
  resolve.
- Content removed from section 9.7 (per-domain automatic-restore-permission
  prose) becomes redundant with, not contradictory to, the new ADR-008 matrix —
  no reader-facing information is lost, only its single source of truth
  changes (per `skills/DESIGN.md` Avoid implementation-reference duplication).

## Security considerations

- No new secret, credential, or sensitive value introduced.
- Section 9.8's existing statement about excluding row-level DB content from
  recovery Error/Audit records is unchanged (category-spanning sentence, left
  as-is per Method).

## Rollback considerations

- Revert is a single Markdown file edit; `git revert`/`git checkout` fully
  restores prior section 9.7 prose and prior section 9 wording, with no
  data-migration or runtime-state concern.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md` | Documentation structure/quality check | `uv run python tools/check_docs_quality.py` | No new findings |
| `docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md` | Documentation structure check | `uv run python tools/check_docs_structure.py docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md` | Passes; no dangling reference to removed section 9.7 prose |
| `docs/00_governance_03_issue-and-uncertainty-management.md` | Cross-reference verification only (no edit expected) | `uv run python tools/check_docs_consistency.py --domain overview` | `SHARED-003` Target field resolves; no broken internal link reported |

## Completion criteria

- Section 9.7's heading text is unchanged; its body points to the ADR-008
  matrix and retains only API/parameter-mapping detail.
- No category-unqualified "recovery"/"リカバリ" occurrence remains in sections
  9.1-9.6, 9.8, 9.9 except genuinely category-spanning ones.
- `SHARED-003`'s `Target` field in `docs/00_governance_03_...` still resolves
  after the rewrite (Procedure step 3).
- `tools/check_docs_quality.py` and `tools/check_docs_structure.py` report no
  new findings for this file.

## Out of scope

- Editing `docs/adr/ADR-008-sqlite-4db-separation.md` (row 1) or
  `docs/90_shared_00_document-guide.md` (row 3).
- Editing `docs/00_governance_03_issue-and-uncertainty-management.md` itself —
  Procedure step 3 only verifies its `SHARED-003` Target field resolves; an
  edit is performed only if that verification fails, which is a conditional
  Plan-amendment path, not a committed change of this row.
- Sections 10-13 of this document (Plan scopes term substitution to section 9
  and the ADR only).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite section 9.7 body; term-substitute sections 9.1-9.6/9.8/9.9 per Procedure/Method/Details | Pending | — | — | |
| 2 | No test changes required — documentation-only row (Plan Tests section) | N/A | — | — | Not applicable: no `pytest` target for this row |
| 3 | Re-verify `SHARED-003` Target field resolves post-rewrite (Procedure step 3) | Pending | — | — | |
| 4 | Run `check_docs_quality.py` / `check_docs_structure.py` / `check_docs_consistency.py --domain overview` per Validation plan | Pending | — | — | |

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
- **Requirement ID**: REQ-003 (term substitution), REQ-004 (section 9.7 rewrite)
- **Source issue**: issues/20260903-110304_h0701_define-recovery-policy-per-sqlite-persistence-domain.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260905-162730_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-113622
- **Related target files**: docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md
