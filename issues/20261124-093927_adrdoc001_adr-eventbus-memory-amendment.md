Generated at: 20261124-093927

# Amend ADR-006 and ADR-008 for SQLite-only EventBus, bounded retention, and Episodic Memory

## Priority
High

## Summary
Amend ADR-006 and ADR-008 as one coordinated architecture-documentation change: SQLite-only EventBus persistence, no EventBus or Agent Memory JSONL, bounded state-aware EventBus retention, ADR-008 renamed around six SQLite stores, and the Repository Context / Episodic Memory design. The same issue updates the Approval Ledger impact, ADR authority configuration, ADR index, and invariant verification matrix, because these artifacts are mechanically linked to the ADR text.

## Background
Source: `memo-issue.md` (consolidated documentation issues, scope limited to ADR and documentation updates). Verified against current source on 2026-11-24:
- `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` still describes a JSONL archive as a "secondary audit log" and a derived data store, a WARNING-only behavior on JSONL append failure, and a test `test_publish_succeeds_if_jsonl_append_fails` as invariant evidence (INV-02).
- `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` carries the filename `4db` while its front matter title reads "Separating SQLite into Six Databases"; its Approval Record already lists pending decision-text changes tracked by AAL-024, AAL-026, AAL-027 and (for ADR-006) AAL-029.
- The Approval Ledger lives in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 5 (entries AAL-024, AAL-026, AAL-027, AAL-029 confirmed present; approver and date are `Not recorded`).
- The listed ADR tools, `config/adr_authority.toml`, `tools/_adr_authority_core.py`, `tools/check_db_separation.py`, and `tests/tools/test_check_db_separation.py` exist in the repository.
- The memo's claims about the target design (Repository Context, Episodic Memory, retention rules) are the approved redesign direction supplied by the requester; they are not re-derived from code here.

## Problem
The ADR set holds mutually inconsistent decisions and labels:
- ADR-006 and the EventBus documents describe `events.jsonl` although publish success is decided by the SQLite commit and a JSONL append failure neither fails nor repairs the event; the file is an incomplete replica, not a source of truth, backup, recovery source, or audit ledger.
- ADR-006 and ADR-008 accept unbounded EventBus growth (events, delivery rows, DLQ outbox rows, DLQ artifacts, WAL files, verified archives) without a retention contract.
- ADR-008 describes six SQLite files while its filename and verification language still say four databases.
- ADR-008 documents the old Agent memory design (Semantic Memory, JSONL, pin/unpin, manual writes, `/memory prune`, `/memory rebuild`), which conflicts with the redesign in which Repository Context is non-persistent and Episodic Memory is the only persistent Agent memory.
- Pending Approval Ledger entries describe the old architecture; approving them unchanged would make the obsolete design authoritative.
- ADR authority, front matter, generated index sections, and the invariant matrix are linked, so prose-only edits cause governance and CI drift.

## Reason for Change
Correctness and operational risk: operators and implementers can take wrong actions (rely on JSONL as a recovery source, assume unbounded replay) while the pending approvals keep obsolete text authoritative. The redesign work depends on the ADRs being the approved baseline, so this must precede the EventBus and Agent documentation rewrites.

## Implementation Intent
Produce one coherent decision model, preserving approval integrity (no approval name or date is invented):
- `eventbus.sqlite` is the sole EventBus system of record; EventBus creates no `events.jsonl`.
- Structured security audit logs stay operational logs and are not EventBus replicas, backups, or recovery sources. DLQ JSON files stay derived artifacts reconstructable from SQLite.
- EventBus retention is state-aware, never age-only, and replay before the retained floor fails explicitly.
- ADR-006 is the primary authority for EventBus persistence, delivery, replay, and retention; ADR-008 is the primary authority for SQLite-store separation and lifecycle policy.
- Repository Context is loaded from configured repository files and is not persisted; Episodic Memory is the only persistent Agent long-term memory, stored only in `session.sqlite`.
- Agent Memory JSONL, EventBus JSONL, `/memory`, pin/unpin, manual memory writes, and JSONL import/rebuild leave the current architecture.
Withdraw or replace pending ledger decisions instead of silently editing them.

## Target Files or Areas
- `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
- `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
- `docs/10_adr/adr_01_index.md`
- `docs/10_adr/adr_00_document-guide.md`
- `docs/10_adr/adr_02_07_016_adr-authority-model.md`
- `config/adr_authority.toml`
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (Approval Ledger, Part 5)

