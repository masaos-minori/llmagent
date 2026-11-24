## Goal
- Amend ADR-006 and ADR-008, together with the Approval Ledger, `config/adr_authority.toml`, the ADR index, and the ADR document guide, so that one coherent decision model holds: `eventbus.sqlite` is the sole EventBus system of record (no `events.jsonl`), EventBus retention is state-aware and replay before the retained floor fails explicitly, ADR-008 governs six SQLite stores, Repository Context is non-persistent, and Episodic Memory (in `session.sqlite` only) is the sole persistent Agent memory. Every check named in the Issue passes, and no approver name, date, or approval sentence is written.

## Priority
High

## Scope
- **In-Scope**: ADR-006 amendment (persistence, DLQ state, retention, replay contract, capacity signals); ADR-008 amendment (title and body for six stores, matrix, Decision Details, invariants, Repository Context and Episodic Memory, removal of memory JSONL); Approval Ledger update (AAL-024 updated; AAL-026 and AAL-027 withdrawn, AAL-029 narrowed to its schema-mismatch no-loss part; three new pending entries); ADR authority configuration; ADR index and ADR document guide (display names, verification matrix rows, regenerated guarded sections); Known Deviations that record where current code differs from the amended ADRs; per-ADR review packages.
- **Out-of-Scope**: production code, database schema, route, retention-worker, CLI, test, and configuration implementation; recording any approval on behalf of the maintainer; the ADR-008 file rename (deferred, see UNK-04); EventBus, Agent, Session DB, and other `docs/` rewrites (the follow-up issues adrdoc002, adrdoc003, adrdoc004); closing the other ledger entries (issue gov005).
- **Dependencies**: Overlaps the open issue gov005 (ADR Approval Ledger work-down): this Plan updates, withdraws, or narrows AAL-024, AAL-026, AAL-027, and AAL-029, which gov005 also lists, so gov005's scope must drop them after this Plan completes (UNK-07). This Plan does not wait for gov005. Blocks the follow-up issues adrdoc002, adrdoc003, and adrdoc004 (named by id).

## Background
The Issue was filed from `memo-issue.md` (an approved redesign direction supplied by the requester). Repository evidence checked on 2026-11-24:
- ADR-006 still records a JSONL archive as a secondary audit log (Context Problem, Constraints, Failure Policy, Fallback Policy, Derived Data) and cites `test_publish_succeeds_if_jsonl_append_fails` (INV-02 evidence). `scripts/eventbus/publish_route.py` still appends to `events.jsonl` and increments `eventbus_jsonl_append_failure_total`, so the code does not yet match the target state.
- ADR-008 has the front matter title "Separating SQLite into Six Databases", the filename `adr_02_05_008_db-sqlite-4db-separation.md`, the index display name unchanged, the guide display name "SQLite 4DB Separation", and the matrix label "SQLite 4DB separation maintained". Decision Details 22 to 24, INV-02, INV-09, and the Recovery Policy Matrix still describe memory JSONL, `/memory rebuild`, and unbounded EventBus growth as an accepted risk.
- The Approval Ledger is Part 5 of `docs/00_governance/governance_03_issue-and-uncertainty-management.md`; its highest entry is AAL-038. AAL-024, AAL-026, AAL-027 (ADR-008) and AAL-029 (ADR-006) exist with `Approver` and `Date` both `Not recorded`.
- `tools/check_adr_structure.py` requires that every pending-approval bullet cites an existing ledger entry, so ADR bullets and ledger entries must change in lockstep.
- The authority model already has `eventbus.persistence` and `eventbus.network-binding` (primary ADR-006) and `db.recovery-separation` (primary ADR-008), plus `adr_edge` rows ADR-008 Governs ADR-006 and ADR-006 Reference ADR-008. All ADR checks pass on the current tree (structure, invariant matrix, authority, generator `--check`, DB separation).

## Problem
The ADR set holds mutually inconsistent decisions and labels: JSONL is described as a replica although SQLite commit alone decides publish success; unbounded EventBus growth is accepted as a risk; ADR-008 mixes six-store scope with four-database labels; ADR-008 documents the old Agent memory design; the pending ledger entries describe that obsolete design; and authority, front matter, generated sections, and the invariant matrix are mechanically linked, so prose-only edits cause drift.

## Reason for Change
Correctness and operational risk: operators and implementers can take wrong actions (rely on JSONL as a recovery source, assume unbounded replay), and approving the pending entries unchanged would make the obsolete design authoritative. The EventBus, Agent, and generated-reference documentation issues depend on these ADR decisions existing first.

## Implementation Intent
Amend the ADRs as one coordinated change set, preserving approval integrity: replace pending decisions through withdrawal and new pending entries, never silent edits and never invented approval text. ADR-006 owns EventBus persistence, delivery, replay, and retention; ADR-008 owns separation and lifecycle policy for six stores and defers EventBus retention detail to ADR-006. The ADRs state the target decision; where current code differs (JSONL append, no retention, no replay floor, old memory design) the difference is recorded as a Known Deviation and the affected invariant is marked Not verified or Partial, not cited as passing. Generated sections are changed only by the generator.

