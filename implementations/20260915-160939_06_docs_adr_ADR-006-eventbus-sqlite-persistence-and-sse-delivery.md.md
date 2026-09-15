## Goal
Remove ADR-006's redundant file/class/config/test list from `## Implementation
Notes` once fully reconciled into `### Implementation References`, per `REQ-006` —
the highest-risk row in the Plan: both copies currently cite files and symbols that
no longer exist in current source at all.

## Scope
- In scope: rewrite `### Implementation References`' 実装ファイル/主要Class・
  Function entries to reflect actual current source; add the `consumer_delivery`/
  `consumer_offsets` schema, the legacy-offset-filename fact, and the DLQ
  dual-promotion-path fact (none currently in References); add the missing
  `tests/db/test_create_schema.py` citation; then delete the now-reconciled Notes
  bullets (実装ファイル, 主要Class・Function, データベーススキーマ, オフセット
  ファイル, DLQ昇格経路, 対応するテスト).
- Out of scope: lines 375-377 (トランザクション保証, Monotonicity Enforcement,
  レガシー移行 prose) — tracked in a separate issue, MUST remain byte-for-byte
  unchanged. No attempt is made here to audit or correct ADR-006's Decision/
  Rationale prose against current source — only the Implementation
  Notes/References list content in scope above.

## Assumptions
- No pointer line is needed — lines 375-377 survive, keeping the section
  non-empty.
- The actual current module layout (confirmed during Plan creation, re-confirm at
  implementation time since more time will have passed):
  - `scripts/eventbus/broker.py` — `class EventBroker`, method `publish()`
    (NOT a `notify_subscribers()` method — that does not exist)
  - `scripts/eventbus/publish_route.py` — `async def publish(...)` (NOT
    `publish.py`, NOT named `publish_event()`)
  - `scripts/eventbus/subscribe_route.py` — `async def subscribe(...)` (NOT
    `subscribe.py`, NOT an `EventSubscriber` class)
  - `scripts/eventbus/db.py` — `ack_event()`, `ack_event_for_consumer()`,
    `nack_event()`, `insert_event()`, `get_consumer_offset()`,
    `migrate_legacy_offsets()` (NOT separate `ack.py`/`nack.py` files)
  - `scripts/eventbus/offsets.py` — `write_offset()`, `read_offset()` (this one
    was already correct in both copies)
  - `scripts/eventbus/dlq.py` — `promote_single()` (already correct)

## Design decisions
- Both Notes and References cite an outdated module layout — the code was
  reorganized into `*_route.py` files and consolidated symbols into `db.py`
  without either ADR copy being updated. Since this is not a Notes-vs-References
  conflict (both agree, both are wrong), the fix is a full rewrite against actual
  current source, not a cross-copy merge.
- The `consumer_delivery`/`consumer_offsets` table schemas, the legacy-offset-
  filename pattern, and the DLQ dual-promotion-path description are unique
  content not derivable from a file/symbol name alone (they encode operational
  facts: column layouts, a specific 60-second loop interval, a filename
  sanitization convention) — per the Plan's Design "Not every list item is a true
  duplicate," these migrate into References as new canonical content rather than
  being silently dropped.

## Alternatives considered
- Merge Notes' and References' existing (both stale) text without checking actual
  source — rejected; this would just produce a third, still-wrong version. Only
  reading actual current `scripts/eventbus/*.py` source produces a correct result.
- Leave the stale entries in place since fixing them is arguably outside this
  issue's literal "duplication" framing — rejected per the Plan's Design
  reasoning: once Notes' copy is deleted, a stale References becomes the sole,
  uncorrected record, which is a regression this issue's own goal (a reliable
  single source of truth) must not produce.