## Required Changes
A. Approval Ledger and decision ownership
- [ ] Update AAL-024 so its scope is six SQLite stores.
- [ ] Withdraw the pending decision that accepts unbounded EventBus growth as a risk (AAL-026 text on the `eventbus.sqlite` retention rule and INV-09 accepted-risk wording).
- [ ] Withdraw the pending decision that retains Agent Memory JSONL (AAL-027 memory canonical-store classification, as applicable).
- [ ] Withdraw or replace the pending EventBus retention-risk decision (AAL-029).
- [ ] Create new approval items for (1) Repository Context and Episodic Memory, (2) removal of EventBus `events.jsonl`, (3) EventBus state-aware retention and replay expiration.
- [ ] Prepare one review package per amended ADR: old decision, proposed decision, rationale, affected documents, expected implementation impact, removed behavior, new invariants, verification expectations.
- [ ] Leave approver and approval-date fields unrecorded until the responsible maintainer supplies them.

B. ADR-006 amendment
- [ ] Define `eventbus.sqlite` as the sole source of truth for events, consumer delivery state, consumer offsets, DLQ state, DLQ outbox state, requeue lineage, retention-participant state, and retention-maintenance state.
- [ ] State that EventBus does not create `events.jsonl`; publish success is a successful SQLite commit; broker notification is a best-effort side effect that cannot roll back a committed event.
- [ ] State that structured security audit records are operational logs, not replicas, backups, replay sources, or recovery sources.
- [ ] Define DLQ JSON files as derived artifacts; define `events.dlq_at` and `dlq_outbox` as authoritative DLQ state; prohibit automatic deletion of `pending` and `failed` outbox rows.
- [ ] Define a persistent source of truth for consumers that take part in retention safety, or record the unresolved owner decision if the consumer-registry model is not yet approved. State that authorization generations, connected subscribers, offsets, and existing delivery rows are individually insufficient to identify the participant set.
- [ ] Prohibit deletion based solely on event age; require all active participants to acknowledge an event or be explicitly decommissioned before purge.
- [ ] Block purge when DLQ processing is incomplete, outbox state is `pending` or `failed`, a legal hold applies, or requeue lineage must be retained; purge an event and its dependent delivery/outbox state as one referentially consistent unit.
- [ ] Define `earliest_available_seq` and `latest_available_seq`; define HTTP 410 with error code `replay_position_expired` for replay or subscribe positions before the floor; prohibit silent consumer-offset advancement; redefine `since_seq=0` as the earliest retained event.
- [ ] Define retention as a dedicated maintenance task separate from the DLQ repair loop.
- [ ] Define capacity signals (database size, WAL size, free disk, purge lag, retention-blocked count, oldest retained event age, last retention result), warning versus critical behavior, and that critical disk shortage and retention-invariant failure make readiness false.

C. ADR-008 amendment
- [ ] Change the title to `ADR-008: Separation and Lifecycle Policy for Six SQLite Stores`.
- [ ] Rename the file to `adr_02_05_008_db-six-sqlite-store-separation.md` only when all references can be updated atomically; otherwise align title and content first and record the rename as a follow-up inside this issue.
- [ ] Identify the four platform-domain databases (`rag.sqlite`, `session.sqlite`, `workflow.sqlite`, `eventbus.sqlite`) and the two non-domain stores (`mcp_dedup.sqlite`, `mdq.sqlite`).
- [ ] Prohibit physical-path sharing, cross-store `ATTACH`, cross-store foreign keys, and schema-qualified cross-store access.
- [ ] Define sessions, messages, conversation state, session diagnostics, Episodic Memory events, and Episodic relations as authoritative `session.sqlite` data; Episodic FTS and Vector indexes as derived data.
- [ ] Remove Semantic Memory, User Semantic, memory JSONL, pin state, manual memory writes, and `/memory` data from the current policy.
- [ ] Define configured repository files as the source of truth for Repository Context, not stored in SQLite or JSONL and without a persistent FTS or Vector index.
- [ ] Define Episodic Memory as the only persistent long-term Agent memory, generated internally, with no user-facing CRUD contract, recoverable only from verified SQLite backup.
- [ ] Define EventBus authoritative and derived data consistently with amended ADR-006; remove `events.jsonl`, JSONL writers, JSONL recovery, and JSONL count comparisons from the recovery policy matrix.
- [ ] Add authoritative data, derived data, backup, restore, schema mismatch, retention, capacity monitoring, failure mode, owner, and verification columns for all six stores; record unresolved lifecycle policies as known deviations instead of leaving ambiguous cells.