## Requirements
- `REQ-001`: ADR-006 defines `eventbus.sqlite` as the sole source of truth (events, delivery state, offsets, DLQ state, DLQ outbox, requeue lineage, retention-participant state, retention-maintenance state); states that EventBus creates no `events.jsonl`; defines publish success as SQLite commit and broker notification as a best-effort side effect that cannot roll back a commit; states that structured security audit records are operational logs and not replicas, backups, replay sources, or recovery sources; defines DLQ JSON files as derived artifacts and `events.dlq_at` plus `dlq_outbox` as authoritative DLQ state; prohibits automatic deletion of `pending` and `failed` outbox rows.
- `REQ-002`: ADR-006 defines state-aware retention: a persistent source of truth for retention participants (or records the unresolved owner decision, UNK-01); that authorization generations, connected subscribers, offsets, and delivery rows are individually insufficient; no age-only deletion; all active participants acknowledge or are decommissioned before purge; purge is blocked by incomplete DLQ processing, `pending` or `failed` outbox state, a legal hold, or required requeue lineage; an event and its dependent delivery and outbox state are purged as one referentially consistent unit; retention runs as a dedicated maintenance task separate from the DLQ repair loop; capacity signals (database size, WAL size, free disk, purge lag, retention-blocked count, oldest retained event age, last retention result) with warning versus critical behavior, critical disk shortage and retention-invariant failure making readiness false.
- `REQ-003`: ADR-006 defines `earliest_available_seq` and `latest_available_seq`, HTTP 410 with error code `replay_position_expired` for replay or subscribe positions before the retention floor, no silent consumer-offset advancement, and `since_seq=0` as the earliest retained event (scope of this redefinition: UNK-02).
- `REQ-004`: ADR-008 title becomes `ADR-008: Separation and Lifecycle Policy for Six SQLite Stores` and its Summary, Scope, body, and verification language consistently describe six stores; it identifies the four platform-domain databases and the two non-domain stores; prohibits physical-path sharing, cross-store `ATTACH`, cross-store foreign keys, and schema-qualified cross-store access; and the Recovery Policy Matrix gains authoritative data, derived data, backup, restore, schema mismatch, retention, capacity monitoring, failure mode, owner, and verification columns (rows) for all six stores, with unresolved lifecycle policies recorded as Known Deviations.
- `REQ-005`: ADR-008 defines sessions, messages, conversation state, session diagnostics, Episodic Memory events, and Episodic relations as authoritative `session.sqlite` data and Episodic FTS and Vector indexes as derived; defines configured repository files as the Repository Context source of truth (not stored in SQLite or JSONL, no persistent FTS or Vector index); defines Episodic Memory as the only persistent Agent long-term memory, generated internally with no user-facing CRUD contract, recoverable only from verified SQLite backup; removes Semantic Memory, User Semantic, memory JSONL, pin state, manual memory writes, `/memory` data, and the `/memory rebuild` precondition from the current policy.
- `REQ-006`: ADR-008 defines EventBus authoritative and derived data consistently with amended ADR-006 and removes `events.jsonl`, JSONL writers, JSONL recovery, JSONL count comparisons, and the accepted-risk wording (Decision Detail 23, INV-09) from the recovery policy matrix and invariants.
- `REQ-007`: The Approval Ledger: AAL-024 scope reads six SQLite stores; AAL-026 and AAL-027 are withdrawn (the pending change is reverted and the entry removed, per the ledger Rules) with their ADR pending bullets, and AAL-029 is narrowed to the no-loss-under-schema-mismatch statement (its retention-risk part is withdrawn, because the no-loss text stays in ADR-006 and still needs a pending entry); three new pending entries are created (Repository Context and Episodic Memory; removal of EventBus `events.jsonl`; EventBus state-aware retention and replay expiration); one review package per amended ADR is prepared; `Approver` and `Date` stay `Not recorded`.
- `REQ-008`: ADR authority: ADR-006 is the primary authority for EventBus persistence, delivery, replay, and retention; ADR-008 is the primary authority for store separation and lifecycle policy; only necessary supplemental edges between them are added in `config/adr_authority.toml`, with one primary owner per target and no cycle; ADR front matter matches the configuration; ADR-008 display names in the ADR index and document guide are updated; current-specification references to four-database separation are removed from the files in this Plan.
- `REQ-009`: Invariants are added for SQLite-only EventBus durability, absence of EventBus JSONL, safe retention, replay-floor failure, six-store separation, non-persistent Repository Context, SQLite-only Episodic Memory, and absence of both JSONL memory paths; Automated Tests tables and the ADR index verification matrix cite only real test paths and node names, and mark unverifiable items Manual, Partial, or Not verified with cadence and expected evidence; each place where current code differs from the amended text is recorded under Known Deviations.
- `REQ-010`: Guarded ADR index sections are regenerated with `tools/generate_adr_authority.py` and never edited by hand; `tools/check_adr_structure.py`, `tools/check_adr_authority.py`, `tools/check_adr_reference.py`, `tools/check_adr_preservation.py`, `tools/check_adr_invariant_matrix.py`, the DB-separation verification cited by ADR-008, and the EventBus tests cited by ADR-006 pass or have their expected findings reported (UNK-06); every blocking invariant cites a real passing automated test.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Modify: EventBus persistence, DLQ state, retention, replay contract, invariants, verification, Known Deviations, pending-approval bullets | Remove the JSONL archive decisions (Context, Constraints, Failure Policy, Fallback Policy, Data Ownership) and INV-02 JSONL evidence; add retention, replay-floor, and capacity decisions and invariants; narrow the AAL-029 bullet to its no-loss part and add bullets for the new entries; record code divergence as Known Deviations (currently `Not applicable`) | REQ-001, REQ-002, REQ-003, REQ-009; AC-01, AC-02, AC-07 | Lines 46, 52, 211, 220, 225, 252 mention the JSONL archive (checked in Step 3); `Replay Contract` section and `Known Deviations: Not applicable` present (checked in Step 3); `scripts/eventbus/publish_route.py` lines 26-97 still write `events.jsonl` (checked in Step 3) | `tests/eventbus/test_eventbus_publish.py`, `tests/eventbus/test_eventbus_publish_contract.py`, `tests/eventbus/test_eventbus_replay_subscribe.py`, `tests/eventbus/test_eventbus_replay_pagination.py` (existing; no new test in scope) | Verified |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Modify: title and body for six stores, Recovery Policy Matrix, Decision Details 2, 4, 22, 23, 24, invariants INV-02, INV-04, INV-09 and new ones, verification, Known Deviations, pending-approval bullets (file name stays) | Align title and verification language with six stores; add lifecycle columns; replace memory design with Repository Context and Episodic Memory; remove memory JSONL, `/memory rebuild`, and the unbounded-growth accepted risk; remove the SHARED-002 `memories_vec` wording that no longer applies; replace the AAL-026 and AAL-027 bullets, update AAL-024 | REQ-004, REQ-005, REQ-006, REQ-009; AC-03, AC-04, AC-05, AC-07 | Front matter title already "Six Databases", file name `4db` (checked in Step 2); Matrix lines 88, 89, 106, 107 and Decision Details 22-24 name memory JSONL, `/memory rebuild`, and accepted growth risk (checked in Step 2); bullets for AAL-024, AAL-026, AAL-027 at Approval Record lines 390-393 (checked in Step 2) | `tests/tools/test_check_db_separation.py`, `tests/db/test_create_schema.py`, `tests/db/test_db_recovery.py` (existing) | Verified |
| `docs/10_adr/adr_01_index.md` | Modify: ADR-008 display name, verification matrix rows and pipeline summary for the amended invariants; regenerate guarded sections (generator only) | Rename "SQLite 4DB separation maintained" matrix label and the ADR-008 index row title; update or add rows for amended ADR-006 and ADR-008 invariants with real citations; refresh generated sections | REQ-008, REQ-009, REQ-010; AC-03, AC-06, AC-07 | ADR-008 row at line 54, matrix rows at lines 203-212, guarded blocks at lines 72-91, 101-134, 140-153 (checked in Step 3) | `tests/tools/test_check_adr_invariant_matrix.py`, `tests/tools/test_generate_adr_authority.py`, `tests/tools/test_run_cited_adr_tests.py` | Verified |
| `docs/10_adr/adr_00_document-guide.md` | Modify: ADR-008 display name in the reading-order table | Replace the "SQLite 4DB Separation" display name; the guide front matter lists the same file name, which stays | REQ-008; AC-03 | Line 37 reads `SQLite 4DB Separation` (checked in Step 3) | `tests/tools/test_check_adr_reference.py` | Verified |
| `config/adr_authority.toml` | Modify: add only necessary supplemental authority edges between ADR-006 and ADR-008 | Record ADR-008 as a limited supplemental authority on `eventbus.persistence` (separation and lifecycle policy of `eventbus.sqlite`) and ADR-006 on `db.recovery-separation` (EventBus retention and replay-floor semantics), if the checkers confirm they are necessary | REQ-008; AC-06 | `eventbus.persistence` and `db.recovery-separation` entries and the ADR-008 Governs ADR-006 and ADR-006 Reference ADR-008 edges exist (checked in Step 3); `tools/check_adr_authority.py` passes before the change (checked in Step 3) | `tests/tools/test_adr_authority.py`, `tests/tools/test_generate_adr_authority.py` | Verified |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Modify: Part 5 Approval Ledger (update AAL-024, narrow AAL-029, remove AAL-026 and AAL-027, add three entries) and the SHARED-002 Known Issue in Part 1 | Withdraw or replace pending decisions through ledger Rules; create the new pending items with `Approver` and `Date` `Not recorded`; close or update SHARED-002 because the `memories_vec` classification no longer exists in the amended design | REQ-007; AC-04 | Entries AAL-024, AAL-026, AAL-027, AAL-029 at lines 555-610, highest ID AAL-038, Rules at lines 358-362; SHARED-002 at line 194 (checked in Step 3) | `tests/tools/test_check_adr_structure.py` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Authority model and amendment precedent; it names ADR-008 only as an example and needs no change (checked in Step 3) | REQ-008 |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | ADR-013 owns authentication; retention and replay-floor decisions must not contradict it | REQ-002, REQ-003 |
| `docs/00_governance/governance_01_documentation-policy.md` | ADR Acceptance Evidence Standard and amendment rules | REQ-007 |
| `docs/00_governance/governance_02_documentation-metadata.md` | Metadata and status vocabulary for the edited documents | REQ-009 |
| `tools/check_adr_structure.py` | Pending-approval bullet and ledger citation rules | REQ-007, REQ-010 |
| `tools/check_adr_preservation.py` | Rules that report errors on intended invariant changes (UNK-06) | REQ-010 |
| `tools/check_adr_invariant_matrix.py` | Matrix and cited-test rules | REQ-009, REQ-010 |
| `tools/check_adr_authority.py` | Authority uniqueness and cycle rules | REQ-008, REQ-010 |
| `tools/check_adr_reference.py` | Front matter `related` and `adr_edge` consistency | REQ-008, REQ-010 |
| `tools/generate_adr_authority.py` | Generator of the guarded index sections | REQ-010 |
| `tools/_adr_authority_core.py` | Shared authority-model logic | REQ-008 |
| `tools/check_db_separation.py` | DB-separation check cited by ADR-008 | REQ-004, REQ-010 |
| `tests/tools/test_check_db_separation.py` | ADR-008 cited tests | REQ-009, REQ-010 |
| `scripts/eventbus/publish_route.py` | Current JSONL append behavior, for Known Deviations | REQ-001, REQ-009 |
| `scripts/eventbus/replay_route.py` | Current replay contract, for Known Deviations | REQ-003, REQ-009 |
| `scripts/eventbus/subscribe_route.py` | Current subscribe start-position behavior | REQ-003 |
| `scripts/eventbus/schema.sql` | Current EventBus tables (events, consumer_delivery, consumer_offsets, dlq_outbox) | REQ-001, REQ-002 |
| `config/eventbus.toml` | Confirms no retention or capacity keys are defined today | REQ-002, REQ-009 |
| `.github/run_cited_adr_tests.py` | CI runner for the cited ADR tests | REQ-010 |

