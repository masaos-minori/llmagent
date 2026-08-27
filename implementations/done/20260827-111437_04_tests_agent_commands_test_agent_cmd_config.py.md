## Goal

Extend `tests/agent/commands/test_agent_cmd_config.py`'s `TestCmdReload` class with a
characterization test for the new "LIVE" render line (REQ-005), per
`plans/20260826-120102_plan.md`.

## Scope

- In scope: one or two new test methods in `TestCmdReload` asserting the "LIVE" line
  appears when `always_live` is populated, and does not appear when it is not.
- Out of scope: existing `TestCmdReload` tests (`test_reload_shows_startup_only_items`,
  `test_reload_no_changes_shows_message`, etc. — unaffected reference patterns, not
  modified unless seq 02's `cmd_config.py` change alters their expected output,
  which it should not per that item's Compatibility considerations); any other test
  class in this file.

## Assumptions

- `scripts/agent/commands/cmd_config.py`'s `_cmd_reload()` has been (or is being, in
  this same pass, seq 02) updated to render `result.always_live` via
  `_write_item_list(..., "Live via config file (no restart or /reload needed)",
  "LIVE")` and to exclude `always_live` from the "No changes detected." branch —
  this test's assertions depend on that exact wording; if seq 02's actual wording
  differs from its own draft, update these assertions to match the final wording,
  not the other way around.
- **Correction (plan-to-implementation-procedure adversarial verification,
  2026-08-27)**: this Plan originally named `tests/agent/commands/
  test_cmd_config_char.py` as REQ-005's target — verified 2026-08-27 that file
  contains no `_cmd_reload`/`TestCmdReload` tests at all (its characterization tests
  cover unrelated `_ConfigMixin` output methods). The actual `TestCmdReload` class
  is in this file (`test_agent_cmd_config.py`, lines 378-580), including the
  `test_reload_shows_startup_only_items` pattern this Requirement explicitly
  mirrors. This procedure targets the corrected file.

## Design decisions

- Mirror `test_reload_shows_startup_only_items`'s exact structure (verified 2026-08-27,
  lines 530-556): construct a `ConfigReloadOutcome` directly with the relevant field
  populated, patch `ConfigReloadService.apply_config_dict` to return it, call
  `cmd._cmd_reload()`, assert on `capsys` output — rather than exercising the real
  detector end-to-end (that path is already covered by seq 03's unit tests).
- Add a second test mirroring `test_reload_no_changes_shows_message` (lines 558-573)
  but with `startup_only=[]` and `always_live=[]` both explicitly empty, to confirm
  "No changes detected." still appears when nothing changed at all (regression guard
  for REQ-003's condition change).

## Alternatives considered

- Testing only the "LIVE" line's presence (skipping the "does not appear when
  empty" case) was considered and rejected — REQ-005 explicitly requires both the
  present and absent cases, and `test_reload_no_changes_shows_message` is the
  existing test whose behavior REQ-003's condition change must not break, so adding
  an explicit assertion here is the direct regression guard for that risk.

## Implementation
### Target file
`tests/agent/commands/test_agent_cmd_config.py`

### Procedure
1. Add `test_reload_shows_always_live_items` to `TestCmdReload`, mirroring
   `test_reload_shows_startup_only_items`'s structure with `always_live=[
   "diagnostics.retention_days"]`.
2. Confirm `test_reload_no_changes_shows_message` (lines 558-573) still passes
   unchanged after seq 02's `cmd_config.py` edit — add an explicit assertion or a
   new test if the existing one does not already cover the always_live-empty case.
3. Run `uv run pytest tests/agent/commands/test_agent_cmd_config.py -v`.

### Method
Direct file edit (Edit tool) — one new test method in `TestCmdReload`; verify (not
necessarily modify) one existing test.

### Details
New test method (mirroring lines 530-556):
```python
def test_reload_shows_always_live_items(self, capsys: Any) -> None:
    """Characterization test for the always_live item-listing branch."""
    from unittest.mock import patch

    from agent.services.config_reload import ConfigReloadOutcome

    ctx = _make_ctx()
    ctx.conv.history = []
    cmd = _FakeCmd(ctx)
    outcome = ConfigReloadOutcome(
        applied=[], needs_restart=[], always_live=["diagnostics.retention_days"]
    )
    with (
        patch("shared.config_loader.ConfigLoader.load_all", return_value={}),
        patch(
            "agent.services.config_reload.ConfigReloadService.apply_config_dict",
            return_value=outcome,
        ),
    ):
        cmd._cmd_reload()
    out = capsys.readouterr().out
    assert "Config reloaded — no /reload action needed for changed settings" in out
    assert "Live via config file (no restart or /reload needed): [1 items]" in out
    assert "  [LIVE] - diagnostics.retention_days" in out
```
Adjust the exact expected strings to match seq 02's final wording (this draft
mirrors this Plan's own proposed phrasing, which seq 02's own Assumptions note the
implementer may adjust). Confirm `test_reload_no_changes_shows_message` (currently
constructing `ConfigReloadOutcome(applied=[], needs_restart=[])` with `always_live`
implicitly defaulting to `[]`) still asserts `"No changes detected." in out` — this
should hold automatically once seq 02 is implemented correctly (the default empty
list is falsy), but re-run this specific test after seq 02 lands to confirm no
regression.

## Compatibility considerations

- Test-only change; no production code path is affected.
- Depends on seq 02 (`cmd_config.py`) landing in the same change for the new test's
  wording assertions to pass.

## Security considerations

- Confirm the new test's assertions do not encode an expectation that a real
  `encryption_key` value would ever be printed — the example field name used
  (`diagnostics.retention_days`) deliberately avoids the encryption-key field for
  this reason; if a follow-up test specifically covers `diagnostics.encryption_key`,
  assert only the field *name* appears, never a value.

## Rollback considerations

- Single-method addition revert via `git diff`/`git checkout -- <path>`; must be
  reverted together with seq 02 (`cmd_config.py`) in this same pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/agent/commands/test_agent_cmd_config.py` | Characterization | `uv run pytest tests/agent/commands/test_agent_cmd_config.py -v` | New "LIVE" test passes once seq 02 has also landed; `test_reload_no_changes_shows_message` and other `TestCmdReload` tests remain green |

## Completion criteria

- A test confirms the "LIVE" line appears when `always_live` is populated.
- `test_reload_no_changes_shows_message` (or an equivalent explicit assertion)
  confirms "No changes detected." still appears when `always_live` is empty.

## Out of scope

- `test_cmd_config_char.py` (confirmed unrelated to `_cmd_reload`, see Assumptions).
- Any other test class in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `test_reload_shows_always_live_items` | Completed | 2026-08-28 | 2026-08-28 | Test passes |
| 2 | Confirm `test_reload_no_changes_shows_message` still passes | Completed | 2026-08-28 | 2026-08-28 | Also added explicit regression guard |
| 3 | Run `uv run pytest tests/agent/commands/test_agent_cmd_config.py -v` | Completed | 2026-08-28 | 2026-08-28 | All 11 TestCmdReload tests pass |

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
- **Source issue**: `issues/20260821_06_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-120102_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-111437
- **Related target files**: `tests/agent/commands/test_agent_cmd_config.py`
