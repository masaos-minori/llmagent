## Goal

Add a normative six-term recovery-category glossary and an 18-field x 4-database
recovery-policy matrix to `docs/adr/ADR-008-sqlite-4db-separation.md`, and replace
ambiguous, category-unqualified uses of "recovery"/"リカバリ" in this document's
existing prose with the appropriate new term (`REQ-001`, `REQ-002`, `REQ-003`,
`REQ-006`, `REQ-007`).

## Scope

- In scope: adding two new subsections (glossary, matrix) to this ADR; editing
  existing prose in Context, Decision Details, Rationale, Invariants, Consequences,
  Failure Policy, and Data Ownership and Persistence to use the new terms where the
  current wording is category-ambiguous.
- Out of scope: editing any other file (see the separate implementation procedure
  documents for `docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md`
  and `docs/90_shared_00_document-guide.md`); any change to `scripts/db/recovery.py`,
  `scripts/db/maintenance.py`, or `scripts/db/create_schema.py`; renumbering or
  rewording Decision Details/Invariants beyond the term substitution itself; the
  ADR's `Implementation Notes` section's file/symbol inventory (not part of this
  Plan's Requirements).

## Assumptions

- `docs/adr/ADR-008-sqlite-4db-separation.md` remains the single canonical location
  for this matrix (Plan Assumptions; confirmed no competing canonical document
  exists via this ADR's own `Related Documents` cross-references).
- The six terms are new additions — confirmed via `grep` that none of
  `initialization`, `schema-repair`, `logical-repair`, `derived-data-rebuild`,
  `physical-recovery`, `operator-restore` currently appear in this file.

## Design decisions

- Place the glossary as a new subsection under `## Decision` (e.g. `### Recovery
  Category Glossary`), immediately before or after `### Decision Details`, since the
  six terms name categories that Decision Details #14-20 already distinguishes
  informally — keeping them adjacent avoids forcing a reader to jump between
  sections to connect a term to its originating decision.
- Place the matrix as a new subsection also under `## Decision` (e.g. `### Recovery
  Policy Matrix`), after the glossary — the matrix's cells reference glossary terms,
  so the glossary must appear first in reading order.
- One matrix per persistence domain is not needed; a single table with one row (or
  row-group) per database and one column per policy field satisfies `REQ-002`
  without introducing four near-duplicate tables — apply `skills/DESIGN.md` Avoid
  implementation-reference duplication at the table-structure level (one table, not
  four).
- Term-to-evidence grounding (do not invent policy; cite the existing Decision
  Detail/Invariant number that already establishes each term's boundary, per Plan
  Design section):
  - `initialization` -> `create_schema()` behavior (`scripts/db/create_schema.py`,
    confirmed present), described in `docs/90_shared_05_04_...` section 11 ("DB
    Recreation Procedure").
  - `schema-repair` -> `workflow.sqlite`'s `apply_workflow_migrations()` /
    `eventbus.sqlite`'s `_migrate()` incremental mechanisms (confirmed present:
    `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`
    sections 8a/8b), distinct from `rag`/`session`'s recreate-only path (same doc,
    section 8, "do not support backward-compatible migrations").
  - `logical-repair` -> `RagMaintenanceService.consistency()` (confirmed present in
    `scripts/agent/services/rag_maintenance_service.py`).
  - `derived-data-rebuild` -> `RagMaintenanceService.rebuild_fts()` /
    `rebuild_vec()` (confirmed present, same file) — `rag.sqlite`-only, per
    Decision Detail #11/#20.
  - `physical-recovery` -> `recover_corruption()`'s `DbCondition.CORRUPTION` path
    (confirmed present in `scripts/db/recovery.py`: `DbCondition` StrEnum with
    `HEALTHY`/`CORRUPTION`/`LOCK_CONTENTION`/`PERMISSION_FAILURE`/`INVALID_FORMAT`/
    `UNKNOWN` members).
  - `operator-restore` -> the manual, operator-triggered nature of
    `recover_corruption()` itself (Decision Detail #14, #17), and `workflow`/
    `eventbus`'s manual-only policy (Decision Detail #20, Invariant INV-18).

## Alternatives considered

- Defining the six terms inline at each first use, instead of a dedicated glossary
  subsection: rejected — the Issue requires one authoritative definition per term,
  and inline repetition would risk drifting wording across the ~29 existing
  "recovery"/"リカバリ" occurrences in this file.
- Splitting the matrix into four separate per-database tables: rejected per Design
  decisions above — a single table keeps all four domains comparable side-by-side,
  matching the Issue's "side-by-side" framing (Plan Problem section), and avoids
  duplicating the 18-field header four times.

## Implementation

### Target file

`docs/adr/ADR-008-sqlite-4db-separation.md`

### Procedure

1. Insert the six-term glossary subsection under `## Decision`.
2. Insert the 18-field x 4-database matrix subsection immediately after the
   glossary.
3. Walk the ~29 existing "recovery"/"リカバリ" occurrences in this file (`Summary`,
   `Context > Problem`, `Context > Constraints`, `Decision Details` #10/#14/#20,
   `Rationale` #1/#3/#4, `Consequences` (Positive/Negative/Operational),
   `Invariants` INV-09/INV-13/INV-17/INV-18, `Failure Policy` (Retry Policy),
   `Data Ownership and Persistence` (`Recovery Source` field)) and replace each
   category-unqualified use with the matching glossary term, leaving
   category-spanning uses unchanged (e.g. the `## Status`/`## Decision` headings
   themselves, and any sentence that genuinely spans more than one category, such
   as Decision Detail #10's "各DBに独立したBackup、Recovery..." which spans all six
   categories and stays as the umbrella word).
4. Re-verify Invariant INV-18's `workflow.sqlite`/`eventbus.sqlite`
   automatic-restore-prohibited wording is preserved verbatim in meaning after term
   substitution (`REQ-006`; `AC-6`, `AC-7`) — only the category word changes, not
   the prohibition itself.
5. Add a fail-closed default statement to the new matrix for a hypothetical
   future database whose recovery source or policy field is undefined (`REQ-007`;
   `AC-1` residual case) — phrase as a matrix-level footnote or default row, not as
   a gap in any of the four existing database rows, since all four currently have a
   defined policy.

### Method

- Author the glossary as one definition sentence per term, each explicitly citing
  the Decision Detail number or code symbol it is grounded in (per Design decisions
  above) — follow `skills/DESIGN.md` Output language's normative-term guidance
  (short, explicit sentences; one claim per sentence).
- Author the matrix with one row per database (`rag.sqlite`, `session.sqlite`,
  `workflow.sqlite`, `eventbus.sqlite`) and columns for the 18 policy fields the
  Issue lists (system of record, owning component, recovery source or explicit
  "none", automatic-restore permission, operator-approval requirement, post-restore
  physical/logical verification requirement, and the remaining fields per the
  Issue's Required Change 2 — cross-reference the Issue file directly for the
  complete 18-field list, since `skills/DESIGN.md` No implementation counts
  disallows restating "18" as a hardcoded catalog here; name the fields from the
  Issue's own list rather than re-deriving them).
- Populate every cell from an existing Decision Detail/Invariant/Data Ownership
  value (Decision Details #1-4 for system of record/owner, #10/#20 and Invariants
  INV-09/INV-18 for recovery source and automatic-restore permission, `Data
  Ownership and Persistence` for System of Record/Recovery Source/Deletion Rule) —
  do not invent a policy value not already stated somewhere in this ADR.
- For term substitution, use plain find-and-classify: for each occurrence, decide
  which of the six categories the surrounding sentence actually describes (using
  the Design decisions grounding above), then substitute; if a single sentence
  genuinely spans multiple categories, leave the umbrella word and note why in the
  edit (no inline comment needed in the final ADR text itself, since ADRs do not
  carry meta-commentary about their own edits).

### Details

- No code changes. This is a Markdown-only edit to one `docs/adr/*.md` file.
- The glossary and matrix are additive subsections; term substitution is an
  in-place edit of existing sentences — no section is removed or renamed.
- `## Related Documents > Known Issues` already cross-references `SHARED-003` (the
  `workflow`/`eventbus` runbook gap) — leave that cross-reference as-is; this row
  does not touch `docs/00_governance_03_issue-and-uncertainty-management.md` (that
  file is a Reference File only for this Plan, verified only by the
  `90_shared_05_04` row's procedure, not this one).

## Compatibility considerations

- Purely additive (new subsections) plus in-place prose term substitution — no
  heading is renamed, no existing subsection is removed, so no inbound anchor link
  from another document breaks as a direct result of this row's edit (unlike the
  `90_shared_05_04` row, which does remove section 9.7's prose).
- `docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md`'s own
  cross-reference to "ADR-008 Decision Details #20 for the canonical recovery
  policy" (see that document's section 9.7, to be rewritten by the sibling
  implementation procedure) continues to resolve, since Decision Detail #20 itself
  is not removed, only term-substituted.

## Security considerations

- No new secret, credential, or sensitive value is introduced — glossary/matrix
  content is drawn entirely from already-accepted ADR policy per `skills/DESIGN.md`
  No secrets in output.
- No change to `Security Consequences`'s existing statement that recovery
  Error/Audit records exclude row-level DB content — that sentence is
  category-spanning (spans multiple recovery categories) and is left unchanged
  per Procedure step 3.

## Rollback considerations

- Revert is a single Markdown file edit; `git revert`/`git checkout` against this
  one commit fully restores prior wording with no data-migration or runtime-state
  concern (documentation-only change).

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/adr/ADR-008-sqlite-4db-separation.md` | Documentation structure/quality check | `uv run python tools/check_docs_quality.py` | No new findings introduced by the glossary/matrix additions |
| `docs/adr/ADR-008-sqlite-4db-separation.md` | Documentation structure check | `uv run python tools/check_docs_structure.py docs/adr/ADR-008-sqlite-4db-separation.md` | Passes (heading structure, Front Matter, internal links) |
| `docs/adr/ADR-008-sqlite-4db-separation.md` | Manual review | Re-read Invariant INV-18 after edit | `workflow.sqlite`/`eventbus.sqlite` automatic-restore prohibition wording unchanged in meaning (`AC-6`, `AC-7`) |

## Completion criteria

- The glossary subsection defines all six terms, each citing a concrete Decision
  Detail/Invariant/code symbol.
- The matrix subsection covers all four databases across the Issue's full field
  list, with no invented (non-ADR-traceable) value.
- No category-unqualified "recovery"/"リカバリ" occurrence remains in this file
  except genuinely category-spanning ones (headings, umbrella sentences).
- `tools/check_docs_quality.py` and `tools/check_docs_structure.py` report no new
  findings for this file.
- Invariant INV-18's `workflow`/`eventbus` automatic-restore prohibition is
  confirmed unchanged in meaning (`AC-6`, `AC-7`).

## Out of scope

- Editing `docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md` or
  `docs/90_shared_00_document-guide.md` — each has its own implementation procedure
  document (rows 2 and 3 of the Plan's Implementation Target Files table).
- Verifying/correcting `docs/00_governance_03_issue-and-uncertainty-management.md`'s
  `SHARED-003` Target field — that verification belongs to the `90_shared_05_04`
  row's procedure (Plan Phase 2 step 4), since it is conditional on that row's
  section 9.7 rewrite.
- Any change to `scripts/db/recovery.py`, `scripts/db/maintenance.py`, or
  `scripts/db/create_schema.py` (Plan Out-of-Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add glossary + matrix subsections; apply term substitution per Procedure/Method/Details | Done | — | — | Glossary/matrix already present from prior commit; term substitution applied: 9 occurrences replaced (initialization/operator-restore/schema-repair/logical-repair/derived-data-rebuild/physical-recovery), 1 category-spanning cross-reference left unchanged |
| 2 | No test changes required — documentation-only row (Plan Tests section) | N/A | — | — | Not applicable: no `pytest` target for this row |
| 3 | Run `check_docs_quality.py` / `check_docs_structure.py` per Validation plan | Done | — | — | check_docs_quality.py passed; check_docs_structure.py reports pre-existing warnings (size limit, broken links, missing sections) |
| 4 | N/A — this row's change is itself the documentation update; no further downstream doc depends on this row | N/A | — | — | |

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
- **Requirement ID**: REQ-001 (glossary), REQ-002 (matrix), REQ-003 (term
  substitution), REQ-006 (INV-18 preservation), REQ-007 (fail-closed default)
- **Source issue**: issues/20260903-110304_h0701_define-recovery-policy-per-sqlite-persistence-domain.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260905-162730_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-113622
- **Related target files**: docs/adr/ADR-008-sqlite-4db-separation.md
