## Goal
- Rewrite the nine affected EventBus documents under `docs/24_eventbus/` so they describe the amended ADR-006 model consistently: `eventbus.sqlite` is the only event source of truth (no `events.jsonl`), structured security audit logs are separate operational logs, DLQ JSON files are SQLite-derived artifacts, retention is state-aware and bounded, replay before the retained floor fails with HTTP 410, and database, WAL, disk, artifact, audit-log, and archive growth each have bounded-growth guidance. Where code does not yet implement the model, each statement points to the Known Issue that tracks the difference, and no configuration key, response field, or threshold is invented.

## Priority
High

## Scope
- **In-Scope**: the document guide, system overview, publish-and-subscribe, DLQ and delivery semantics, persistence and replay, configuration and operations, publish durability, health endpoint, and replay endpoint documents; removal of `events.jsonl`, JSONL append, JSONL count comparison, and unsafe manual deletion SQL from current guidance; documentation of retention participants, purge predicates and blockers, purge unit, dedicated retention task, replay floor and HTTP 410, DLQ artifact and archive lifecycle, capacity and health signals, and backup and archive retention requirements.
- **Out-of-Scope**: ADR changes (done by the amendment plan for adrdoc001); implementation of retention, health fields, the replay floor, or configuration keys; Agent and Session DB documents (the follow-up issue adrdoc003); regeneration of repository-wide references and the terminology sweep (the follow-up issue adrdoc004); the API manifest and the generated block of the reference document (derived from `scripts/eventbus/*.py`, which this Plan does not change).
- **Dependencies**: Depends on the ADR-006 and ADR-008 amendment (adrdoc001), which is complete and archived, so it needs no ordering bullet. Blocks the follow-up issue adrdoc004 (named by id). No open Plan or Issue overlaps the nine documents.

## Background
The Issue was filed from `memo-issue.md`. The ADR-006 amendment (Decision Details 15 to 20, the Replay Contract additions, INV-17 to INV-22) is committed, and its Known Deviations cite the Known Issues EVENTBUS-001 (code still appends `events.jsonl`) and EVENTBUS-002 (no retention task, purge, capacity signal, replay floor, or HTTP 410; the retention-participant registry is unapproved). Repository evidence checked on 2026-11-24:
- The thirteen files `eventbus_00` to `eventbus_12` exist under `docs/24_eventbus/`. JSONL appears in four of them: `eventbus_05` (JSONL Archive Retention, Reliability Limits), `eventbus_06` (JSONL Archive section, append guard, SQLite/JSONL Consistency Check procedure), `eventbus_03` (JSONL Append Failure paragraph and Failure Behavior Summary row), and `eventbus_09` (Canonical Store, publish flow, JSONL Append Failure scenario, Recovery Procedure, Metrics).
- `eventbus_05` Retention documents manual SQL (`DELETE FROM events ... ` after `DELETE FROM dlq_outbox`) that leaves `consumer_delivery` rows as orphans, and states that no automatic cleanup exists.
- `scripts/eventbus/publish_route.py` still appends `events.jsonl` and increments `eventbus_jsonl_append_failure_total`; `config/eventbus.toml` and `scripts/eventbus/config.py` hold no retention or capacity key; `scripts/eventbus/health_route.py` reports no database size, WAL size, disk, or retention field; no replay-floor check or HTTP 410 exists in `replay_route.py` or `subscribe_route.py`.
- `events` has one timestamp column, `published_at`, which is publisher-supplied (`event_repo.py`, `publish_route.py`); no EventBus-generated receive time is stored. EventBus-generated timestamps (`now_iso()` in `json_utils.py`) exist only on `dlq_at`, `dlq_outbox`, and requeue fields.
- `registry/manifests/eventbus_api.yaml` is generated from the public classes and functions of `scripts/eventbus/*.py` (`tools/generate_reference_table.py`, `_api_manifest_entries("eventbus")`), and `registry/manifests/health_contracts.yaml` from `scripts/shared/security/posture_contract.py`; neither is an EventBus documentation input that needs editing while the code is unchanged.
- `uv run python tools/check_docs_consistency.py --domain eventbus` and `tools/check_needs_confirmation_inventory.py` pass on the current tree.