D. ADR authority, index, and invariant matrix
- [ ] Make ADR-006 the primary authority for EventBus persistence, delivery, replay, retention; ADR-008 the primary authority for store separation and lifecycle policy; add only necessary supplemental authority edges between them.
- [ ] Update ADR front matter to match `config/adr_authority.toml`; update ADR-008 display names in the ADR index and document guide; remove current-specification references to four-database separation.
- [ ] Add invariants for SQLite-only EventBus durability, absence of EventBus JSONL, safe retention, replay-floor failure, six-store separation, non-persistent Repository Context, SQLite-only Episodic Memory, and absence of both JSONL memory paths.
- [ ] Update Automated Tests tables with real test paths and test-node names only; mark unverifiable items Manual, Partial, or Not verified with cadence and expected evidence.
- [ ] Regenerate guarded ADR index sections with the official generator; do not edit generated sections by hand.

## Constraints
- Approval integrity: an implementer never writes an approver, a date, or an approval sentence, and never creates an entry for a past approval (Approval Ledger Rules, `governance_03` Part 5).
- Scope is ADR and documentation only. Generated sections are changed only through the generator.
- ADR amendments follow the repository's ADR amendment process; the structure, authority, reference, preservation, and invariant-matrix checks must pass afterwards.
- Documentation content must not duplicate implementation references (see `skills/DESIGN.md` "Avoid implementation-reference duplication").

## Acceptance Criteria
- [ ] ADR-006 contains no current decision requiring EventBus `events.jsonl` and defines a state-aware retention model with explicit replay expiration.
- [ ] ADR-008 describes six SQLite stores consistently in its title, body, index entry, and verification scope, and describes Repository Context and Episodic Memory as designed.
- [ ] Neither Agent Memory JSONL nor EventBus JSONL appears as a current recovery source.
- [ ] Old Approval Ledger decisions are withdrawn or replaced rather than silently changed; no approval name or date is fabricated.
- [ ] ADR authority has one primary owner per target and no cycles.
- [ ] `tools/check_adr_structure.py`, `tools/check_adr_authority.py`, `tools/check_adr_reference.py`, `tools/check_adr_preservation.py`, and `tools/check_adr_invariant_matrix.py` pass after the amendment.
- [ ] Every blocking invariant cites a real passing automated test.

## Testing Expectations
Documentation-only change with mechanical gates: the five ADR checkers above, `tools/generate_adr_authority.py` (drift check), the DB-separation verification cited by ADR-008 (`tools/check_db_separation.py`, `tests/tools/test_check_db_separation.py`), the EventBus tests cited by ADR-006, and `.github/run_cited_adr_tests.py`. Test citations whose tests do not yet exist (for example for retention and replay-floor invariants) must be marked Not verified or Partial, not cited as passing.

## Documentation Impact
Yes. ADR-006, ADR-008, the ADR index and document guide, ADR authority model and configuration, and the Approval Ledger. Record intent, boundaries, constraints, failure behavior, retention and capacity operations, and Known Deviations / Needs Confirmation items for undecided lifecycle policies.

## Out of Scope
- Production code, database schema, route, retention-worker, CLI, test, and configuration implementation.
- Recording approvals on behalf of the maintainer.
- EventBus and Agent documentation outside the ADR set (see the dependent issues).

## Dependencies
- Overlaps `issues/20261123-104604_gov005_adr-approval-ledger.md`, which tracks closing all 37 ledger entries including AAL-024, AAL-026, AAL-027, AAL-029. This issue replaces or withdraws those four entries by amendment; gov005 must drop them from its scope or be re-verified after this issue is resolved. This issue does not depend on gov005 completing.
- Blocks issues/20261124-093928_adrdoc002_eventbus-docs-sqlite-retention.md, issues/20261124-093929_adrdoc003_agent-memory-docs-episodic.md, and issues/20261124-093930_adrdoc004_docs-regenerate-cross-validate.md.

## Unresolved Questions
- `不明`: the approved consumer-registry model for retention participants; if not approved, ADR-006 records the open owner decision.
- `不明`: whether all references to `adr_02_05_008_db-sqlite-4db-separation.md` can be updated atomically in this change or the rename is a follow-up.
- `不明`: exact new invariant numbers and test citations (depend on the current ADR Verification tables and cited tests).
- `不明`: the maintainer's approval statements and dates for the new approval items.
- `不明`: the form and location of the per-ADR review packages (compare the same open question in gov005).
- Assumption: AAL-027 is withdrawn or replaced as part of the Agent Memory JSONL decision; the memo names AAL-027 without stating its exact disposition.

## AI Implementation Instruction
Change only the files listed under Target Files or Areas. Never write an approver, a date, or an approval sentence. Do not edit generated sections by hand; run the official generator. Cite only test paths and node names that exist and pass. Do not implement production code. Stop and report if the consumer-registry model or an approval statement is needed and not provided.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261124-093927
- **Related target files**: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/10_adr/adr_01_index.md`, `docs/10_adr/adr_00_document-guide.md`, `docs/10_adr/adr_02_07_016_adr-authority-model.md`, `config/adr_authority.toml`, `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