## Acceptance Criteria
- `AC-01` (REQ-001, REQ-002): ADR-006 contains no current decision requiring EventBus `events.jsonl` and defines a state-aware retention model.
- `AC-02` (REQ-003): ADR-006 defines explicit replay expiration (`earliest_available_seq`, `latest_available_seq`, HTTP 410 `replay_position_expired`, no silent offset advancement).
- `AC-03` (REQ-004, REQ-008): ADR-008 describes six SQLite stores consistently in its title, body, index entry, document-guide entry, and verification scope.
- `AC-04` (REQ-005, REQ-006, REQ-007): ADR-008 describes Repository Context and Episodic Memory as designed; neither memory JSONL nor EventBus JSONL appears as a current recovery source; old ledger decisions are withdrawn or replaced rather than silently changed; no approver name, date, or approval sentence is fabricated.
- `AC-05` (REQ-005, REQ-006): the Recovery Policy Matrix has authoritative data, derived data, backup, restore, schema mismatch, retention, capacity monitoring, failure mode, owner, and verification entries for all six stores, with undecided policies recorded as Known Deviations.
- `AC-06` (REQ-008, REQ-010): ADR authority has one primary owner per target and no cycle; generated index sections match the authority configuration.
- `AC-07` (REQ-009, REQ-010): `check_adr_structure`, `check_adr_authority`, `check_adr_reference`, `check_adr_invariant_matrix` pass, `check_adr_preservation` reports only the expected, intentional findings, and every blocking invariant cites a real passing automated test.

