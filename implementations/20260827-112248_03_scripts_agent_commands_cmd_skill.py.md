## Goal

Update `cmd_skill.py`'s stale explanatory comment (REQ-001) to describe the fixed
clearing mechanism instead of a permanent, accepted limitation, per
`plans/20260826-121839_plan.md`.

## Scope

- In scope: the comment block (verified at lines ~50-59 as of 2026-08-27) only —
  no behavior change.
- Out of scope: `cmd_skill.py`'s `append_message()` call itself, its own
  `_skill_ephemeral` filter list comprehension (both unchanged, both still
  correct); any other file.

## Assumptions

- **Depends on seq 02 (`orchestrator.py`) landing in the same change** — this
  comment update describes the fixed behavior that seq 02's `_EPHEMERAL_KEYS`
  change actually implements; do not apply this comment update in isolation
  before that code change lands, or the comment would describe behavior that
  does not yet exist.
- Same sign-off gate as seq 02 applies here — per this Plan's Design section, the
  comment update is part of REQ-001's single implementation step (Phase 2,
  "Explicit sign-off gates"); both files land together, gated on the same sign-off.

## Design decisions

- Replace the "known, accepted... do not fix without review" framing with text
  describing the current (fixed) mechanism: `_ephemeral` is still stripped at
  append time (harmless — `_skill_ephemeral` alone now suffices for the
  orchestrator's sweep to match), and the message is cleared by the
  orchestrator's generic sweep at the very next turn boundary, same as any other
  ephemeral message — per this Plan's own Implementation steps wording (Phase 2,
  item 2).
- Keep a reference to the historical context (the prior implementation-procedure
  doc that introduced this gap) for future readers, but reframe it as resolved
  history, not an active caveat.

## Alternatives considered

- Deleting the comment entirely (since the gap is now fixed) was considered and
  rejected — a future reader benefits from knowing this mechanism was once broken
  and is now intentionally fixed, especially since the "do not fix without review"
  language specifically warned against a different, rejected fix (touching
  `TRUSTED_SOURCES`) that a future contributor might otherwise still attempt.

## Implementation
### Target file
`scripts/agent/commands/cmd_skill.py`

### Procedure
1. Confirm seq 02 (`orchestrator.py`'s `_EPHEMERAL_KEYS` change) has landed or is
   landing in the same change.
2. Replace the comment block per Method/Details.
3. Run `uv run pytest tests/agent/commands/test_cmd_skill.py -v` and separately
   re-confirm the pre-existing failure count/cause (see this Plan's UNK-02) is
   unchanged — not newly introduced by this comment-only edit (comment changes
   cannot introduce test failures, but confirm as a sanity check per this Plan's
   Phase 3 instruction).

### Method
Direct text edit (Edit tool) — one comment block, no code logic change.

### Details
Current comment (verified 2026-08-27, preceding the `await
ctx.conv.append_message(...)` call):
```python
        # source="skill_mixin" only authorizes "_skill_ephemeral" in
        # TRUSTED_SOURCES (message_schema.py); "_ephemeral" is therefore
        # stripped by append_message()'s sanitize-and-log fallback. This is a
        # known, accepted retention-window change (see
        # implementations/done/20260726-101004_mode_classification_and_cmd_skill.py.md):
        # skill context is no longer auto-cleared by the orchestrator's
        # generic "_ephemeral" sweep at the next turn boundary; it is still
        # cleared by this file's own "_skill_ephemeral" filter above on the
        # next /skill invocation. Do not "fix" this by adding "_ephemeral" to
        # TRUSTED_SOURCES["skill_mixin"] without review.
```
Replace with text stating: `source="skill_mixin"` only authorizes
`"_skill_ephemeral"` in `TRUSTED_SOURCES` (`message_schema.py`); `"_ephemeral"` is
therefore stripped by `append_message()`'s sanitize-and-log fallback, which is
harmless — `Orchestrator._EPHEMERAL_KEYS` (`orchestrator.py`) now also matches on
`"_skill_ephemeral"` directly, so skill context is cleared by the orchestrator's
generic sweep at the very next turn boundary, same as any other ephemeral message
(fixed by `plans/done/20260826-121839_plan.md` — the prior gap is described in
`implementations/done/20260726-101004_mode_classification_and_cmd_skill.py.md`).
This file's own `"_skill_ephemeral"` filter above remains as a redundant,
harmless no-op safeguard for the next `/skill` invocation.

Verify the exact archived-plan path reference (`plans/done/20260826-121839_...`)
matches this Plan's own filename once it is actually moved to `plans/done/` at
Step 4 of the plan-to-implementation-procedure workflow — if this comment update
lands before that move, reference the plan by its current `plans/` path instead.

## Compatibility considerations

- Comment-only; no behavior change (this Plan's own Affected areas table confirms
  "no behavior change" for this file).

## Security considerations

- N/A: comment-only change.

## Rollback considerations

- Comment-only revert via `git diff`/`git checkout -- scripts/agent/commands/cmd_skill.py`;
  should be reverted together with seq 02 if reverting the fix as a whole, but this
  file's revert alone has no functional effect.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/commands/cmd_skill.py` | Regression | `uv run pytest tests/agent/commands/test_cmd_skill.py -v` | Same pass/fail pattern as the pre-existing baseline (this Plan's UNK-02: 8 pre-existing unrelated `RuntimeWarning: coroutine ... was never awaited` failures) — no new failures attributable to this comment-only change |

## Completion criteria

- The comment no longer describes the gap as a permanent, accepted limitation.
- The comment describes the current (fixed) clearing mechanism.

## Out of scope

- `append_message()` call and its arguments.
- The file's own `_skill_ephemeral` filter list comprehension.
- REQ-002 (separate target files).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm seq 02 has landed or lands together | Pending | — | — | |
| 2 | Replace the comment block | Pending | — | — | |
| 3 | Run `uv run pytest tests/agent/commands/test_cmd_skill.py -v`, confirm baseline unchanged | Pending | — | — | Pre-existing 8 failures (UNK-02) expected, unrelated to this change |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | Same sign-off gate as seq 02 applies (see that procedure's Blocker Log) | No | — |

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
- **Related target files**: `scripts/agent/commands/cmd_skill.py`