## Problem
The EventBus documentation describes the retired model: `events.jsonl` as an event replica that can permanently diverge from SQLite, JSONL append-failure and count-comparison procedures, no retention, orphan-prone manual deletion SQL, `since_seq=0` as complete replay, and no retention-participant, decommission, replay-floor, archive-cleanup, or capacity guidance. The lifecycles of active DLQ artifacts, `requeued/` artifacts, verified database archives, and audit logs are not separated.

## Reason for Change
Operators can keep using unsafe manual SQL, assume JSONL is a recoverable replica, or expect data older than the retention floor to stay replayable, even though the ADRs are corrected (wrong-action risk). The ADR amendment is complete, so this work can proceed now.

## Implementation Intent
Present one operational model: SQLite is the only source of truth; audit records are separate logs; DLQ JSON files are derived; retention is controlled by persisted state and explicit predicates, in bounded batches, referentially consistent; replay expiration is explicit and fail-closed; every store of data has a bounded-growth rule; health output separates warnings from readiness failures. The documents state the contract from ADR-006 and cite EVENTBUS-001 or EVENTBUS-002 for each point the code does not yet meet. Documentation edits introduce no Needs Confirmation marker: an open point is recorded by citing a Known Issue, because unregistered markers fail the inventory check.

## Requirements
- `REQ-001`: The document guide routes to the revised persistence, retention, replay, health, and operations documents, and the system overview states that `eventbus.sqlite` is the only EventBus system of record, distinguishes structured security audit logs from event persistence, describes DLQ JSON files as SQLite-derived artifacts, and shows no `events.jsonl` in any diagram, data flow, recovery description, or storage inventory.
- `REQ-002`: Persistence and publish durability documents remove JSONL append steps, failure scenarios, metrics, the SQLite/JSONL count comparison, and JSONL repair; define a successful SQLite commit as publish success; keep duplicate and conflict behavior and best-effort broker notification; and state the retention timestamp rule (an EventBus-generated timestamp, never the publisher-supplied `published_at`), noting that no such column exists yet (EVENTBUS-002).
- `REQ-003`: Operations documents replace the manual deletion SQL with the retention model: retention participants and explicit decommission, why authorization TTL expiry, connections, offsets, and delivery rows are individually insufficient, purge eligibility predicates, purge-blocking states, purge ordering and referential-integrity expectations, batch size, per-cycle limit, scheduling, shutdown behavior, and a dedicated task separate from the DLQ repair loop, each marked as not yet implemented where applicable (EVENTBUS-002).
- `REQ-004`: Replay and subscribe documents state `earliest_available_seq` and `latest_available_seq`, HTTP 410 `replay_position_expired` for `/replay` and `/subscribe` resume, that consumer offsets are never advanced silently to the floor, and that `since_seq=0` on `/replay` means the earliest retained event while the `/subscribe` start-position order stays as documented.
- `REQ-005`: DLQ documents state `events.dlq_at` and `dlq_outbox` as authoritative DLQ state, the retention behavior of `pending`, `done`, and `failed` outbox rows, recovery and reconciliation of missing artifacts from SQLite, retention of active and `requeued/` artifacts, handling of orphan, mismatched, and temporary files, and where archive or deletion outcomes are recorded.
- `REQ-006`: The health and operations documents describe database size, WAL size, archive size, DLQ artifact size, audit-log size, and free-disk measurements; event count, purge-eligible count, retention-blocked count, oldest retained event age, purge lag, last retention run, last result, and last deleted count; warning and critical levels; readiness behavior for critical disk shortage and retention-state inconsistency; and a retention health state separate from the DLQ task and authorization sweep. Fields and thresholds that do not exist are stated as undefined (EVENTBUS-002).
- `REQ-007`: The operations documents describe SQLite Online Backup API use where applicable, retention of verified database archives by generation, age, and total size, a minimum number of verified recovery generations, protection of the latest verified recovery candidate, and WAL checkpoint requirements around retention and shutdown, with the values left undefined where no ADR or code defines them.
- `REQ-008`: Configuration, API, and generated-reference content: only keys and fields that exist in the implementation are documented as existing; retention and capacity keys are stated as not defined (EVENTBUS-002); the replay and subscribe documents carry the HTTP 410 response and the health document the retention and capacity signals; the API manifest and the generated block stay unchanged because the code is unchanged.
- `REQ-009`: The edited documents pass the repository documentation checks, no `eventbus_*` link or path reference is broken, and no current EventBus document describes `events.jsonl` as a replica, backup, recovery source, or audit ledger.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/24_eventbus/eventbus_00_document-guide.md` | Modify: Reading Order and AI Query Routing | Route retention, replay-floor, capacity, and archive questions to the revised documents and keep the canonical-source list current | REQ-001; AC-01 | Reading-order and routing tables list no retention or capacity topic (checked in Step 3) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/24_eventbus/eventbus_01_system-overview.md` | Modify: Architecture and Purpose text | State `eventbus.sqlite` as the only system of record, separate audit logs from event persistence, describe DLQ files as derived | REQ-001; AC-01 | Architecture "Persistence" bullet names SQLite and per-event DLQ JSON files only (checked in Step 3) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/24_eventbus/eventbus_03_dlq_operations.md` | Modify: publish and subscribe contract, JSONL Append Failure paragraph, `since_seq` rules, reconciliation, Failure Behavior Summary | Remove JSONL failure handling; add the HTTP 410 resume rule; align DLQ artifact reconciliation with derived-artifact wording | REQ-002, REQ-004, REQ-005; AC-02, AC-04, AC-05 | JSONL Append Failure at line 59 and the summary row at line 174; since_seq precedence at lines 72 to 100; reconciliation at lines 139 to 165 (checked in Step 3) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | Modify: Retention, JSONL Archive Retention, `since_seq` Precedence, Reliability Limits | Replace the TTL, manual cleanup SQL, and JSONL retention text with the state-aware retention model, artifact and archive lifecycle, and the replay-floor rule | REQ-003, REQ-004, REQ-005, REQ-007; AC-03, AC-04, AC-05, AC-07 | Retention at lines 171 to 205 with manual SQL leaving orphan `consumer_delivery` rows; Reliability Limits line 290 mentions SQLite and JSONL divergence (checked in Step 3) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | Modify: front matter keywords, JSONL Archive, idempotency guard, consistency check procedure, Replay Behavior, timestamps | Remove the JSONL replica and count comparison; rename the procedure to a SQLite-only integrity check; state the replay floor and the retention timestamp rule | REQ-002, REQ-004; AC-02, AC-04 | JSONL keyword at line 9, section at line 52, guard at line 64, procedure at lines 74 to 99, keyword at line 162; `published_at` is publisher-supplied (checked in Step 3) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Modify: Configuration Fields, Health Endpoint Semantics, Delivery and DLQ Operations, Shutdown | Document the retention task, capacity measurements, backup and archive retention, WAL checkpoint around retention and shutdown, and the absence of retention keys | REQ-003, REQ-006, REQ-007, REQ-008; AC-03, AC-06, AC-07 | Configuration Fields (lines 53 to 66) list no retention or capacity key; `config/eventbus.toml` has none (checked in Step 3) | `tests/eventbus/test_eventbus_config.py`, `tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/24_eventbus/eventbus_09_publish_durability.md` | Modify: Canonical Store, Publish Success Criterion, Failure Scenarios, Recovery Procedure, Metrics | Remove the JSONL append step, failure scenarios, counter, and repair statements; keep SQLite-commit success and best-effort broker notification | REQ-002; AC-02 | JSONL appears at lines 21 to 52, 69 to 89 and in the keywords (checked in Step 3) | `tests/eventbus/test_eventbus_publish_contract.py`, `tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/24_eventbus/eventbus_10_health_endpoint.md` | Modify: Response Content, Possible Degraded Reasons, Health Tiers | Add the retention and capacity signals, warning versus critical readiness behavior, and the separate retention health state, marked as not yet implemented | REQ-006, REQ-008; AC-06 | Degraded reasons at lines 50 to 65 and `health_route.py` report no retention or capacity field (checked in Step 3) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/24_eventbus/eventbus_11_replay_endpoint.md` | Modify: Parameters, Success Response, Invalid Parameters | Add the replay-floor bounds, HTTP 410 `replay_position_expired`, and the `since_seq=0` earliest-retained meaning | REQ-004, REQ-008; AC-04 | `since_seq` described as `seq` greater than the value at line 32; no 410 response documented (checked in Step 3) | `tests/eventbus/test_eventbus_replay_subscribe.py`, `tools/check_docs_consistency.py --domain eventbus` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Amended source of the decisions the documents restate (Decision Details 15 to 20, Replay Contract, INV-17 to INV-22) | REQ-001 to REQ-007 |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Lifecycle matrix for `eventbus.sqlite` (backup, restore, retention, capacity monitoring) | REQ-006, REQ-007 |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Known Issues EVENTBUS-001 and EVENTBUS-002 that the documents cite | REQ-002, REQ-003, REQ-006 |
| `docs/24_eventbus/eventbus_02_api-reference-index.md` | Endpoint index and common patterns; links stay valid and need no change | REQ-004 |
| `docs/24_eventbus/eventbus_04_dlq_endpoint.md` | DLQ endpoint contract; no JSONL or retention content, no change | REQ-005 |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Generated class and function reference; its generated block follows the code and stays unchanged | REQ-008 |
| `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` | ACK and NACK contract; the only retention wording concerns the NACK idempotency key, no change | REQ-004 |
| `scripts/eventbus/publish_route.py` | Current JSONL append and metric, for the cited deviation | REQ-002 |
| `scripts/eventbus/replay_route.py` | Current replay behavior, for the cited deviation | REQ-004 |
| `scripts/eventbus/subscribe_route.py` | Current subscribe start-position behavior | REQ-004 |
| `scripts/eventbus/health_route.py` | Current health fields and degraded reasons | REQ-006 |
| `scripts/eventbus/schema.sql` | Current tables and timestamp columns | REQ-002, REQ-003 |
| `scripts/eventbus/json_utils.py` | `now_iso()` as the EventBus-generated timestamp format | REQ-002 |
| `scripts/eventbus/config.py` | Confirms the configuration fields that exist | REQ-008 |
| `config/eventbus.toml` | Confirms no retention or capacity key exists | REQ-008 |
| `scripts/eventbus/db_tools.py` | `rotate` and verify tooling behind the archive wording | REQ-007 |
| `tools/generate_reference_table.py` | Shows the EventBus manifest is derived from code | REQ-008 |

