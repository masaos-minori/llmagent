## Goal
Reclassify ADR-006's three remaining non-file-list Implementation Notes prose
items per `REQ-001` through `REQ-005`: promote the transaction-guarantee item to
a new Invariant with Verification, delete the Monotonicity duplicate, and
reconcile the legacy-migration item into the existing `EVENTBUS-007` Known
Deviation rather than creating a duplicate entry.

## Scope
- In scope: add new local `INV-16` to `## Invariants`; add its `## Verification`
  entry; condense the transaction-guarantee Notes prose to a pointer; delete the
  Monotonicity Enforcement Notes prose, replacing with a short INV-05/INV-09
  pointer that preserves the `ON CONFLICT` SQL detail; enhance `EVENTBUS-007`
  with the `migrate_legacy_offsets()` mechanism detail; delete the legacy-
  migration Notes prose, replacing with a pointer to `EVENTBUS-007`.
- Out of scope: the DLQ昇格経路 item (already migrated to `### Implementation
  References` by a prior, already-completed Plan this session — confirmed absent
  from `## Implementation Notes` entirely, see Design); ADR-006's other Known
  Deviations entries; the 60-second DLQ background-loop interval's rationale;
  backfilling `docs/adr-index.md` cross-references for ADR-006's other 14 local
  Invariants.

## Assumptions
- ADR-006's own `## Verification` > `### Automated Tests` subsection does not
  cite `file.py::test_name` paths directly in its existing entries (unlike
  ADR-001) — only `**Test**` / `**Verifies**` / `**Type**` / `**Blocking**`
  fields. The new entry follows this same local format, naming the confirming
  test inline within the `**Test**` description per the source issue's explicit
  request for a citation.
- The confirming test's class is `TestCrashBeforeAck`
  (`tests/eventbus/test_eventbus_crash_ack.py`), confirmed via `grep` during Plan
  creation — not `TestCrashRecoveryScenarios` or any other name.
- No new test is required — `test_offset_write_failure_after_delivery_state`
  already asserts neither `consumer_delivery` nor `consumer_offsets` commits when
  the transaction's commit fails.

## Design decisions
- `INV-16`'s wording must match the existing `INV-01`–`INV-15` style exactly:
  short, single-sentence, Japanese, declarative — not an English compound
  sentence. Example target wording (exact phrasing may be refined at
  implementation time, but must stay single-sentence Japanese):
  `INV-16: ack_event_for_consumer()のDelivery-State UPSERTとOffset進捗は単一
  トランザクション内でコミットし、いずれかが失敗した場合は両方をロールバック
  する。`
- `EVENTBUS-007` is enhanced in place, not duplicated — it already states the
  legacy path's provisional nature and retirement condition
  ("移行期間終了後にレガシーパスを削除"); only the specific
  `migrate_legacy_offsets()` mechanism (`.map`-companion lookup, sanitized-
  filename fallback) is missing from it.
- The DLQ昇格経路 item is not touched here at all — it no longer exists in
  `## Implementation Notes` (confirmed via `grep` both at Plan creation and again
  in this procedure's own Step 3a re-verification); it was already migrated to
  `### Implementation References` by `plans/done/20260915-154020_plan.md`'s
  implementation, completed earlier in this same session.

## Alternatives considered
- File a new Known Deviation ID for the legacy-migration mechanism instead of
  enhancing `EVENTBUS-007` — rejected per the source issue's own AI
  Implementation Instruction ("do not duplicate an existing entry if one already
  covers it").
- Add a new test for the transaction-atomicity behavior — rejected;
  `tests/eventbus/test_eventbus_crash_ack.py::TestCrashBeforeAck::test_offset_write_failure_after_delivery_state`
  already covers it exactly (verified by reading the test in full).

## Implementation
### Target file
`docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure
1. Re-verify (idempotent recheck) current line numbers and content: confirm
   `## Invariants` still ends at `INV-15` (line 247), `## Implementation Notes`
   still has exactly the 3 prose lines (370-372) with no file-list content
   remaining before them, and `## Known Deviations`' `EVENTBUS-007` entry (lines
   400-404) still reads as previously confirmed.
2. In `## Invariants`, add a new bullet immediately after `INV-15`:
   `- INV-16: {single-sentence Japanese wording per Design decisions above}`.
3. In `## Verification` > `### Automated Tests`, add a new entry matching the
   existing field format:
   ```
   - **Test**: Delivery-State UPSERTとOffset進捗が単一トランザクション内で原子的に
     コミットされること（`tests/eventbus/test_eventbus_crash_ack.py::TestCrashBeforeAck::test_offset_write_failure_after_delivery_state`）
     - **Verifies**: INV-16
     - **Type**: Regression
     - **Blocking**: Yes
   ```
4. In `## Implementation Notes`, replace the トランザクション保証 line (370)
   with a short pointer: something like
   `- トランザクション保証: INV-16参照（`ack_event_for_consumer()`内の単一トランザクション）`.
5. In `## Implementation Notes`, replace the Monotonicity Enforcement line (371)
   with a short pointer that preserves the SQL mechanism detail, e.g.:
   `- Monotonicity Enforcement: INV-05, INV-09参照（`consumer_offsets`テーブルへの
   `INSERT ... ON CONFLICT(consumer_id) DO UPDATE SET offset = excluded.offset
   WHERE excluded.offset > consumer_offsets.offset`で実装）`.
6. In `## Known Deviations`, enhance the `EVENTBUS-007` entry's description to
   add the `migrate_legacy_offsets()` mechanism detail: it reads `.map` companion
   files to recover the original `consumer_id`, seeding `consumer_offsets`; falls
   back to the sanitized filename when no `.map` companion exists.
7. In `## Implementation Notes`, replace the レガシー移行 line (372) with a
   short pointer to `EVENTBUS-007`, e.g.:
   `- レガシー移行: `migrate_legacy_offsets()`の詳細はKnown Deviations
   EVENTBUS-007参照`.

### Method
Use `Edit` (exact-string replacement) — one call per step 2-7, so each change
remains independently reviewable in the diff.

### Details
- Do not alter `INV-01` through `INV-15`, any other `## Verification` entry, or
  any other `## Known Deviations` entry.
- Do not touch the DLQ昇格経路-related content in `### Implementation
  References` (a different section, out of this document's scope) or lines
  375-377's boilerplate (unaffected by this edit — they follow, not precede, the
  edited prose).
- Re-confirm `EVENTBUS-007`'s exact current text via `grep` immediately before
  step 6's edit, since it is a multi-line entry and the enhancement must be
  inserted precisely without disturbing its `**Type**`/`**Summary**`/`**Impact**`/
  `**Resolution Target**` fields.

## Compatibility considerations
N/A: documentation-only change; no code, config, or test reads this ADR's
Invariants/Verification/Notes/Known Deviations sections programmatically beyond
`tools/check_adr_invariant_matrix.py` (which targets `docs/adr-index.md`, not
this file directly, and is covered in Validation plan below).

## Security considerations
N/A: documentation-only change.

## Rollback considerations
Single-file, git-tracked Markdown edit — revert via
`git checkout -- docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`
if validation fails. Note this file already carries this session's prior,
still-uncommitted file-list edit (from `plans/done/20260915-154020_plan.md`) — a
rollback here must not revert that unrelated, already-completed change; scope
any revert to only this procedure's own edit (use `git diff` to confirm the
exact hunk before reverting, not a blanket checkout if other uncommitted changes
are present).

