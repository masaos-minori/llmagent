## Goal

Update `docs/05_agent_03_turn-processing-flow.md` to correctly describe `ToolLoopGuard` behavior as **fail-fast (loop termination)**, replacing the incorrect "inject hint to LLM" claim. Design decision confirmed: fail-fast is the intended behavior. Option A applies.

## Scope

**In**: `docs/05_agent_03_turn-processing-flow.md` — ToolLoopGuard description section (approximately lines 100–103). Rewrite the 4 bullet points and add a diagnostic note.

**Out**:
- No Python source files are modified (fail-fast is already the correct implementation).
- No other doc files.
- `_save_guard_hint()` diagnostic persistence path — unchanged and must not be touched.

## Assumptions

1. The section at lines 100–103 contains exactly 4 bullet points (Dedup, Cycle detection, Retry, Consecutive error). Confirmed by grep during planning.
2. No other documentation files repeat the "inject hint" claim. Verify with `grep -rn "inject hint" docs/` before closing.
3. The hint strings (`DEDUP_HINT`, `CYCLE_HINT`, `RETRY_HINT`) and the `_save_guard_hint()` mechanism remain in the code as diagnostic-only paths. The doc should acknowledge their existence.

## Implementation

### Target file
`docs/05_agent_03_turn-processing-flow.md`

### Procedure
1. Read lines 96–110 to confirm exact current wording and surrounding context.
2. Replace the 4 bullet points (lines 100–103) with the corrected description.
3. Add a callout note explaining the diagnostic-only hint storage.
4. Verify no other occurrences of "inject hint" remain in `docs/`.

### Method
Direct file edit.

### Details

**Locate and replace** the section containing these lines (exact content may vary slightly — match by content, not strictly by line number):

```markdown
# Before (approximately lines 100–103)
- **Dedup:** same `(name, args)` seen > `tool_dedup_max_repeats` times → inject hint
- **Cycle detection:** same tool sequence in last `tool_cycle_detect_window` rounds → warn
- **Retry:** errored `(name, args)` called again > `tool_error_retry_max` → block
- **Consecutive error:** all tools in a round errored `tool_error_max_consecutive` times → break loop
```

**Replace with:**

```markdown
- **Dedup:** same `(name, args)` seen ≥ `tool_dedup_max_repeats` times → terminate loop;
  user sees `"Repeated tool call detected."`; hint stored in `session_diagnostics`
  (`kind='guard_hint'`, `guard_type='dedup'`).
- **Cycle detection:** same tool-call fingerprint repeated in the last
  `tool_cycle_detect_window` rounds → terminate loop;
  user sees `"Cyclic tool call pattern detected."`;
  hint stored in `session_diagnostics` (`kind='guard_hint'`, `guard_type='cycle'`).
- **Retry:** errored `(name, args)` called again → terminate loop;
  user sees `"Repeated failed tool call detected."`;
  hint stored in `session_diagnostics` (`kind='guard_hint'`, `guard_type='retry'`).
- **Consecutive error:** all tools in a round errored `tool_error_max_consecutive` times
  → terminate loop; user sees `"Too many consecutive tool errors."`.

> **Note:** Guard hints (`DEDUP_HINT`, `CYCLE_HINT`, `RETRY_HINT`) are stored in
> `session_diagnostics` under `kind='guard_hint'` for offline diagnostics only.
> They are **not** injected into `ctx.conv.history` and the LLM does not see them.
> The loop terminates immediately on any guard hit.
```

**After the edit**, verify:
```bash
grep -rn "inject hint" docs/
```
Expected: 0 matches.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| "inject hint" removed from docs | `grep -rn "inject hint" docs/` | 0 matches |
| "terminate loop" present in updated section | `grep -n "terminate loop" docs/05_agent_03_turn-processing-flow.md` | ≥ 1 match |
| Diagnostic note present | `grep -n "not.*injected\|not.*ctx.conv.history" docs/05_agent_03_turn-processing-flow.md` | ≥ 1 match |
| Existing guard tests pass (no code change) | `uv run pytest tests/agent/test_tool_loop_guard.py -v` | All green |
| No other sections modified | `git diff docs/05_agent_03_turn-processing-flow.md` | Only the guard behavior section |
