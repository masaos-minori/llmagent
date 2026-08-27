## Goal

Add `"_skill_ephemeral"` to `Orchestrator._EPHEMERAL_KEYS` (REQ-001) so `/skill`-
injected system context is cleared at the very next turn boundary, per
`plans/20260826-121839_plan.md`.

## Scope

- In scope: `_EPHEMERAL_KEYS` frozenset literal (verified at line 123 as of
  2026-08-27) only.
- Out of scope: `agent.message_schema.TRUSTED_SOURCES`/`ROLE_KEY_WHITELIST` (the
  alternative fix this Plan explicitly rejected — see Design); any other
  `Orchestrator` method; `cmd_skill.py`'s own filter list comprehension (stays
  correct, becomes a harmless no-op).

## Assumptions

- **BLOCKING GATE, not yet satisfied**: this Plan's `rules/coding.md` "Explicit
  sign-off gates" citation requires a maintainer comment on
  `plans/20260826-121839_plan.md` explicitly confirming the option-2 approach
  (aligning `_EPHEMERAL_KEYS`, not changing `TRUSTED_SOURCES`) is acceptable,
  BEFORE this code change lands — re-verified 2026-08-27 that no such sign-off
  comment or note currently exists on the Plan file or in git history for it. Do
  not apply this item's code change until that sign-off is obtained and recorded.
- `cmd_skill.py` is the only current producer of `_skill_ephemeral` — re-verified
  2026-08-27 via `rg -n "_skill_ephemeral" scripts/`, finding it only in
  `cmd_skill.py`, `message_schema.py`'s `TRUSTED_SOURCES` entry, and
  `shared/types.py`'s `LLMMessage` field declaration.
- `TRUSTED_SOURCES["skill_mixin"] == {"_skill_ephemeral"}` (re-verified 2026-08-27
  at `message_schema.py:21`) is unaffected by this change — this item does not
  touch `message_schema.py`.

## Design decisions

- Add `"_skill_ephemeral"` to the existing frozenset literal — a one-line change,
  per this Plan's Design section's chosen "option 2" (align the clearing logic),
  not "option 1" (authorize `_ephemeral` for `source="skill_mixin"`, which would
  touch the security-tested `TRUSTED_SOURCES` contract).
- This is the narrower, single-file fix specifically because the existing
  `cmd_skill.py` code comment flags option 1 as requiring review — see the
  Blocking Gate above.

## Alternatives considered

- Option 1 (`TRUSTED_SOURCES["skill_mixin"] = {"_skill_ephemeral", "_ephemeral"}`)
  was considered and rejected by this Plan's own Design section — it would touch a
  security-relevant, explicitly-tested contract
  (`tests/agent/test_ephemeral_filtering_security.py:398`,
  `tests/agent/test_message_schema.py:251` both assert the current value by name)
  for no additional benefit over the chosen option 2.

## Implementation
### Target file
`scripts/agent/orchestrator.py`

### Procedure
1. **Confirm the sign-off gate above is satisfied** — do not proceed past this
   step without it.
2. Re-run `rg -n "read_active" .` and `rg -n "_skill_ephemeral" scripts/`
   immediately before editing, to confirm no new caller/producer landed since this
   Plan was written (per this Plan's own Phase 1 preparation step).
3. Change line 123 from `_EPHEMERAL_KEYS: frozenset[str] = frozenset({"_ephemeral",
   "_memory_injected"})` to `frozenset({"_ephemeral", "_memory_injected",
   "_skill_ephemeral"})`.
4. Run `uv run pytest tests/agent/test_orchestrator.py -v` (will show the new
   `_skill_ephemeral` assertion failing until seq 05, this same pass, is also
   applied — or passing if this item lands after that test addition).

### Method
Direct code edit (Edit tool) — one frozenset literal, one added string element.

### Details
Current code (verified 2026-08-27, line 123):
```python
    _EPHEMERAL_KEYS: frozenset[str] = frozenset({"_ephemeral", "_memory_injected"})
```
Change to:
```python
    _EPHEMERAL_KEYS: frozenset[str] = frozenset(
        {"_ephemeral", "_memory_injected", "_skill_ephemeral"}
    )
```
No other line in this file references `_EPHEMERAL_KEYS`'s literal contents besides
`_clear_previous_turn_ephemeral_messages()` (verified at line 558's call site,
which reads the set generically — no per-key branching to update).

## Compatibility considerations

- Only messages carrying `_skill_ephemeral` are newly affected — per this Plan's
  Assumptions, `cmd_skill.py` is the sole producer, so blast radius is confined to
  the `/skill` code path.
- `_ephemeral` is still stripped from stored `skill_mixin`-sourced messages by
  `validate_message()`'s sanitize-and-log fallback (unchanged) — this item does not
  restore `_ephemeral` to those messages, it makes the orchestrator's sweep also
  match on `_skill_ephemeral` directly.

## Security considerations

- This item deliberately avoids touching `TRUSTED_SOURCES` (a security-relevant
  contract) — confirm after the edit that
  `tests/agent/test_ephemeral_filtering_security.py` and
  `tests/agent/test_message_schema.py` both still pass unchanged, proving that
  contract was not disturbed.

## Rollback considerations

- Single-line revert via `git diff`/`git checkout -- scripts/agent/orchestrator.py`;
  independent of seq 03 (`cmd_skill.py`'s comment update) — reverting this file
  alone would leave `cmd_skill.py`'s comment describing a fix that no longer
  exists, so revert both together if reverting at all.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/orchestrator.py` | Unit | `uv run pytest tests/agent/test_orchestrator.py -v` | New `_skill_ephemeral` regression test passes once seq 05 is also applied |
| `scripts/agent/orchestrator.py` | Regression | `uv run pytest tests/agent/test_ephemeral_filtering_security.py tests/agent/test_message_schema.py -v` | All pass unchanged — confirms `TRUSTED_SOURCES` untouched |

## Completion criteria

- The sign-off gate is satisfied and recorded before this change is applied.
- `_EPHEMERAL_KEYS` includes `"_skill_ephemeral"`.
- A `_skill_ephemeral`-only history message is removed by
  `_clear_previous_turn_ephemeral_messages()` on the next turn.

## Out of scope

- `agent.message_schema.TRUSTED_SOURCES`/`ROLE_KEY_WHITELIST`.
- `cmd_skill.py`'s own filter list comprehension.
- REQ-002 (memory module dead-code removal, separate target files).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Obtain and record explicit maintainer sign-off | Pending | — | — | BLOCKING — do not proceed to step 3 without this |
| 2 | Re-run `rg` re-verification greps immediately before editing | Pending | — | — | |
| 3 | Add `"_skill_ephemeral"` to `_EPHEMERAL_KEYS` | Pending | — | — | |
| 4 | Run `uv run pytest tests/agent/test_orchestrator.py -v` | Pending | — | — | Requires seq 05 applied |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Explicit maintainer sign-off on the option-2 approach not yet obtained (see `rules/coding.md` Explicit sign-off gates, cited by this Plan's Design section) | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001
- **Source issue**: `issues/20260821_08_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-121839_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-112248
- **Related target files**: `scripts/agent/orchestrator.py`
