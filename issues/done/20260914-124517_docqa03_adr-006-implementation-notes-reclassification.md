# Reclassify ADR-006's Implementation Notes prose: monotonicity/transaction notes duplicate existing Invariants; legacy offset migration note reads as an unregistered Known Issue

## Priority
Medium

## Summary
`docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`'s `## Implementation Notes` section (beyond the file/class/config/test list handled by a separate issue) contains four prose items: transaction-guarantee, monotonicity-enforcement, DLQ-promotion-path, and legacy-offset-migration descriptions. Comparing each against the ADR's own `## Invariants` section (INV-01 through INV-15): the monotonicity and DLQ-path descriptions restate content already captured by INV-05/INV-09 and INV-13 respectively (delete candidates — duplication, not new information); the transaction-guarantee description explains *why* a single-transaction boundary matters for data integrity and is not yet captured by any existing Invariant wording (promote candidate); the legacy-offset-migration description documents a "レガシー、移行中" mechanism with no corresponding Invariant, Known Deviation, or Known Issue entry anywhere in the ADR (move-to-Known-Issue candidate — its own wording, "移行中," signals a provisional implementation state per this review's classification criteria).

## Background
This issue follows a review requested in this session: classify each item in every ADR's Implementation Notes section against four buckets (delete / promote to ADR-Decision-or-design-body / move to Known Issue / move to Needs Confirmation). This issue covers ADR-006's non-file-list prose specifically; the file/class/config/test list itself is covered by a separate, common-pattern issue from the same review.

## Problem
Confirmed by direct reading of `docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`:
- **Implementation Notes** (~line 366-383) contains:
  1. "トランザクション保証: `ack_event_for_consumer()`はper-consumer delivery-state UPSERTとoffset進捗を単一SQLiteトランザクション内で実行。いずれかが失敗すると両方がロールバックされる" — explains a data-integrity mechanism (atomic UPSERT+offset) with a clear "why" (partial-state corruption if not atomic). No existing Invariant (INV-01 through INV-15, lines 231-247) states this atomicity requirement explicitly; INV-12 ("ACK永続化失敗時はエラー応答を返し、再配信しない") is adjacent but does not itself state the two writes must be atomic with each other.
  2. "Monotonicity Enforcement: `consumer_offsets`テーブルの`INSERT ... ON CONFLICT(...) DO UPDATE SET offset = excluded.offset WHERE excluded.offset > consumer_offsets.offset`で強制。古いseq値ではオフセット後退しない" — this is a restatement of INV-05 ("ACK済みOffsetの後退を許可しない") and INV-09 ("`new_offset <= current_offset`を拒否する"), just with the SQL mechanism spelled out.
  3. "DLQ昇格経路: インライン昇格（`POST /nack`時）とバックグラウンドループ（60秒ごと）" — this restates INV-13 ("DLQ昇格はインライン昇格を優先し、バックグラウンドループは補完のみ"), adding only the 60-second interval value (itself arguably a Needs-Confirmation-worthy detail — see Unresolved Questions).
  4. "レガシー移行: 起動時に`migrate_legacy_offsets()`が`.map`コンパニオンから元の`consumer_id`を取得し、`consumer_offsets`テーブルにシード。`.map`なしの場合はサニタイズ済みファイル名を使用" — no Invariant, Known Deviation, or Known Issue entry anywhere in this ADR mentions this migration path, its completion criteria, or when it can be safely removed. The ADR's own wording ("レガシー") signals a transitional mechanism with no stated end condition.
- `## Known Deviations` section of this ADR (line ~384) was not read in full during this issue's drafting — verify during implementation whether it already covers item 4 before treating it as unregistered.

## Reason for Change
Items 2 and 3 are pure duplication of existing Invariants — the same information exists in two places with no mechanism keeping them synchronized (a future Invariant wording change would not automatically update the Implementation Notes restatement, or vice versa). Item 1 documents a real data-integrity constraint ("複数実装が同じ制約を守る必要がある" per this review's promote criterion — any future refactor of `ack_event_for_consumer()` or an equivalent must preserve this atomicity) that is not yet a first-class Invariant, meaning a future change could silently break it without an Invariant to violate/flag. Item 4 is a live migration mechanism with no stated retirement condition, sitting outside this ADR's Known Deviations tracking entirely (pending verification).

## Implementation Intent
Delete items 2 and 3 from Implementation Notes (their content is already covered by INV-05/INV-09 and INV-13 respectively — Implementation Notes can reference the Invariant by ID instead of restating it in prose). Promote item 1's atomicity requirement to a new Invariant in the `## Invariants` section (e.g. "delivery-state UPSERT and offset progression commit atomically in one transaction; a failure in either rolls back both"), with a corresponding Verification entry. For item 4, first check whether `## Known Deviations` already covers the legacy migration; if not, register it as a Known Issue (or Known Deviation) stating its provisional nature and a condition for removal (e.g. "remove once all `.map` companion files are confirmed migrated in production"), per this review's Known-Issue criterion ("実装が暫定状態にある").

## Target Files or Areas
- `docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`

## Required Changes
- Remove the Monotonicity Enforcement and DLQ昇格経路 prose items from Implementation Notes; replace with a short pointer to INV-05/INV-09 and INV-13 respectively if any implementation-mechanism detail is still worth keeping (e.g. the specific `ON CONFLICT` SQL clause), otherwise remove entirely.
- Add a new Invariant for the transaction-guarantee item (atomic UPSERT+offset-progression), with a corresponding entry in `## Verification` citing the actual test that exercises this (search `tests/test_eventbus_*.py` for existing coverage before assuming none exists).
- Read `## Known Deviations` in full to determine whether the legacy offset migration is already tracked; if not, add an entry there describing its provisional status and retirement condition, following ADR-002's `### CI-001: ...` structured field format (already established as this project's Known Issue format inside an ADR).

## Constraints
Do not remove the underlying SQL mechanism detail (the `ON CONFLICT` clause) if it is genuinely useful implementation guidance — only remove the duplicated Invariant restatement; a short "implemented via `INSERT ... ON CONFLICT ...`" pointer alongside the Invariant reference is acceptable.

## Acceptance Criteria
- Implementation Notes no longer restates INV-05/INV-09/INV-13 in prose form.
- A new Invariant (with ID following the existing INV-01 through INV-15 numbering) captures the transaction-atomicity requirement for `ack_event_for_consumer()`, with a Verification entry.
- The legacy offset migration mechanism is either already covered by `## Known Deviations`, or a new entry is added there.
- `tools/check_adr_invariant_matrix.py` and `tools/check_adr_reference.py` still pass after the change (the new Invariant may require adding a row to `docs/adr-index.md`'s Invariant Verification Matrix — check whether this ADR's Invariants are indexed there and follow the same pattern used when ADR-014's INV-023/024/025 were added).

## Testing Expectations
Search `tests/test_eventbus_*.py` for existing coverage of the atomic UPSERT+offset-progression behavior before assuming a new test is needed; add one only if no existing test covers it.

## Documentation Impact
This issue's entire scope is `docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`, with a possible follow-on edit to `docs/adr-index.md`'s Invariant Verification Matrix if a new Invariant ID is added.

## Out of Scope
- The file/class/config/test list at the top of ADR-006's Implementation Notes — tracked in the common-pattern issue from the same review.
- Other ADRs' Implementation Notes prose (ADR-004's Known Deviations structure, ADR-007's Circuit Breaker description) — tracked in separate issues from the same review.
- The 60-second DLQ background-loop interval's own rationale — flagged as a possible Needs-Confirmation item below, but not resolved within this issue.

## Dependencies
N/A: none — can be implemented independently, though it is part of the same review batch as the other Implementation Notes issues filed alongside it.

## Unresolved Questions
- Whether the DLQ background loop's 60-second interval (mentioned in the item-3 prose) has a documented rationale anywhere, or whether it is itself a Needs-Confirmation candidate ("値や処理の根拠が不明") — not resolved by this issue; note it for a future pass if this issue's implementer does not find an existing rationale.
- Whether `## Known Deviations` already covers the legacy offset migration mechanism — this issue's drafting did not read that section in full; resolve first during implementation before adding a duplicate entry.

## AI Implementation Instruction
Read `## Known Deviations` in full before adding a new entry for the legacy migration — do not duplicate an existing entry if one already covers it. When adding the new transaction-atomicity Invariant, follow the existing INV-01 through INV-15 numbering and wording style exactly (short, single-sentence, imperative/declarative form) rather than introducing a different style.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-124517
- **Related target files**: docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md, docs/adr-index.md
