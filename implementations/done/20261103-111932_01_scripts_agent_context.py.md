## Goal

Give `ConversationState` (`scripts/agent/context.py`) a lock-guarded raw-swap method
`swap_history` (new) that assigns a compressed list under `self._ensure_lock` while
preserving messages appended to the pre-await list after the caller's snapshot (REQ-001;
AC-3), with unit tests proving the semantics (REQ-003 (b), (c)). This is the helper
`handle_history_compression` will call in the seq 02 document (REQ-002; AC-1).

## Scope
**Release unit**: N/A: not part of a release unit

Covers the `scripts/agent/context.py` row (seq 01) and its companion test row
`tests/agent/test_context_append_message.py` (seq 03, companion-eligible, no document of
its own) of
`plans/20261101-143236_histlock001_history-compression-bypasses-conversation-lock.md`.
Execution order for the whole plan: this document (helper + unit tests) first, then
`implementations/20261103-111932_02_scripts_agent_conversation_state_manager.py.md`
(manager + interleaving test).

## Assumptions
- Verified against current source (20261103): `ConversationState` is at
  `scripts/agent/context.py:92`; `_ensure_lock` is a lazy-init property (117-121);
  `append_message` (123), `extend_messages` (164), `replace_history` (176, async, validates
  each row with `_UNTRUSTED_RESTORE_SOURCE` defined at 61), `snapshot_messages` (191) and
  `restore_messages` (200, raw `clear` + `extend`) all take the lock; no `swap_history` (new)
  symbol exists anywhere in `scripts/` or `tests/` (rg 20261103) — the Plan's working name
  is collision-free.
- `HistoryManager.compress` result shapes confirmed in `scripts/agent/history.py`:
  no-op returns the very same list object (279, 283); summary path awaits
  `_get_summary_text` (285) and builds a new list from pre-await selection slices; the
  fallback `_fallback_truncate(history)` (288) is built after the await from the live list
  (REQ-003 (b) test shapes).
- Plan overlap judgment re-confirmed: `tools/check_plan_target_overlaps.py` (run 20261103)
  reports no overlap naming this Plan; the `context.py` co-owner `wfretry001` plan is
  completed under `plans/done/` and edits a different class (Plan Assumptions, Step 8b).
- Baselines confirmed: `context.py` 16219 B (gate 20480 B; Plan corrected 20261103);
  `radon cc`: `_sanitize_message` B(6) (existing), new method must land at rank A/B.
- `tests/agent/test_context_append_message.py` already hosts `TestAppendMessage` (15),
  `TestExtendMessages` (119) and `TestReplaceHistory` (137) against a real
  `ConversationState`.

## Design decisions
- Final signature (the Plan defers it to this document): `async def swap_history(self,
  new_history: list[LLMMessage], base_history: list[LLMMessage], base_len: int) -> None`
  — the compressed list, the pre-await list object, and the snapshot length, per Plan
  Decision 1.
- Identity, not equality, for the two guards (Plan Decision 2): same-object no-op when
  `new_history is base_history`; tail preservation only while `self.history is
  base_history`; tail members already present in `new_history` by `id()` are skipped.
- Trusted-input contract stated in the docstring: input must come from validated history
  (unlike `replace_history`, which re-validates and strips markers); points to
  `replace_history` / `restore_messages` for the other cases (Plan Risks mitigation).

## Alternatives considered
N/A: the Plan already rejected the four alternatives (lock across `compress`, reuse
`replace_history`, reuse `restore_messages`, re-run `compress`); this document adopts its
Decision 1 unchanged.

## Implementation
### Target file
`scripts/agent/context.py`

### Procedure
1. Write the red companion unit tests (see Companion test files) and confirm they fail
   (the method does not exist yet).
