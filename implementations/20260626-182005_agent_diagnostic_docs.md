# Implementation: agent diagnostic persistence docs correction

Source plan: `plans/20260626-180402_plan.md` — Phase 2

---

## Goal

Correct all documentation that describes diagnostics as stored in `messages` table with `role="diagnostic"`, replacing it with the accurate description: diagnostics are stored exclusively in the `session_diagnostics` table via `DiagnosticStore`, and are excluded from normal session history.

---

## Scope

**In-Scope**
- `docs/05_agent_03_turn-processing-flow.md`: remove any `role="diagnostic"` language
- `docs/05_agent_04_state-and-persistence.md`: add clear "Diagnostic persistence" section
- `docs/05_agent_09_data-layer.md`: confirm `session_diagnostics` table description; clarify session restore excludes diagnostics

**Out-of-Scope**
- Code changes (DiagnosticStore is already correct)
- Changing what events are treated as diagnostics

---

## Assumptions

1. `DiagnosticStore.save()` writes to `session_diagnostics` (confirmed: diagnostic_store.py:33).
2. `fetch_messages()` queries only `messages` table — diagnostics are already excluded (confirmed: session_message_repo.py:119-121).
3. Session restore (`restore_session()`) calls `fetch_messages()` — diagnostics already excluded from restore.
4. The discrepancy exists in docs only, not in code.

---

## Implementation

### Target files
- `docs/05_agent_03_turn-processing-flow.md`
- `docs/05_agent_04_state-and-persistence.md`
- `docs/05_agent_09_data-layer.md`

### Procedure
1. Read each target doc.
2. Locate and remove any `role="diagnostic"` references or language implying diagnostics are stored in `messages`.
3. Add/update "Diagnostic persistence" description in each doc.

### Details

**Standard replacement text for all three docs:**

> Diagnostic events (LLM transport errors, partial completions, serialization events, loop guard hints) are stored in the `session_diagnostics` table via `DiagnosticStore`. They are NOT stored as rows in `messages` and are NOT included in session history retrieval, `/history` output, or session restore via `/session load`.

**Per-doc changes:**

`05_agent_03_turn-processing-flow.md`:
- Remove any sentence/paragraph referencing `role="diagnostic"` rows in `messages`.
- Add note: "Diagnostic events recorded during turn processing are persisted to `session_diagnostics`, separate from conversation messages."

`05_agent_04_state-and-persistence.md`:
- Add "Current behavior" callout: compressed history is in-memory only; DB retains original messages pending issue fix.
- Add "Diagnostic persistence" section clearly distinguishing `session_diagnostics` from `messages`.

`05_agent_09_data-layer.md`:
- Confirm/update `session_diagnostics` table description.
- Add: "Session restore (`/session load`) fetches from `messages` only. Diagnostic rows are not included."

---

## Validation Plan

| Check | Command / Action | Expected |
|---|---|---|
| Grep check | `grep -rn "role.*diagnostic\|diagnostic.*messages" docs/` | 0 hits after fix |
| Read check | Re-read changed sections | No contradictions with code |
| Test (separate doc) | See `test_agent_session_diagnostics.py.md` | tests pass |