## Acceptance Criteria
- `AC-01` (REQ-001): the guide routes to the revised documents, and the overview states `eventbus.sqlite` as the only system of record, separates audit logs, describes DLQ files as derived, and shows no `events.jsonl`.
- `AC-02` (REQ-002): no current EventBus document describes a JSONL append step, failure scenario, metric, count comparison, or repair, and each document states that a successful SQLite commit is publish success.
- `AC-03` (REQ-003): retention participants, purge predicates, purge blockers, decommission, purge unit, batching, and the dedicated task are stated unambiguously, and no operations guide recommends manual SQL that can leave orphan rows.
- `AC-04` (REQ-004): replay and subscribe expired-position behavior (HTTP 410 `replay_position_expired`, no silent offset advance, `since_seq=0` on `/replay`) is documented in the replay, subscribe, and delivery documents.
- `AC-05` (REQ-005): `events.dlq_at` and `dlq_outbox` are documented as authoritative, DLQ artifacts as derived and reconstructable, with active, `requeued/`, orphan, mismatched, and temporary file handling stated.
- `AC-06` (REQ-006, REQ-008): capacity and retention signals, warning versus critical behavior, and the retention health state are documented, with each missing field, key, or threshold stated as undefined and cited to a Known Issue.
- `AC-07` (REQ-003, REQ-007, REQ-009): database, WAL, disk, DLQ artifacts, audit logs, and verified archives each have bounded-growth guidance, and no `events.jsonl` is described as a replica, backup, recovery source, or audit ledger.
- `AC-08` (REQ-009): the documentation, link, canonical-source, and Needs-Confirmation-inventory checks pass and the generated block of the reference document is unchanged.

