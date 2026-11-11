## Goal

Document, in `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, the `dlq_outbox` table (Scope + Data Ownership), the `/replay` contract, and the `/subscribe` replay-start precedence, each with a pending maintainer-approval record, so no EventBus table or endpoint behavior is left without an ADR-level specification (`REQ-001`, `REQ-002` / `AC-1`, `AC-2`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The edits are decision-text only; no code changes. Both decision-text edits need a pending maintainer approval record (UNK-04), tracked by the approval-ledger Plan (adrrev012).
- The current Scope `Target data` bullet (line 91) lists DLQ state as `events.dlq_at` and deadletter files but omits the `dlq_outbox` table; the Data Ownership block (lines 215-221) likewise does not name it.
- `/replay` and `/subscribe` behavior is confirmed from code (below); the ADR must describe it, not invent it.

## Design decisions
- Extend the existing Scope `Target data` and Data Ownership bullets rather than adding a new subsection, so the additions sit beside the DLQ wording that already exists.
- Add a dedicated `### Replay Contract` subsection under `Context` (or after the Invariants) stating the `/replay` and `/subscribe` rules, and map them into the Automated Tests invariant matrix.
- Record each decision-text edit as a `Current Decision Approval (pending)` line in the Approval Record, mirroring the "Recorded pending a maintainer decision … not resolved" phrasing used in ADR-008's Known Issues — never fabricating an approval.

## Alternatives considered
- Adding a separate ADR for replay semantics: rejected — `/replay` and `/subscribe` are delivery-path behaviors already owned by ADR-006; a new ADR would fragment the EventBus contract.

## Implementation
### Target file
`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure
1. Scope — `Target data` bullet (line 91): append the `dlq_outbox` table to the DLQ-state listing.
2. Data Ownership (lines 215-221): add a bullet naming `dlq_outbox` as the durable per-event promotion record and its retention of `done` rows.
3. Add a `Replay Contract` subsection describing the `/replay` and `/subscribe` rules (text below).
4. Verification → Automated Tests matrix: add rows mapping `dlq_outbox` persistence and the replay-start precedence to INV-08 and the new replay rule.
5. Approval Record: append one `Current Decision Approval (pending)` line per decision-text edit (Scope/Data Ownership and Replay Contract).
6. Do not alter any other ADR's text, invariant, or the ADR index.

### Method
1. Scope `Target data` (line 91) becomes:
> - **Target data**: the `events` table, the `consumer_delivery` and `consumer_offsets` tables, DLQ state (`events.dlq_at`, deadletter files, and the `dlq_outbox` durable promotion record with `status` `pending`/`done`/`failed`), and the `dlq_outbox` retention of `done` rows

2. Add to Data Ownership (after the Deletion Rule bullet, ~line 221):
> - **Durable promotion record**: the `dlq_outbox` table (`scripts/eventbus/schema.sql`) records each Event promoted to the DLQ with its `requested_at`, `status` (`pending`/`done`/`failed`), attempt count, and `next_attempt_at`; it is the outbox the background loop consumes. `done` rows are retained as the delivery history; the EventBus does not delete them.

3. Replay Contract subsection (place after the Invariants list, before Failure Policy, or as a new `### Replay Contract` under Context):
> ### Replay Contract
>
> - **`/replay` is Operator-only.** Only a caller authenticated with the `Operator` role may read via `/replay` (`scripts/eventbus/replay_route.py`, `require_role(Role.OPERATOR)`). It reads any `seq` range and advances **no** Consumer offset: a replay is a read-only view, so repeated replays never move a stored position.
> - **`/subscribe` replay-start precedence.** On `GET /subscribe`, the start `seq` is resolved as `since_seq` (when non-zero) **then** the Consumer's stored resume position **then** the `Last-Event-ID` header (`scripts/eventbus/subscribe_route.py`, precedence documented at its REQ-003/REQ-004 comments). `since_seq=0` means "unspecified", so for a `consumer_id` that has a stored offset `/subscribe` resumes from that offset and **cannot** replay from the start; `since_seq>0` overrides the stored position. To read from the start, use `/replay` with `since_seq=0`.
> - **Maintainer decision (UNK-01).** Whether `/subscribe` should support replay-from-the-start for a Consumer with a stored offset is deferred; this ADR documents the current behavior and `/replay` as the alternative.