## Validation plan
- Manual diff: confirm `INV-16` added after `INV-15`, in single-sentence Japanese matching the existing style.
- Manual diff: confirm the new `## Verification` entry cites the correct test path and class.
- Manual diff: confirm both Notes prose items (370, 371) are replaced with short pointers, not fully deleted without a trace, and the `ON CONFLICT` SQL detail survives somewhere.
- Manual diff: confirm `EVENTBUS-007` retains its ID, Type, Summary, Impact, and Resolution Target fields, with only the mechanism detail added.
- Manual diff: confirm the レガシー移行 line (372) is replaced with a pointer, not silently dropped.
- `uv run pytest tests/eventbus/test_eventbus_crash_ack.py::TestCrashBeforeAck::test_offset_write_failure_after_delivery_state -v` — must still pass, confirming the cited evidence remains accurate.
- `uv run python tools/check_docs_quality.py docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` — expect zero findings.
- `uv run python tools/check_docs_structure.py docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` — expect no new finding beyond the 11-finding baseline already established this session.
- `uv run python tools/check_adr_invariant_matrix.py` — run after the sibling `docs/adr-index.md` procedure lands too (this file's new `INV-16` isn't cited by `docs/adr-index.md`'s matrix by number, only the new row added there cites this file's test) — expect zero findings.

## Completion criteria
- `INV-16` exists, single-sentence Japanese, immediately after `INV-15`.
- A `## Verification` entry for `INV-16` exists citing the confirming test.
- Neither the Monotonicity Enforcement nor the transaction-guarantee item remains
  as full duplicate prose — both are short pointers.
- `EVENTBUS-007` includes the `migrate_legacy_offsets()` mechanism detail; no new
  duplicate Known Deviation entry exists for the same mechanism.
- All Validation plan checks pass (or no new `check_docs_structure.py` finding).

## Out of scope
- The DLQ昇格経路 item and `### Implementation References` generally.
- Any other ADR-006 section.
- `docs/adr-index.md` — covered by the sibling procedure document,
  `implementations/20260915-170836_02_docs_adr-index.md.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-170836 | 20260915-180258 | Added INV-16 + Verification entry citing TestCrashBeforeAck::test_offset_write_failure_after_delivery_state; condensed transaction-guarantee/Monotonicity Notes prose to pointers; enhanced EVENTBUS-007 with migrate_legacy_offsets() mechanism detail; replaced legacy-migration prose with pointer to EVENTBUS-007 |
| 2 | Add or update tests per Validation plan | Completed | 20260915-180258 | 20260915-180258 | N/A: no new test needed — existing coverage confirmed sufficient; only a re-run to confirm it still passes Re-ran cited test: PASSED (1 passed, 0.65s) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-180258 | 20260915-180258 | N/A: documentation-only, use this document's own Validation plan instead check_docs_quality: 0 findings; check_docs_structure: 11 pre-existing unrelated findings matching established baseline |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-180258 | 20260915-180258 | N/A: this document's own target file IS the documentation being updated N/A: target file IS the documentation |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005 — reclassify ADR-006's non-file-list Implementation Notes prose
- **Source issue**: issues/done/20260914-124517_docqa03_adr-006-implementation-notes-reclassification.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-164611_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-170836
- **Related target files**: docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md