## Tests
- `REQ-001` to `REQ-003`: no new automated test (test implementation is out of scope); the existing EventBus tests cited by ADR-006 still pass, and new invariants whose behavior is not implemented are recorded as Not verified. Evidence is the ADR text plus the ADR checkers.
- `REQ-004` to `REQ-006`: `tools/check_db_separation.py` and `tests/tools/test_check_db_separation.py` pass unchanged (four platform-domain databases and two non-domain stores remain distinct).
- `REQ-007`: `tools/check_adr_structure.py` confirms every pending bullet cites an existing entry and every ledger entry has a heading.
- `REQ-008`, `REQ-010`: `tools/check_adr_authority.py`, `tools/check_adr_reference.py`, `uv run python tools/generate_adr_authority.py --check`.
- `REQ-009`: `tools/check_adr_invariant_matrix.py` and `.github/run_cited_adr_tests.py` (cited tests exist and pass).

## Documentation Impact
Yes. The files under `Implementation Target Files` are the documentation. They record intent, boundaries, constraints, failure behavior, retention and capacity behavior, Known Deviations (code differs from the amended decisions), and Needs Confirmation items. Other `docs/` files that mention the retired model (EventBus, Agent, DB, deployment, shared, RAG documents) are updated by the follow-up issues adrdoc002, adrdoc003, and adrdoc004 via `docs/00_index.md` "Document References by Task".