## Tests
- `REQ-001` to `REQ-009`: documentation-only, so no automated test is added. Evidence is the checker set in the Validation plan, plus the existing EventBus tests cited by the documents (`tests/eventbus/test_eventbus_config.py`, `tests/eventbus/test_eventbus_publish_contract.py`, `tests/eventbus/test_eventbus_replay_subscribe.py`) still passing unchanged.
- `REQ-008`: `uv run python tools/generate_reference_table.py --check` shows no drift, which confirms the manifest and generated block were not touched.

## Documentation Impact
Yes. The nine target documents under `docs/24_eventbus/` are the documentation, reached through `docs/00_index.md` ("Event Bus" area). They record intent, boundaries, constraints, failure behavior, operational notes, and Known Issue citations (EVENTBUS-001, EVENTBUS-002) for each point the code does not yet meet. `docs/00_index.md` lists no new file and needs no change.

## Assumptions
- The nine documents state the target contract from the amended ADR-006 and ADR-008, and cite EVENTBUS-001 or EVENTBUS-002 wherever current code differs; they do not claim the behavior exists.
- A statement of an undefined key, field, threshold, or timestamp column is expressed by citing EVENTBUS-002; no `Needs Confirmation` marker is added to a document, because each marker needs an inventory entry and this Plan does not edit the inventory.
- `eventbus_02`, `eventbus_04`, `eventbus_08`, and `eventbus_12` need no edit: they contain no JSONL, retention, or capacity content (checked in Step 3), and the generated block of `eventbus_08` follows the code.
- The API manifest and the generated reference inputs stay unchanged; the Issue's instruction to update them applies only when the code changes (corrected here from the Issue's wording).
- Dead-letter files stay documented as derived artifacts under `{deadletter_dir}`; their retention and the archive bounds are described as requirements without numeric values.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Names and thresholds of retention and capacity configuration keys and health response fields | None exist in `config/eventbus.toml`, `config.py`, or `health_route.py`; the ADR defines the signals but not key or field names | The documents describe the signals by their ADR names, state that keys, fields, and thresholds are undefined, and cite EVENTBUS-002; the implementation issue supplies the names | False |
| UNK-02 | The EventBus-generated timestamp used for age-based retention decisions | `events` stores only the publisher-supplied `published_at`; no receive-time column exists | The documents state the ADR-006 rule (an EventBus-generated timestamp, never `published_at`) and that no such column exists yet (EVENTBUS-002) | False |
| UNK-03 | The persistent source of truth for retention participants (consumer registry) | ADR-006 records it as an open owner decision | The documents record the open decision and that no purge runs until it is approved (EVENTBUS-002) | False |
| UNK-04 | Retention bounds for verified database archives by generation, age, and total size, and the minimum number of verified generations | No ADR, config key, or code defines them; `db_tools.py rotate` applies no bound | The documents state the required properties (bounded growth, a minimum of verified recovery generations, protection of the latest verified candidate) without numbers and keep the existing statement that no retention logic exists | False |
| UNK-05 | Destination and rotation of structured security audit logs | EventBus logging configuration under `config/`, `deploy/`, or service units was not located in this pass | The documents describe audit-log size as a deployment-defined measurement outside `eventbus.sqlite`; re-check when the implementation issue defines the signal | False |
| UNK-06 | Whether `/subscribe` with `since_seq=0` and a stored offset should replay from the start | ADR-006 keeps this as an open decision | The documents keep the current `/subscribe` start-position order and apply the earliest-retained meaning to `/replay` only | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/24_eventbus/eventbus_00_document-guide.md` | Modify | Low (routing table) | 0 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_01_system-overview.md` | Modify | Low | 2 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_03_dlq_operations.md` | Modify | Medium (anchors cited from other documents) | 6 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | Modify | High (anchors such as `#consumer-identity` are linked from several documents) | 5 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | Modify | Medium | 8 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Modify | Medium (cited by `tests/eventbus/test_eventbus_config.py` docstrings) | 8 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_09_publish_durability.md` | Modify | Low | 3 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_10_health_endpoint.md` | Modify | Low | 6 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_11_replay_endpoint.md` | Modify | Low | 1 | 2 authors in 365 days | not applicable (rsynced) |