## Implementation
### Target file
`docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure
1. Re-verify current line numbers: confirm the Notes list is still at lines
   370-378 (with 375-377 as the protected non-list prose) and References at
   513-521.
2. Re-run the full source audit against current `scripts/eventbus/*.py` (do not
   trust the Assumptions section above without re-checking — source may have
   changed further since Plan creation):
   - `ls scripts/eventbus/broker.py scripts/eventbus/publish_route.py scripts/eventbus/subscribe_route.py scripts/eventbus/db.py scripts/eventbus/offsets.py scripts/eventbus/dlq.py`
   - `grep -n "^class \|^def \|^async def " scripts/eventbus/broker.py scripts/eventbus/publish_route.py scripts/eventbus/subscribe_route.py scripts/eventbus/db.py scripts/eventbus/offsets.py scripts/eventbus/dlq.py`
   - Confirm `scripts/eventbus/publish.py`, `subscribe.py`, `ack.py`, `nack.py` still do not exist (`ls` should fail for all four).
3. Rewrite References' 実装ファイル/主要Class・Function bullets entirely, one
   bullet per actual current file:
   - `scripts/eventbus/broker.py` — `EventBroker.publish()`
   - `scripts/eventbus/publish_route.py` — `publish()`
   - `scripts/eventbus/subscribe_route.py` — `subscribe()`
   - `scripts/eventbus/db.py` — `ack_event()`, `ack_event_for_consumer()`,
     `nack_event()`, `insert_event()`, `get_consumer_offset()`,
     `migrate_legacy_offsets()`
   - `scripts/eventbus/offsets.py` — `write_offset()`, `read_offset()` (unchanged)
   - `scripts/eventbus/dlq.py` — `promote_single()` (unchanged)
4. Update References' `events`テーブル bullet to also include `consumer_delivery`
   テーブル (`consumer_id`, `event_id`, `acked_at`, PRIMARY KEY
   `(consumer_id, event_id)`) and `consumer_offsets`テーブル (`consumer_id`
   PRIMARY KEY, `offset INTEGER NOT NULL DEFAULT 0`) — copy the exact column
   definitions currently in Notes line 372 verbatim.
5. Add a new References bullet for the legacy offset filename pattern:
   `{offsets_dir}/{sanitized_consumer_id}`（レガシー、移行中）— copied verbatim
   from Notes line 373.
6. Add a new References bullet for the DLQ dual-promotion path: インライン昇格
   （`POST /nack`時）とバックグラウンドループ（60秒ごと）— copied verbatim from
   Notes line 374.
7. Add `tests/db/test_create_schema.py` to References' test bullet (alongside the
   already-present `tests/test_eventbus_*.py`).
8. Delete the now-fully-reconciled Notes bullets: 実装ファイル (370), 主要Class・
   Function (371), データベーススキーマ (372), オフセットファイル (373), DLQ
   昇格経路 (374), 対応するテスト (378). Leave lines 375-377 (トランザクション
   保証, Monotonicity Enforcement, レガシー移行) completely untouched.

### Method
Use `Edit` (exact-string replacement) — one call per step 3-8, so each change is
independently reviewable. Do not batch steps 3-7 into a single edit even though
they all target the same References subsection — keep them separable in the diff.

### Details
- This is the Plan's highest-risk row — do not skip step 2's re-audit even if it
  feels redundant with this document's own Assumptions section; source may have
  changed since this procedure was generated.
- Preserve lines 375-377 byte-for-byte — verify with a diff after editing that
  these three lines are unchanged.
- If step 2's re-audit finds the module layout has changed AGAIN since this
  procedure was written (e.g. a further rename), this is a "Plan Gap" per
  `skills/plan-to-implementation-procedure/workflow.md` Step 3c — do not silently
  adapt; report it and use the newly-discovered actual layout instead, updating
  this document's own Procedure text to match before applying the edit.

## Compatibility considerations
N/A: documentation-only change; no code, config, or test reads this ADR's
Notes/References sections programmatically.

## Security considerations
N/A: documentation-only change.

## Rollback considerations
Single-file, git-tracked Markdown edit — revert via
`git checkout -- docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`
if validation fails. Given the scale of this row's rewrite, prefer reverting and
re-attempting over patching a partially-wrong rewrite in place, if step 2's
re-audit reveals the initial rewrite was itself based on stale information.

## Validation plan
- `ls`/`grep` re-audit (step 2 above) — must be run fresh at implementation time, not assumed from this document's Assumptions section.
- Manual diff: confirm References' file/symbol list matches actual current source exactly (cross-check each bullet against a fresh `grep` result).
- Manual diff: confirm lines 375-377 are byte-for-byte unchanged.
- Manual diff: confirm Notes' reconciled bullets (370-374, 378) are removed; 375-377 remain.
- `uv run python tools/check_docs_quality.py docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` — zero findings.
- `uv run python tools/check_docs_structure.py docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` — record baseline, confirm no new finding.
- `uv run python tools/check_adr_reference.py` and `uv run python tools/check_adr_invariant_matrix.py` — zero findings.

## Completion criteria
- Every file path and symbol in References matches actual current source
  (verified via fresh `ls`/`grep`, not merely internally consistent).
- `consumer_delivery`/`consumer_offsets` schema, offset-filename pattern, and DLQ
  dual-promotion-path fact all appear in References.
- `tests/db/test_create_schema.py` appears in References.
- Lines 375-377 are unchanged.
- All Validation plan checks pass (or no new `check_docs_structure.py` finding).

## Out of scope
- Lines 375-377 (transaction guarantee, Monotonicity Enforcement, legacy
  migration prose).
- Any audit or correction of ADR-006's Decision/Rationale/Invariants/Verification
  prose against current source.
- Any other ADR-006 section.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-160939 | 20260915-162816 | Re-audited actual current source (unchanged from Plan/procedure evidence); fully rewrote References to match current file/symbol layout; migrated consumer_delivery/consumer_offsets schema, offset-filename fact, DLQ dual-promotion fact, and test_create_schema.py; deleted reconciled Notes bullets; preserved lines 375-377 verbatim (verified via diff) |
| 2 | Add or update tests per Validation plan | Completed | 20260915-162816 | 20260915-162816 | N/A: documentation-only N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-162816 | 20260915-162816 | N/A: documentation-only, use this document's own Validation plan check_docs_quality: 0 findings; check_docs_structure: 11 pre-existing unrelated findings, confirmed via git diff not caused by this edit |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-162816 | 20260915-162816 | N/A: target file IS the documentation N/A: target file IS the documentation |

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
- **Requirement ID**: REQ-006 — full source-audit reconciliation, delete reconciled Notes lines, preserve 375-377
- **Source issue**: issues/done/20260914-124438_docqa02_adr-implementation-notes-file-list-duplicates-references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-154020_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-160939
- **Related target files**: docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md