## Assumptions
- The ADRs state the approved target design; current code is unchanged by this Plan, so each divergence is a Known Deviation, not a claim that the behavior exists.
- New pending approval items take the next ledger IDs after AAL-038: AAL-039 (Repository Context and Episodic Memory, ADR-008), AAL-040 (removal of EventBus `events.jsonl`, ADR-006), AAL-041 (state-aware retention and replay expiration, ADR-006). The AAL-018 gap is not reused.
- Withdrawing a pending decision means reverting its text in the ADR and removing the ledger entry, which is the ledger's own closing rule for a reverted change; this is not an approval.
- AAL-029 covers two statements: the no-loss claims under the ADR-008 schema-mismatch rule (ADR-006 Summary, Decision Detail 9, INV-07, Rationale, Consequences) and the accepted retention risk (ADR-006 Data Ownership Deletion Rule). Only the retention part is withdrawn; the no-loss text stays and keeps a narrowed AAL-029 entry (found in plan-to-implementation-procedure Step 3a, corrected here).
- The next free invariant numbers are ADR-006 INV-17 and ADR-008 INV-19 (current maxima INV-16 and INV-18); existing invariant numbers are not renumbered.
- The ADR-008 file rename is deferred (UNK-04); the title, content, index entry, and guide display name are aligned now, and the file name and the `related` lists that cite it stay unchanged.
- No runtime component reads `config/adr_authority.toml` (no match in `scripts/` or `deploy/`, checked in Step 5), so no production deployment is needed.
- The review packages are delivered in the implementation report, not as a repository file, until the maintainer decides otherwise (UNK-05).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | The persistent source of truth for retention participants (a consumer registry model) is not approved | No approved registry model in ADRs, schema, or config | Maintainer decision; until then ADR-006 records the open owner decision (the Issue permits this) | False |
| UNK-02 | Scope of "`since_seq=0` means the earliest retained event": the current Replay Contract says `since_seq=0` is unspecified for `/subscribe` and records an open decision on replay from the start | Maintainer decision on `/subscribe`; AAL-037 covers the related delivery-guarantee text | Apply the redefinition to the `/replay` lower bound and keep the `/subscribe` open decision recorded until the maintainer decides | False |
| UNK-03 | Disposition of AAL-025 text: Decision Detail 22 and the Matrix schema-mismatch row name `/memory rebuild` and the JSONL archive, which this Plan removes, and the Issue does not name AAL-025 | Maintainer statement on whether AAL-025 is amended in place | Remove only the JSONL and `/memory rebuild` wording and update AAL-025's Decision text; record the change in the review package | False |
| UNK-04 | Whether the ADR-008 file rename can be done atomically: 18 files outside `issues/`, `plans/`, and `implementations/` cite the old name, including `tools/check_adr_preservation.py`, `tools/check_db_separation.py`, `tools/check_docs_structure.py`, and two baseline files under `tools/` | A decision to include tool and baseline edits, which are out of this Plan's documentation-only scope | File a follow-up issue for the rename after this Plan; the Issue allows deferral | False |
| UNK-05 | Form and location of the per-ADR review packages (gov005 raises the same question) | Maintainer decision | Deliver in the implementation report; relocate on the maintainer's instruction | False |
| UNK-06 | `tools/check_adr_preservation.py` reports ERROR on changed invariants, Approval, and H2 sequence by design (it guards size reductions), so it cannot report a clean pass on an intended amendment | How the repository records an amendment outcome for this check | Run it with `--base` against the pre-amendment commit, report each ERROR as an intended change in the review package, and treat a clean run against the new `HEAD` after the commit as the pass | False |
| UNK-07 | Overlap with the open issue gov005 (`issues/20261123-104604_gov005_adr-approval-ledger.md`), which lists AAL-024, AAL-026, AAL-027, and AAL-029 | gov005 has not been updated for this Plan | After this Plan completes, gov005's scope drops those entries or is re-verified; this Plan does not edit gov005 | False |
| UNK-08 | The approver and date for each new and updated ledger entry | Maintainer statement | Leave `Not recorded`; never write them (ledger Rules) | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Modify | Medium (checked by ADR checkers; cited by ADR-008, ADR-013, EventBus docs) | 17 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Modify | High (cited by 18 files, tools, and docs; file name unchanged) | 17 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/10_adr/adr_01_index.md` | Modify | Medium (generated sections, matrix, cited-test runner) | 24 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/10_adr/adr_00_document-guide.md` | Modify | Low | 7 | 2 authors in 365 days | not applicable (rsynced) |
| `config/adr_authority.toml` | Modify | Medium (authority checkers and generator) | 9 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Modify | Medium (ledger consumed by `tools/check_adr_structure.py`) | 23 | 2 authors in 365 days | not applicable (rsynced) |

