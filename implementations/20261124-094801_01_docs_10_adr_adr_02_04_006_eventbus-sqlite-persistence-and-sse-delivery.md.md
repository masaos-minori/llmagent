## Goal
Amend ADR-006 so `eventbus.sqlite` is the sole EventBus source of truth with no `events.jsonl`, add state-aware retention, the replay-floor contract, and capacity signals, and record where current code differs (REQ-001 sole SQLite source of truth; REQ-002 state-aware retention; REQ-003 replay floor; REQ-009 invariants and Known Deviations; REQ-007 pending approval bullets).

## Scope
**Release unit**: adr-amendment

- Edits only `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`. Part of the release unit with the ledger, ADR-008, index, authority, and guide documents (checkers cross-validate them).
- The `since_seq` / `Last-Event-ID` text of AAL-037 and the Replay Contract of AAL-007 are kept; this document only adds to them.

## Assumptions
- New pending entries exist after the ledger document is applied: AAL-040 (removal of `events.jsonl`) and AAL-041 (state-aware retention and replay expiration). Entry text is written by the ledger document (06).
- AAL-029 is narrowed, not removed: its no-loss-under-schema-mismatch statements (Summary, Decision Detail 9, INV-07, Rationale 1, Positive Consequences) stay; only the accepted retention risk (Data Ownership Deletion Rule) is withdrawn.
- New invariant numbers start at INV-17 (current maximum is INV-16). Existing numbers are not renumbered; new Decision Details are appended after the last existing one.
- Needs confirmation (UNK-01): the retention-participant registry model is unapproved, so the ADR records an open owner decision instead of a registry design. Needs confirmation (UNK-02): `since_seq=0` is redefined for `/replay`; the `/subscribe` open decision stays.

## Design decisions
- State the target decision and record each code divergence under Known Deviations; unimplemented invariants are Not verified, never cited to a passing test.
- Retention is defined once, here; ADR-008 refers to it.

## Alternatives considered
N/A: the alternatives (keep JSONL as audit replica, age-only retention) are rejected inside the ADR text itself.

## Implementation
### Target file
`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure
1. Remove JSONL as a data store: Context Problem (line 46), Constraints (line 52), Failure Policy (line 211), Fallback Policy (line 220), Data Ownership Derived Data (line 225). Replace with: `eventbus.sqlite` is the sole source of truth; structured security audit records are operational logs, not replicas, backups, replay sources, or recovery sources; DLQ JSON files are derived artifacts reconstructable from SQLite.
2. Append Decision Details after the last existing one: publish success is a SQLite commit and broker notification is a best-effort side effect; `events.dlq_at` and `dlq_outbox` are authoritative DLQ state and `pending` or `failed` outbox rows are never deleted automatically; retention rules (participants, blockers, atomic purge unit, dedicated task, capacity signals, readiness).
3. Rewrite the Data Ownership Deletion Rule (line 231): remove "no retention ... accepted risk" and refer to the retention Decision Details. Update Review Triggers (line 307) so the automatic-retention trigger no longer reads as undecided.
4. Replay Contract: add `earliest_available_seq` (new) and `latest_available_seq` (new), HTTP 410 with error code `replay_position_expired` (new) for `/replay` and `/subscribe` positions before the floor, no silent offset advancement, and `since_seq=0` as the earliest retained event for `/replay`; keep the `/subscribe` open decision.
5. Invariants: append INV-17 (SQLite commit is the only publish success), INV-18 (no `events.jsonl`; audit logs are not a replica), INV-19 (no age-only purge; all participants acknowledged or decommissioned; blockers respected; event and dependent rows purged as one unit), INV-20 (position before the floor fails with 410 and never advances an offset), INV-21 (`pending` and `failed` outbox rows are never deleted automatically), INV-22 (retention is a dedicated task; critical disk shortage or retention-invariant failure makes readiness false).

### Method
- Edit with the Edit tool, section by section; keep every existing Decision Detail and INV number stable.
- Automated Tests table: remove the row at line 252 (`test_publish_succeeds_if_jsonl_append_fails`) and, in the row at line 253, drop "neither the JSONL append nor". Cite only tests that exist (`tests/eventbus/test_eventbus_publish.py::test_publish_sqlite_write_failure_reports_failure_without_side_effects`, `tests/eventbus/test_eventbus_replay_subscribe.py`).
- Add Manual Review lines for INV-17 to INV-22 marked Not verified, each with the expected evidence and cadence (CI once the implementation issue lands).

### Details
- Known Deviations (replace `Not applicable`): `scripts/eventbus/publish_route.py` still appends `events.jsonl` and exposes `eventbus_jsonl_append_failure_total`; no retention task, retention configuration, purge, replay-floor check, or HTTP 410 exists; the retention-participant registry is undecided (UNK-01). Each entry names the INV it affects.
- Approval Record: narrow the AAL-029 pending bullet to the no-loss claims; add one pending bullet citing AAL-040 and one citing AAL-041 in the existing wording style (decision-text change awaiting maintainer approval; approver, date, and scope not recorded; no approval recorded here). Do not write an approver, a date, or an approval sentence.
- Related ADRs and front matter `related` keep ADR-008 and ADR-013; the ADR-008 file name is unchanged.

## Compatibility considerations
N/A: documentation only; the amended text describes the approved target and the deviations are recorded.

## Security considerations
N/A: no authentication change; ADR-013 stays the authority for authorization.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py` (pending bullets, Known Deviations heading, invariants).
- `uv run python tools/check_adr_invariant_matrix.py` once the index document is applied.
- `uv run python tools/check_adr_preservation.py --base HEAD docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`: expect intended invariant, Approval, and Known Deviations findings only (UNK-06).
- `uv run pytest tests/eventbus/test_eventbus_publish.py tests/eventbus/test_eventbus_publish_contract.py tests/eventbus/test_eventbus_replay_subscribe.py -q`.

## Completion criteria
- No current decision in the file requires or describes `events.jsonl`, and no JSONL test is cited.
- Retention, replay-floor, and capacity decisions and INV-17 to INV-22 are present; the Replay Contract states HTTP 410 `replay_position_expired` (new).
- Known Deviations lists each code divergence; the Approval Record cites AAL-029 (narrowed), AAL-040, AAL-041 and contains no approval sentence.

## Out of Scope
- Code, schema, route, configuration, and test changes; other ADR and `docs/` files; editing the ledger (document 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit ADR-006 text, Replay Contract, invariants, Known Deviations, and Approval Record per Implementation | Pending | — | — | |
| 2 | Run the ADR checkers and the cited EventBus tests per Validation plan | Pending | — | — | Checkers pass only after documents 01 to 06 are applied (release unit) |

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
- **Requirement ID**: REQ-001 (sole SQLite source of truth), REQ-002 (state-aware retention), REQ-003 (replay floor), REQ-007 (pending approval bullets), REQ-009 (invariants and Known Deviations)
- **Source issue**: issues/20261124-093927_adrdoc001_adr-eventbus-memory-amendment.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-094324_adrdoc001_adr-eventbus-memory-amendment.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-094801
- **Related target files**: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