## Design
Classification: Path B (nine target rows, more than three).

Analysis (documentation only; no Python target, so the radon, vulture, and bandit baseline is `N/A: no Python target`):
- Coupling: the documents cross-link by relative path and heading anchor (for example `eventbus_05#consumer-identity`), and `tools/check_docs_consistency.py --domain eventbus` checks internal links, `scripts/` path references, and backticked function references. Renaming a heading removes its anchor, so headings that other documents link to are kept or their links are updated in the same edit set. `eventbus_06` front matter keywords (`jsonl-archive`, `jsonl archive`) are edited together with the body.
- Content policy: `tools/check_docs_content_policy.py` and `skills/DESIGN.md` "Avoid implementation-reference duplication" apply; the documents cite the ADR and the Known Issue instead of restating code.
- Unsafe guidance: the manual deletion SQL is removed with no replacement statement; the operator guidance becomes "no manual deletion procedure is supported; retention is performed by the dedicated task once implemented (EVENTBUS-002)".
- Consumer scan and predictable fallout check: no persisted schema, public API, shared constant, or code symbol changes, so `tools/scan_change_consumers.py` is not applicable. Pinned counts: no test asserts a documentation count (checked in Step 3); tool inventory and module size: `not affected`; generated blocks: the `eventbus_08` block derives from `scripts/eventbus/*.py` and stays unchanged. `tests/eventbus/test_eventbus_config.py` only cites `eventbus_07` in docstrings, so `not affected`. Size ceiling of `tools/check_docs_structure.py` (default 32768 bytes): the largest target (`eventbus_05`, 17896 bytes) stays below it even if it doubles, `not affected`.
- Operational check: no process or database is touched (not run, documentation only). Persisted schema check (`rules/persisted-schema-change.md`): not applicable, no DDL or migration changes.