## Design
Classification: Path B (six target files, more than three; the amended ADR-008 is a public contract for the database layer).

Architecture and dependency analysis (docs and governance tooling only; no Python target):
- Cross-checkers couple the files: `check_adr_structure.py` (pending bullet to ledger entry, both directions of citation), `check_adr_invariant_matrix.py` and `.github/run_cited_adr_tests.py` (index matrix to ADR invariants and tests), `check_adr_reference.py` (front matter `related` to `adr_edge`), `check_adr_authority.py` and `generate_adr_authority.py --check` (authority configuration to guarded index blocks). The edits therefore land together (release unit below).
- Authority: `eventbus.persistence` stays ADR-006; `db.recovery-separation` stays ADR-008. Adding limited supplemental entries (ADR-008 on `eventbus.persistence`: separation and lifecycle of `eventbus.sqlite`; ADR-006 on `db.recovery-separation`: EventBus retention and replay-floor semantics) keeps one primary per target; the `adr_edge` rows ADR-008 Governs ADR-006 and ADR-006 Reference ADR-008 already cover the graph, so no new `adr_edge` row is planned. If a checker shows the supplemental entries are redundant, the row is reduced by an approved Plan amendment (R-05).
- Decision text: ADR-006 retention uses a persisted retention-participant set, never event age alone, and the purge unit is the event plus its `consumer_delivery` and `dlq_outbox` rows. ADR-008's matrix retention cell for `eventbus.sqlite` points to ADR-006 for detail, so retention is defined once.
- Consumer scan and predictable fallout check: no persisted schema, public API, or code symbol changes, so `tools/scan_change_consumers.py` is not applicable. Fallout candidates: pinned counts and cited-test totals — the ADR-cited test runner reads the index matrix, and `tests/tools/test_run_cited_adr_tests.py` tests only the runner's pure functions (no pinned total found, checked in Step 3), so `not affected`; tool inventory and module size: `not affected` (no tool is added); generated blocks: the three guarded sections of `docs/10_adr/adr_01_index.md` are regenerated (target row 3).
- Files outside this Plan that cite the retired model (`docs/24_eventbus/`, `docs/23_agent/`, `docs/41_db/`, `docs/90_deployment/`, `docs/40_shared/`, `docs/21_rag/`, and `tools/` references to the ADR-008 file name) are `not affected` here and handled by adrdoc002, adrdoc003, adrdoc004, and the rename follow-up.
- Operational check: no database is touched; no process lock check applies (not run, documentation only). Persisted schema check (`rules/persisted-schema-change.md`): not applicable, no DDL, schema version, or migration is changed.

Decisions:
- Ledger ordering: add the new entries first, replace the ADR pending bullets, then remove the withdrawn entries, so each cross-check has a consistent state.
- Where the amended text prescribes behavior the code does not implement (no `events.jsonl`, retention task, replay floor, health fields, Episodic-only memory), the ADR records a Known Deviation and marks the invariant Not verified instead of citing a passing test.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above. All steps edit documentation or configuration text only.

1. **Phase 1: Approval Ledger and review packages**
   - [ ] Add AAL-039, AAL-040, AAL-041 entries (all six fields, `Approver` and `Date` `Not recorded`) and update the AAL-024 Decision and Scope text to six SQLite stores; keep AAL-026, AAL-027, and the current AAL-029 text until their ADR bullets are replaced (REQ-007; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`)
   - [ ] Draft one review package per amended ADR (old decision, proposed decision, rationale, affected documents, expected implementation impact, removed behavior, new invariants, verification expectations) for the implementation report (REQ-007)
2. **Phase 2: ADR-006 amendment**
   - [ ] Rewrite Context, Constraints, Decision Details, Failure Policy, Fallback Policy, and Data Ownership for SQLite-only persistence, derived DLQ files, and audit-log separation (REQ-001; `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`)
   - [ ] Add the retention, replay-floor, and capacity decisions and invariants INV-17 onward, update the Replay Contract, and keep UNK-01 and UNK-02 as recorded open decisions (REQ-002, REQ-003, REQ-009; same file)
   - [ ] Update Automated Tests and Manual Review rows with real tests only, mark unimplemented behavior Not verified, narrow the AAL-029 pending bullet to the no-loss claim and add bullets citing AAL-040 and AAL-041, and record Known Deviations for current code (REQ-001, REQ-009; same file)
3. **Phase 3: ADR-008 amendment**
   - [ ] Align the title, Summary, Scope, and verification wording with six stores; add the store-separation prohibitions and the lifecycle matrix columns (REQ-004; `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`)
   - [ ] Rewrite Decision Details 2, 4, 22, 23, 24 and INV-02, INV-04, INV-09 for Repository Context, Episodic Memory, and ADR-006 retention; remove memory JSONL, `/memory rebuild`, and the accepted-growth risk; add invariants INV-19 onward (REQ-005, REQ-006, REQ-009; same file)
   - [ ] Replace the AAL-026 and AAL-027 pending bullets with a bullet citing AAL-039, keep the AAL-024 bullet, update Known Deviations including SHARED-002, and record unresolved lifecycle policies as Known Deviations (REQ-004, REQ-007; same file)
4. **Phase 4: Withdraw replaced ledger entries**
   - [ ] Remove AAL-026 and AAL-027 and narrow AAL-029 (Decision and Scope: no-loss statements under the ADR-008 schema-mismatch rule only) in Part 5 and update or close SHARED-002 in Part 1, after confirming no ADR bullet still cites them (REQ-007; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`)
