# Implementation Procedure: `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` (ADR-008 amendment)

## Goal
Amend ADR-008's decision text so the migration contract for `workflow`/`eventbus`, the pre-migration backup gate, and failure behavior are recorded as decided, while the recreate policy is kept for `rag`/`session` (Plan row 20; REQ-008, AC-7).

## Scope
- In scope: ADR-008 body edits (decision text, scope section, revisit-trigger section) per the canonical ADR structure.
- Out of scope: the index row (row 21), the DB spec docs (rows 22–23), any code.

## Current shape (facts)
- `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md:60` states all four DBs "have no migration mechanism and are recreated on a schema change. Migration design is out of scope for this ADR." (re-verified 2026-10-30).
- `:359` lists a revisit trigger: "A migration mechanism or a replicated storage foundation is introduced".
- ADR-008 churn: 4 commits/30d (Plan Affected areas) — rebase against HEAD immediately before editing (Plan Risk mitigation).

## Assumptions
- The amendment records decisions this Plan implements (Plan REQ-008/AC-7 requires the approval record be discoverable, not a silent edit); the amendment date/status follows the repo's ADR metadata convention (canonical metadata schema, `skills/DESIGN.md`).
- Docs content is English, intent/boundary/constraint-level only — no implementation details (docs content policy).

## Design decisions
- Amend in place (status: amended, decision record kept visible) rather than superseding with a new ADR — the storage-separation decision stands; only the migration sub-decision changes.
- The `:60` sentence is split by domain: `workflow`/`eventbus` = forward-only registered migrations with verified-backup precondition and refuse-on-unknown semantics; `rag`/`session` = recreate policy retained verbatim.
- Update the revisit-trigger section (`:359` area): mark the "migration mechanism introduced" trigger as realized by this Plan (cross-reference plan path), keeping remaining triggers (replication) open.

## Alternatives considered
- New ADR superseding 008 — rejected: separation semantics, DB-per-domain rationale, and rag/session policy are unchanged; a supersede would fragment the record AC-7 asks to consolidate.

## Implementation
### Target file
- `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` (modify)

### Procedure
1. Update ADR metadata (status/date/amendment note) per the canonical ADR metadata schema.
2. Amend the §7 migration sentence (`:60`): domain-split contract as above, one sentence per contract, naming the failure behavior (refusal before mutation; no partial application).
3. Add a short "Amendment" decision subsection: what changed, why (forward-only migration contract adopted), and the cross-reference to the plan and `docs/41_db/db_03...` (row 22) where the operational contract lives.
4. Update the revisit-trigger list (`:359` area) to reflect the realized trigger.

### Method
Markdown edits only; keep existing section numbering stable so cross-refs from db_03/db_07 remain valid.

### Details
- Line anchors shift as text is added; re-locate by section heading at edit time, not by fixed line numbers.

## Compatibility considerations
- Overlap adjudication (recorded during planning): four plans touch `docs/10_adr/adr_01_index.md`; adrauth001 lands its ADR rows first (ADR authority model), then this amendment appends without restructuring the index.
- Docs checkers (`routing.md` Tools) must pass after the edit; run stale detector on this doc row's claims.

## Security considerations
- None (documentation only).

## Rollback considerations
- `git checkout` the file; code behavior is independent of ADR text.

## Validation plan
- Automated: docs checker(s) per `routing.md` "When to run which tool" (docs index/structure checks); `tools/stale_detector.py` on this procedure doc.
- Manual: reviewer confirms the amendment is visible from `adr_01_index.md` (AC-7 discoverability).

## Completion criteria
- ADR-008 records the migration contract per domain, the backup precondition, failure behavior, and an amendment/approval trail discoverable via the index (AC-7).

## Out of Scope
- Index row update (row 21). Operational runbook text (row 23).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Land after code rows per Plan sequencing Edited ADR-008: replaced recreate-only Constraints bullet with forward-only migration contract for workflow/eventbus (verified-backup precondition, refusal classes, transactional rollback, schema_migrations ledger). Added 'Amendment (dbmig001)' H3 subsection and realized the Revisit Trigger. Front matter/INV/Known Deviations/Approval untouched. |
| 2 | Add or update tests per Validation plan | Completed | — | — | Docs checkers only Docs checkers only. check_docs_quality OK; check_docs_content_policy --strict OK; check_docs_structure OK (raised adr_02_05_008 ceiling 33647->34206 in check_docs_structure.py SIZE_EXCEPTIONS, documented); check_docs_japanese OK. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | Docs checker subset check_adr_preservation: 1 WARNING (Decision section text changed, intentional, mapped in commit). No ERROR. check_docs_consistency has no governance domain; ADRs validated via adr-* pre-commit hooks + preservation tool. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | This row is the documentation Procedure doc itself is the deliverable; archived after doc gates pass. |

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
- **Requirement ID**: `REQ-008`
- **Source issue**: `issues/20261029-104500_dbmig001_forward-only-db-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-214108_dbmig001_forward-only-db-migrations.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-071336
- **Related target files**: `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`