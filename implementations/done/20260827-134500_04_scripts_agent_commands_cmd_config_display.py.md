## Goal

Remove the `tool_cache_ttl` display line from `/config`'s settings output, which
would otherwise raise `AttributeError` once `REQ-001` removes
`ToolConfig.tool_cache_ttl` — the same bug class as the already-fixed
`cmd_config_stats.py` regression (`REQ-004`) — per
`plans/20260827-121312_plan.md`'s `REQ-005`.

## Scope

- In scope: the single `self._out.write(...)` call rendering `tool_cache_ttl`
  (verified at line 48 as of 2026-08-27, inside `cmd_config_display.py`'s settings
  print method).
- Out of scope: every other `self._out.write(...)` line in the same method/file
  (all read fields that remain on `ToolConfig`/`LLMConfig` after `REQ-001`).

## Assumptions

- `REQ-001` lands in the same commit — without it, this step alone is a harmless
  cosmetic removal (a still-valid field simply stops being displayed); the bug
  this step prevents only manifests once `REQ-001`'s field removal lands without
  this step.
- No other line in `cmd_config_display.py` reads `tool_cache_ttl` or
  `tool_cache_max_size` — confirmed via `rg -n "tool_cache_ttl|tool_cache_max_size"
  scripts/agent/commands/cmd_config_display.py` showing only the one line this
  step targets.
- Unlike `cmd_config_stats.py`'s `_safe()` helper (a guarded read with a
  `getattr` default-value bug), this line accesses `ctx.cfg.tool.tool_cache_ttl`
  directly with an f-string — no guard exists at all, so it fails identically
  (unconditionally) once the attribute is gone.

## Design decisions

- Delete the line outright rather than guarding it with a `getattr(...,
  default)` fallback — the field is being permanently removed from `ToolConfig`
  (`REQ-001`), so a defensive read would display a fabricated value for a
  setting that no longer exists, which is more misleading than not displaying it
  at all. This mirrors `REQ-004`'s resolution (delete the stat, don't guard the
  read).

## Alternatives considered

- Wrap the read in `getattr(ctx.cfg.tool, "tool_cache_ttl", None)` and skip
  printing if `None`: rejected — adds permanent defensive code for a field being
  intentionally deleted, and risks masking a future, unrelated `AttributeError`
  on the same line if another field is added there later.

## Implementation
### Target file
`scripts/agent/commands/cmd_config_display.py`

### Procedure
1. Re-run `rg -n "tool_cache_ttl" scripts/agent/commands/cmd_config_display.py`
   immediately before editing to confirm the line number has not drifted since
   2026-08-27.
2. Delete the `tool_cache_ttl` display line.
3. Check whether any existing test in
   `tests/agent/commands/test_agent_cmd_config.py` asserts on the printed
   `tool_cache_ttl` line's exact text (as opposed to merely setting the mock
   attribute) — `TestPrintConfigValues._make_cfg_ctx()` (line 188 as of
   2026-08-27) sets `ctx.cfg.tool.tool_cache_ttl = 300.0` on a `MagicMock`, but no
   assertion in this file currently checks the printed output for that value
   (confirmed via `rg -n "tool_cache_ttl" tests/`). Since `ctx.cfg.tool` is a
   `MagicMock`, leaving this now-unread setup line in place will not break the
   test (no `AttributeError` on an unused mock attribute) — remove it anyway for
   cleanliness (dead test setup), but do not treat its removal as required for
   correctness.
4. Run `uv run pytest tests/agent/commands/test_agent_cmd_config.py -k
   "PrintConfigValues" -v`.

### Method
Direct text edit (Edit tool) — remove one line from the source file, one dead
setup line from the test file (best-effort cleanup, not a correctness
requirement).

### Details
Current text (verified 2026-08-27, lines 44-49):
```python
        self._out.write(
            f"  context_compress    : {ctx.cfg.llm.context_compress_turns} turn pairs",
        )
        self._out.write(f"  tool_cache_ttl      : {ctx.cfg.tool.tool_cache_ttl}s")
        self._out.write(f"  llm_max_retries     : {ctx.cfg.llm.llm_max_retries}")
```
Change to:
```python
        self._out.write(
            f"  context_compress    : {ctx.cfg.llm.context_compress_turns} turn pairs",
        )
        self._out.write(f"  llm_max_retries     : {ctx.cfg.llm.llm_max_retries}")
```

Optional test cleanup (verified 2026-08-27,
`tests/agent/commands/test_agent_cmd_config.py:188`):
```python
        ctx.cfg.tool.tool_cache_ttl = 300.0
```
Remove this line from `TestPrintConfigValues._make_cfg_ctx()` — it becomes dead
setup once the source line is removed (best-effort; not required for tests to
pass, since `ctx.cfg.tool` is a `MagicMock` and tolerates the unused attribute).

## Compatibility considerations

- `/config` output format changes: the `tool_cache_ttl` line no longer appears.
  No other consumer parses `/config`'s output programmatically (it is a
  human-readable CLI command) — confirmed via `rg -rn "cmd_config_display\|_print_settings"
  scripts/` showing no downstream parser.

## Security considerations

- N/A: display-only change, no security-relevant behavior.

## Rollback considerations

- Single-line revert via `git diff` / `git checkout --
  scripts/agent/commands/cmd_config_display.py`.
- Should land together with `REQ-001` per Design, but is independently safe to
  apply first (removing a still-valid field's display line is not a regression
  by itself) — only reverting `REQ-001` after this step lands would be
  order-sensitive, and that scenario is not part of this Plan's intended
  sequence.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/commands/cmd_config_display.py` | Static | `rg -n "tool_cache_ttl" scripts/agent/commands/cmd_config_display.py` | No matches |
| `tests/agent/commands/test_agent_cmd_config.py` | Unit | `uv run pytest tests/agent/commands/test_agent_cmd_config.py -k "PrintConfigValues" -v` | All pass |
| Manual (post-`REQ-001`) | Smoke test | Invoke `/config` against a running agent | No `AttributeError`; output omits the `tool_cache_ttl` line |

## Completion criteria

- `rg -n "tool_cache_ttl" scripts/agent/commands/cmd_config_display.py` returns
  no matches.
- `/config` does not raise `AttributeError` after `REQ-001` lands.

## Out of scope

- Every other `self._out.write(...)` line in `cmd_config_display.py`.
- `config_dataclasses.py` (`REQ-001`), `config_builders.py` (`REQ-002`),
  `config_validators.py` (`REQ-003`) — separate implementation procedures.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm current line number | Pending | — | — | |
| 2 | Delete `tool_cache_ttl` display line | Pending | — | — | |
| 3 | Check/clean dead test setup line | Pending | — | — | Best-effort, not correctness-required |
| 4 | Run `PrintConfigValues` tests | Pending | — | — | Coordinate landing with REQ-001 |

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
- **Requirement ID**: REQ-005
- **Source issue**: `issues/done/20260827_toolexecutor_cache_removal_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260827-121312_plan.md`
- **Source implementation procedure**: N/A: this bug was newly found during this
  plan-to-implementation-procedure cycle's second pass (2026-08-27); no prior
  implementation procedure targeted this file
- **Generated at**: 20260827-134500
- **Related target files**: `scripts/agent/commands/cmd_config_display.py`,
  `tests/agent/commands/test_agent_cmd_config.py` (test cleanup only)