Decisions:
- Each statement about a behavior the code lacks carries the Known Issue citation instead of a `Needs Confirmation` marker (Assumptions).
- Retention is described once, in `eventbus_05` Retention, and the other documents link to it; health signals are described once, in `eventbus_10`, and `eventbus_07` links to them.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above. All steps edit documentation text only.

1. **Phase 1: Persistence and publish durability**
   - [ ] Remove JSONL append steps, failure scenarios, the metric, count comparison, and repair; state SQLite commit as publish success and best-effort broker notification; add the retention timestamp rule (REQ-002; `docs/24_eventbus/eventbus_09_publish_durability.md`, `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`, `docs/24_eventbus/eventbus_03_dlq_operations.md`)
2. **Phase 2: Retention, DLQ lifecycle, and archives**
   - [ ] Replace Retention, the manual SQL, and JSONL retention with the state-aware retention model, DLQ artifact and archive lifecycle, and bounded-growth guidance (REQ-003, REQ-005, REQ-007; `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`)
   - [ ] Document the retention task, backup and archive retention, WAL checkpoint around retention and shutdown, and the absence of retention keys in the operations document (REQ-003, REQ-007, REQ-008; `docs/24_eventbus/eventbus_07_configuration-and-operations.md`)
3. **Phase 3: Replay floor, health, and routing**
   - [ ] Add the replay-floor bounds, HTTP 410, and `since_seq=0` wording to the replay endpoint and the subscribe contract (REQ-004, REQ-008; `docs/24_eventbus/eventbus_11_replay_endpoint.md`, `docs/24_eventbus/eventbus_03_dlq_operations.md`)
   - [ ] Add the retention and capacity signals and readiness behavior to the health document (REQ-006, REQ-008; `docs/24_eventbus/eventbus_10_health_endpoint.md`)
   - [ ] Update the guide routing and the overview persistence description (REQ-001; `docs/24_eventbus/eventbus_00_document-guide.md`, `docs/24_eventbus/eventbus_01_system-overview.md`)
4. **Phase 4: Validation**
   - [ ] Run the checkers in the Validation plan and confirm the generated block and manifest are unchanged (REQ-009; all target files)