2. Add `swap_history` (new) to `ConversationState` next to `replace_history` /
   `restore_messages` (after line 209, at the end of the `ConversationState` class body;
   corrected 20261103: line 207 is the `async with` inside `restore_messages`), per Plan
   Decision 1:
   - `async with self._ensure_lock:` for the whole body.
   - If `new_history is base_history`: return (nothing compressed; appends are already in
     the list).
   - `extra = base_history[base_len:]` only when `self.history is base_history`, else
     `[]` (another writer reassigned the list: plain swap, preserve nothing).
   - Skip members of `extra` whose `id()` already appears in `new_history`.
   - `self.history = [*new_history, *extra]` (reassignment, not in-place
     `clear`/`extend`, per the Plan's compatibility Assumption).
3. Update the module/class docstring only if it enumerates lock-guarded methods; the method
   docstring itself states the trusted-input contract and the difference from
   `replace_history` (REQ-001).

### Method
One additive async method (~10 lines) inside the existing lock discipline; no existing
method or signature changes.

### Details
- `extra` filtering: build `{id(m) for m in new_history}` once; identity dedup handles the
  fallback-truncate shape whose list already holds the appended tail (REQ-003 (b)).
- Expected radon rank for the method: A-B (three decision points: same-object return,
  `self.history is` check, comprehension filter).
- Ephemeral and summary markers pass through untouched: the method never calls
  `validate_message` or `_sanitize_message` (REQ-001; AC-3).

### Companion test files
- `tests/agent/test_context_append_message.py` (companion of the `scripts/agent/context.py`
  row; Plan `Implementation Target Files` seq 03 covered here per the companion rule)
  - Procedure: add a `TestSwapHistory` (new) class next to `TestReplaceHistory` using a
    real `ConversationState`, covering REQ-003 (b), (c) / AC-3: (i) empty tail → plain swap;
    (ii) tail appended after the snapshot via `append_message` is preserved after the
    compressed messages, exactly once; (iii) same-object result (`new_history is
    base_history`) changes nothing; (iv) fallback-shaped new list that already contains the
    tail by identity → no duplication; (v) ephemeral and summary markers survive the swap,
    contrasted with `replace_history` stripping them (the existing `TestReplaceHistory`
    pattern); (vi) `self.history` reassigned to a different object → tail not preserved,
    plain swap (Plan Decision 2).
  - Validation: `uv run pytest tests/agent/test_context_append_message.py` — red before
    Procedure 2, green after.

## Compatibility considerations
- Purely additive method on a class imported by about 30 modules; no existing signature
  changes (Plan Design, Path B analysis).
- `tools/generate_reference_table.py --check` must pass; if it reports drift for the new
  public method, regenerate with `uv run python tools/generate_reference_table.py
  --manifests` (same lesson as the dupcallid001 cycle).
- No `docs/` change: the Plan's Documentation Impact is N/A (no `docs/*.md` describes the
  compression swap or the history lock).

## Security considerations
- The method bypasses per-message validation by design (trusted internal input only); the
  docstring must make the contract explicit so it is not mistaken for a `replace_history`
  replacement for untrusted input (REQ-001; Plan Risks).

## Rollback considerations
- Single additive method plus tests; revert the commit removes the helper (the seq 02
  manager change must be reverted with it — they land in one commit).

## Validation plan
1. `uv run pytest tests/agent/test_context_append_message.py tests/agent/test_context.py`
   — new and existing tests pass (AC-3).
2. Static: `uv run ruff check scripts/agent/context.py
   tests/agent/test_context_append_message.py`, `uv run ruff format --check` on both,
   `uv run mypy scripts/agent/context.py` — no findings.
3. Complexity / security / size: `radon cc scripts/agent/context.py -s` (no rank above B),
   `uv run bandit -r scripts/agent/context.py -c pyproject.toml` (no new finding),
   `uv run python tools/check_module_size.py` (under 20480 B; currently 16219 B).
4. `uv run python tools/generate_reference_table.py --check` — no table drift (see
   Compatibility for the regeneration path).
5. Full validation sequence per `rules/toolchain.md` runs once at the end of the plan's
   execution (both procedure documents); deploy is a hand-off to `skills/deploy/SKILL.md`
   after commit and push, and is the user's decision.

## Completion criteria
- AC-3: unit tests show the method holds `self._ensure_lock`, preserves appended messages,
  no-ops on the same-object result, does not duplicate identity-present messages, and keeps
  ephemeral/summary markers intact (unlike `replace_history`).
- AC-1 (second half — no direct assignment in the manager) is completed and verified by
  the seq 02 document.
- REQ-004 audit re-scan recorded in the seq 02 document's Execution Status (its row cites
  REQ-004).

## Out of Scope
- `handle_history_compression` and the interleaving test (seq 02 document).
- Sibling direct assignments of `ctx.conv.history` in `/compact`, `/undo`, `/clear`
  (UNK-01, owner's follow-up decision).
- `replace_history` / `restore_messages` behavior, new locks, `HistoryManager.compress`
  internals (`scripts/agent/history.py` read-only), any `docs/` change (REQ-001 Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write red `TestSwapHistory` (new) unit tests, confirm they fail (Procedure 1; Companion test files) | Completed | 20261103-162200 | 20261103-163505 | 6 companion cases + 1 lock-spy case (AC-3 `self._ensure_lock`), red confirmed |
| 2 | Implement `swap_history` (new) per Decision 1 + docstring contract (Procedure 2-3) | Completed | 20261103-162200 | 20261103-163505 | async def, `async with self._ensure_lock` whole body, 3-arg signature per Final signature; inserted after `restore_messages` (end of class body) |
| 3 | Run this document's checks (Validation plan 1-4) | Completed | 20261103-162200 | 20261103-163505 | targeted pytest 50 passed/1 skipped; ruff check+format clean; mypy clean; radon `-nc` empty (no C+); bandit exit 0; check_module_size OK (context.py 17625 B); reference_table --check: no drift |

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
- **Requirement ID**: REQ-001 (lock-guarded raw swap preserving appended messages),
  REQ-003 (unit tests for the helper's result shapes and marker handling), REQ-002 (the
  manager use this helper enables — carried out in the seq 02 document)
- **Source issue**: issues/20261003-180339_histlock001_history-compression-bypasses-conversation-lock.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-143236_histlock001_history-compression-bypasses-conversation-lock.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-111932
- **Related target files**: `scripts/agent/context.py`, `tests/agent/test_context_append_message.py`