4. Automated Tests matrix rows (append):
> | `dlq_outbox` rows persist the DLQ promotion and its status lifecycle | INV-08 | Integration | Yes | `tests/eventbus/test_eventbus_dlq_promotion.py::TestDLQPromotionSemantics::test_nack_increments_consumer_delivery_failure_count` (outbox row written on promotion) |
> | `/subscribe` resumes from the stored offset when `since_seq=0` and `/replay` advances no offset | (new replay rule) | Integration | Yes | pending — described by this ADR; verified by `tests/eventbus/test_eventbus_health.py` replay/start assertions once added |

5. Approval Record (append two lines before the closing paragraph at line 316):
> - **Current Decision Approval (pending)**: The addition of the `dlq_outbox` durable promotion record to Scope (`Target data`) and to Data Ownership is a decision-text change awaiting maintainer approval; tracked by the approval-ledger Plan (adrrev012). No approval is fabricated.
> - **Current Decision Approval (pending)**: The `/replay` (Operator-only, offset-preserving) and `/subscribe` (`since_seq` > resume position > `Last-Event-ID`) replay contract is a decision-text change awaiting maintainer approval; tracked by adrrev012. No approval is fabricated.

### Details
- The `dlq_outbox` DDL (`event_id PRIMARY KEY REFERENCES events(event_id)`, `status CHECK IN ('pending','done','failed')`) lives in `scripts/eventbus/schema.sql`; cite it in the Data Ownership bullet as above.
- `/replay` uses `fetch_events_since` (read-only) and writes no `consumer_delivery`/`consumer_offsets` row, so offsets are unchanged — state this factually; do not overclaim beyond the code.
- Keep the pending-approval wording identical in structure to ADR-008's "Recorded pending a maintainer decision … not resolved" so governance tooling and reviewers recognize the marker.

## Compatibility considerations
- Documentation-only; no code, config, or schema change. The invariant-matrix additions extend existing rows; no existing invariant text is rewritten.
- Overlap: ADR-006 is also edited by adrrev015 (INV matrix, requeue paragraph) and adrrev016 (front matter, INV-15). This Plan edits the Scope/Data Ownership bullets, the replay subsection, and the Approval Record — distinct locations; keep edits to those regions.

## Security considerations
- The `/replay` Operator-only rule restates an existing authz boundary (ADR-013 INV-02); no new authorization is introduced.

## Rollback considerations
- N/A: revert the commit; all edits are localized to this document.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `check_adr_authority.py`, `check_adr_invariant_matrix.py`, `check_adr_preservation.py` — pass (preservation reports only the intended text changes).
- `uv run python tools/check_docs_consistency.py --domain eventbus` — pass.
- `uv run python tools/check_docs_content_policy.py --strict`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_japanese.py` — pass.

## Completion criteria
- `dlq_outbox` appears in ADR-006 Scope `Target data` and Data Ownership, with the `pending`/`done`/`failed` status lifecycle and `done`-row retention stated.
- The `/replay` (Operator-only, offset-preserving) and `/subscribe` (`since_seq` > resume position > `Last-Event-ID`, `since_seq=0` = unspecified) contract is documented.
- Both decision-text edits carry a `Current Decision Approval (pending)` line; no approval is fabricated.
- Every EventBus table and configuration key named in the ADR is covered by an ADR or referenced specification; the checkers above pass.

## Out of Scope
- Any code change implementing the replay contract — the behavior already exists; this documents it.
- The maintainer decision on full `/subscribe` replay (UNK-01) — recorded as pending, not resolved.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` / `REQ-002` — name `dlq_outbox` in ADR-006 Scope and Data Ownership; document the `/replay` and `/subscribe` replay contract
- **Source issue**: issues/20261109-113152_adrrev014_eventbus-spec-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-103238_adrrev014_eventbus-spec-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-072954
- **Related target files**: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`