5. **Phase 5: Authority, index, and guide**
   - [ ] Add the necessary supplemental authority entries (REQ-008; `config/adr_authority.toml`)
   - [ ] Update the ADR-008 display name and matrix label, add or update ADR-006 and ADR-008 matrix rows and the pipeline summary; do not touch guarded blocks (REQ-008, REQ-009; `docs/10_adr/adr_01_index.md`)
   - [ ] Update the ADR-008 display name in the reading-order table (REQ-008; `docs/10_adr/adr_00_document-guide.md`)
   - [ ] Run `uv run python tools/generate_adr_authority.py` to regenerate the guarded sections (REQ-010; `docs/10_adr/adr_01_index.md`)
6. **Phase 6: Validation and deployment check**
   - [ ] Run the checkers and tests in the Validation plan, report intended `check_adr_preservation.py` findings, and compile the review packages (REQ-010; all target files)
   - [ ] Deployment hand-off: `config/adr_authority.toml` changes, but no runtime consumer exists, so no production deployment is required; if the user wants one, commit and push first and then follow `skills/deploy/SKILL.md` (it has an approval gate) (REQ-008; `config/adr_authority.toml`)

### Release units
**Unit**: adr-amendment | **Phases**: 1, 2, 3, 4, 5 | **Reason**: `check_adr_structure.py` checks pending bullets and ledger entries in both directions, `check_adr_invariant_matrix.py` and `check_adr_reference.py` check the index and authority data against the ADR text, and `generate_adr_authority.py --check` checks the guarded blocks, so no phase of this group passes the checkers alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | ADR structure and Known Deviations checks | `uv run python tools/check_adr_structure.py` | No findings |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Intended-change report (UNK-06) | `uv run python tools/check_adr_preservation.py --base HEAD` before commit | Only the intended invariant, Approval, and heading findings, each listed in the review package |
| `docs/10_adr/adr_01_index.md` | Matrix and cited-test checks | `uv run python tools/check_adr_invariant_matrix.py` and `uv run python .github/run_cited_adr_tests.py` | No findings; cited tests exist and pass |
| `config/adr_authority.toml` | Authority and reference checks | `uv run python tools/check_adr_authority.py`, `uv run python tools/check_adr_reference.py` | No findings, one primary per target, no cycle |
| `docs/10_adr/adr_01_index.md` | Generated block drift | `uv run python tools/generate_adr_authority.py --check` and `uv run python tools/generate_reference_table.py --check` | No drift |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | DB-separation static check and tests | `uv run python tools/check_db_separation.py`, `uv run pytest tests/tools/test_check_db_separation.py -q` | Pass |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | EventBus tests cited by ADR-006 | `uv run pytest tests/eventbus/test_eventbus_publish.py tests/eventbus/test_eventbus_publish_contract.py tests/eventbus/test_eventbus_replay_subscribe.py -q` | Pass |
| All target files | Pre-commit and gates | `uv run python tools/run_validation_gates.py` | No `Fail` or `Blocked` |