### Release units
**Unit**: eventbus-docs | **Phases**: 1, 2, 3 | **Reason**: the documents cross-link by anchor and `check_docs_consistency.py --domain eventbus` validates links and references across them, so removing a JSONL section in one document while another still links to it fails the check; the phases land together.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| All nine target documents | Cross-document consistency, links, path and function references | `uv run python tools/check_docs_consistency.py --domain eventbus` | No findings |
| All nine target documents | Documentation structure, quality, content policy, metadata | `uv run python tools/check_docs_structure.py`, `tools/check_docs_quality.py`, `tools/check_docs_content_policy.py`, `tools/check_metadata_field_policy.py` | No findings |
| All nine target documents | Known Issue and Needs Confirmation citations | `uv run python tools/check_known_deviation_sync.py`, `tools/check_needs_confirmation_inventory.py` | No findings |
| All nine target documents | Preservation of unrelated content | `uv run python tools/check_adr_preservation.py --dir docs/24_eventbus` | Only intended findings, reported |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Generated block unchanged | `uv run python tools/generate_reference_table.py --check` | No drift |
| `docs/24_eventbus/eventbus_07_configuration-and-operations.md`, `eventbus_09_publish_durability.md`, `eventbus_11_replay_endpoint.md` | Existing cited tests still pass | `uv run pytest tests/eventbus/test_eventbus_config.py tests/eventbus/test_eventbus_publish_contract.py tests/eventbus/test_eventbus_replay_subscribe.py -q` | Pass |
| All nine target documents | Gate runner for the changed files | `uv run python tools/run_validation_gates.py` | No `Fail` or `Blocked` |