## Risks
- **Risk**: The amended ADRs describe behavior the code does not implement (JSONL still written, no retention, no replay floor), so a reader may take the ADR as current behavior → **Mitigation**: Known Deviations in ADR-006 and ADR-008, Not verified invariant rows, and no citation of unimplemented tests.
- **Risk**: Other current specifications (EventBus, Agent, DB, deployment documents) still describe the old model until adrdoc002, adrdoc003, and adrdoc004 land, so documents disagree for a period → **Mitigation**: those issues depend on this Plan and are filed; the review package lists the affected documents.
- **Risk**: The pending bullets and ledger entries drift apart and `check_adr_structure.py` fails → **Mitigation**: lockstep ordering in Phases 1 to 4 and the release unit; run the checker before commit.
- **Risk**: High churn (17 to 24 commits in 30 days) on the target files causes merge conflicts with parallel sessions → **Mitigation**: keep the edits scoped, run the sync step of `git-commit-and-sync` immediately before the commit, and re-check the structure checker after any rebase.
- **Risk**: The supplemental authority entries are redundant or create a second owner for retention → **Mitigation**: define retention only in ADR-006 and have ADR-008 refer to it; if a checker rejects the entries, amend the Plan row through the Plan Amendment Approval Classes.
- **Risk**: Withdrawing AAL-026 and AAL-027 and narrowing AAL-029 collides with gov005, which still lists them → **Mitigation**: UNK-07; gov005 is re-scoped after this Plan completes.
- **Risk**: An approval name, date, or sentence is written by mistake → **Mitigation**: the ledger Rules and a final search of the diff for `Approver` and `Date` values other than `Not recorded`.
- **Risk**: The 18-file reference set to the ADR-008 file name (blast radius of a rename, outside the work-item directories) → **Mitigation**: the rename stays out of this Plan (UNK-04).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Approval Ledger: add AAL-039 to AAL-041, update AAL-024, draft review packages | Completed | — | 20261124-100821 |  |
| 2 | ADR-006 amendment: SQLite-only persistence, retention, replay contract, invariants, Known Deviations | Completed | — | 20261124-100821 |  |
| 3 | ADR-008 amendment: six stores, Repository Context, Episodic Memory, lifecycle matrix, invariants | Completed | — | 20261124-100821 |  |
| 4 | Withdraw AAL-026 and AAL-027, narrow AAL-029, and settle SHARED-002 | Completed | — | 20261124-100821 |  |
| 5 | Authority configuration, ADR index, document guide, regenerate guarded sections | Completed | — | 20261124-100821 |  |
| 6 | Validation, intended-change report, deployment check | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261124-094801_01_docs_10_adr_adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261124-094801_02_docs_10_adr_adr_02_05_008_db-sqlite-4db-separation.md.md | 3 | Procedure | Completed | — | — |
| implementations/20261124-094801_03_docs_10_adr_adr_01_index.md.md | 5 | Procedure | Completed | — | — |
| implementations/20261124-094801_04_docs_10_adr_adr_00_document-guide.md.md | 5 | Procedure | Completed | — | — |
| implementations/20261124-094801_05_config_adr_authority.toml.md | 5 | Procedure | Completed | — | — |
| implementations/20261124-094801_06_docs_00_governance_governance_03_issue-and-uncertainty-management.md.md | 1, 4 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261124-093927_adrdoc001_adr-eventbus-memory-amendment.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261124-094324
- **Related target files**: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/10_adr/adr_01_index.md`, `docs/10_adr/adr_00_document-guide.md`, `config/adr_authority.toml`, `docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes B; ADR-006 lines 46-52, 211-225 | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Phase 2 | AC-01 | `tools/check_adr_structure.py`; ADR-006 cited tests | Confirmed by repository evidence |
| REQ-002 | Required Changes B; Reason for change 2 | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Phase 2 | AC-01 | `tools/check_adr_structure.py` | Needs confirmation (UNK-01) |
| REQ-003 | Required Changes B; ADR-006 Replay Contract | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Phase 2 | AC-02 | `tools/check_adr_structure.py` | Needs confirmation (UNK-02) |
| REQ-004 | Required Changes C; ADR-008 front matter and file name | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Phase 3 | AC-03, AC-05 | `tools/check_db_separation.py`; `tools/check_adr_structure.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes C; ADR-008 Matrix and Decision Details 22-24 | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Phase 3 | AC-04, AC-05 | `tools/check_adr_structure.py` | Needs confirmation (UNK-03) |
| REQ-006 | Required Changes C; ADR-008 Decision Detail 23, INV-09 | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Phase 3 | AC-04, AC-05 | `tools/check_adr_structure.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes A; governance_03 Part 5 Rules | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Phase 1, Phase 4 | AC-04 | `tools/check_adr_structure.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes A; ADR pending bullets | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Phase 2 | AC-04 | `tools/check_adr_structure.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes A; ADR pending bullets | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Phase 3 | AC-04 | `tools/check_adr_structure.py` | Confirmed by repository evidence |
| REQ-008 | Required Changes D; adr_authority.toml entries | `config/adr_authority.toml` | Phase 5 | AC-03, AC-06 | `tools/check_adr_authority.py`; `tools/check_adr_reference.py` | Derived from confirmed evidence |
| REQ-008 | Required Changes D; index and guide display names | `docs/10_adr/adr_01_index.md` | Phase 5 | AC-03, AC-06 | `tools/generate_adr_authority.py --check` | Confirmed by repository evidence |
| REQ-008 | Required Changes D; guide line 37 | `docs/10_adr/adr_00_document-guide.md` | Phase 5 | AC-03 | `tools/check_adr_reference.py` | Confirmed by repository evidence |
| REQ-009 | Required Changes D; verification matrix | `docs/10_adr/adr_01_index.md` | Phase 5 | AC-07 | `tools/check_adr_invariant_matrix.py`; `.github/run_cited_adr_tests.py` | Derived from confirmed evidence |
| REQ-009 | Required Changes D; Known Deviations | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Phase 2 | AC-07 | `tools/check_adr_structure.py` | Derived from confirmed evidence |
| REQ-009 | Required Changes D; Known Deviations | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Phase 3 | AC-07 | `tools/check_adr_structure.py` | Derived from confirmed evidence |
| REQ-010 | Required Validation; Acceptance Criteria | `docs/10_adr/adr_01_index.md` | Phase 5, Phase 6 | AC-06, AC-07 | `tools/generate_adr_authority.py --check`; the Validation plan commands | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261124-094801 -->