## Risks
- **Risk**: The documents describe retention, the replay floor, and capacity signals that the code does not implement, so a reader may take them as current behavior → **Mitigation**: each such statement cites EVENTBUS-002, and the JSONL difference cites EVENTBUS-001.
- **Risk**: The documents say the EventBus creates no `events.jsonl` while the code still writes it → **Mitigation**: the EVENTBUS-001 citation and no invented repair procedure; the retired metric is not documented as live.
- **Risk**: A removed heading breaks an anchor link from another document → **Mitigation**: keep linked headings or update the links in the same edit set; `check_docs_consistency.py --domain eventbus` runs before commit.
- **Risk**: A `Needs Confirmation` marker added without an inventory entry fails `check_needs_confirmation_inventory.py` → **Mitigation**: no such marker is written; Known Issue citations are used instead.
- **Risk**: Removing the manual deletion SQL leaves operators with no procedure when disk fills → **Mitigation**: the operations text states the supported actions (back up and rotate the database through `python -m eventbus.db_tools rotate`, as already documented) and that no manual deletion is supported.
- **Risk**: High churn on `eventbus_06`, `eventbus_07`, and `eventbus_03` (6 to 8 commits in 30 days) causes merge conflicts → **Mitigation**: sync immediately before the commit and re-run the consistency check after any rebase.
- **Risk**: Wording drifts from ADR-006 → **Mitigation**: the documents restate the ADR decision and link to it instead of paraphrasing numbers or thresholds.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Persistence and publish durability: remove JSONL, state commit as success | Completed | — | 20261124-102754 |  |
| 2 | Retention, DLQ lifecycle, and archive guidance in the delivery and operations documents | Completed | — | 20261124-102754 |  |
| 3 | Replay floor, health signals, guide routing, and overview | Completed | — | 20261124-102754 |  |
| 4 | Validation checks and unchanged-manifest confirmation | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261124-102127_01_docs_24_eventbus_eventbus_00_document-guide.md.md | 3 | Procedure | Completed | — | — |
| implementations/20261124-102127_02_docs_24_eventbus_eventbus_01_system-overview.md.md | 3 | Procedure | Completed | — | — |
| implementations/20261124-102127_03_docs_24_eventbus_eventbus_03_dlq_operations.md.md | 1, 3 | Procedure | Completed | — | — |
| implementations/20261124-102127_04_docs_24_eventbus_eventbus_05_dlq_offsets_and_delivery_semantics.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261124-102127_05_docs_24_eventbus_eventbus_06_persistence_schema_and_replay.md.md | 1 | Procedure | Completed | — | — |
| implementations/20261124-102127_06_docs_24_eventbus_eventbus_07_configuration-and-operations.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261124-102127_07_docs_24_eventbus_eventbus_09_publish_durability.md.md | 1 | Procedure | Completed | — | — |
| implementations/20261124-102127_08_docs_24_eventbus_eventbus_10_health_endpoint.md.md | 3 | Procedure | Completed | — | — |
| implementations/20261124-102127_09_docs_24_eventbus_eventbus_11_replay_endpoint.md.md | 3 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261124-093928_adrdoc002_eventbus-docs-sqlite-retention.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261124-101736
- **Related target files**: `docs/24_eventbus/eventbus_00_document-guide.md`, `docs/24_eventbus/eventbus_01_system-overview.md`, `docs/24_eventbus/eventbus_03_dlq_operations.md`, `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`, `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`, `docs/24_eventbus/eventbus_07_configuration-and-operations.md`, `docs/24_eventbus/eventbus_09_publish_durability.md`, `docs/24_eventbus/eventbus_10_health_endpoint.md`, `docs/24_eventbus/eventbus_11_replay_endpoint.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes A | `docs/24_eventbus/eventbus_00_document-guide.md` | Phase 3 | AC-01 | `check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-001 | Required Changes A | `docs/24_eventbus/eventbus_01_system-overview.md` | Phase 3 | AC-01 | `check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-002 | Required Changes B; JSONL in eventbus_09 lines 21 to 89 | `docs/24_eventbus/eventbus_09_publish_durability.md` | Phase 1 | AC-02 | `check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-002 | Required Changes B; JSONL in eventbus_06 lines 52 to 99 | `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | Phase 1 | AC-02 | `check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-002 | Required Changes B; JSONL in eventbus_03 lines 59 and 174 | `docs/24_eventbus/eventbus_03_dlq_operations.md` | Phase 1 | AC-02 | `check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-003 | Required Changes C; manual SQL in eventbus_05 lines 171 to 205 | `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | Phase 2 | AC-03, AC-07 | `check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-003 | Required Changes C | `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Phase 2 | AC-03 | `check_docs_consistency.py --domain eventbus` | Needs confirmation (UNK-03) |
| REQ-004 | Required Changes D | `docs/24_eventbus/eventbus_11_replay_endpoint.md` | Phase 3 | AC-04 | `check_docs_consistency.py --domain eventbus` | Needs confirmation (UNK-06) |
| REQ-004 | Required Changes D | `docs/24_eventbus/eventbus_03_dlq_operations.md` | Phase 3 | AC-04 | `check_docs_consistency.py --domain eventbus` | Needs confirmation (UNK-06) |
| REQ-004 | Required Changes D | `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | Phase 3 | AC-04 | `check_docs_consistency.py --domain eventbus` | Needs confirmation (UNK-06) |
| REQ-004 | Required Changes D | `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | Phase 3 | AC-04 | `check_docs_consistency.py --domain eventbus` | Derived from confirmed evidence |
| REQ-005 | Required Changes E; eventbus_03 lines 139 to 165 | `docs/24_eventbus/eventbus_03_dlq_operations.md` | Phase 2 | AC-05 | `check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-005 | Required Changes E | `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | Phase 2 | AC-05 | `check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-006 | Required Changes F | `docs/24_eventbus/eventbus_10_health_endpoint.md` | Phase 3 | AC-06 | `check_docs_consistency.py --domain eventbus` | Needs confirmation (UNK-01, UNK-05) |
| REQ-006 | Required Changes F | `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Phase 2 | AC-06 | `check_docs_consistency.py --domain eventbus` | Needs confirmation (UNK-01, UNK-05) |
| REQ-007 | Required Changes G | `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | Phase 2 | AC-07 | `check_docs_consistency.py --domain eventbus` | Needs confirmation (UNK-04) |
| REQ-007 | Required Changes G | `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Phase 2 | AC-07 | `check_docs_consistency.py --domain eventbus` | Needs confirmation (UNK-04) |
| REQ-008 | Required Changes H; manifest derived from code | `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Phase 2 | AC-06, AC-08 | `generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-008 | Required Changes H | `docs/24_eventbus/eventbus_10_health_endpoint.md` | Phase 3 | AC-06 | `generate_reference_table.py --check` | Needs confirmation (UNK-01) |
| REQ-008 | Required Changes H | `docs/24_eventbus/eventbus_11_replay_endpoint.md` | Phase 3 | AC-04 | `generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-009 | Required validation; Acceptance Criteria | `docs/24_eventbus/eventbus_00_document-guide.md` | Phase 4 | AC-08 | Validation plan checkers | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261124-102127 -->
