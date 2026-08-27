## Goal

Update `_cmd_reload()` to render `result.always_live` with accurate wording and stop
misreporting "No changes detected." when only `diagnostics.*` changed (REQ-003), per
`plans/20260826-120102_plan.md`.

## Scope

- In scope: `_cmd_reload()`'s branch structure (verified at lines 60-95 as of
  2026-08-27) in this one file.
- Out of scope: any other command in this file; any change to
  `ConfigReloadService`/`ConfigReloadOutcome` themselves (separate target file,
  seq 01, in this same pass).

## Assumptions

- `scripts/agent/services/config_reload.py`'s `ConfigReloadOutcome` has (or is
  gaining, in this same pass, seq 01) an `always_live: list[str]` field populated by
  `_detect_diagnostics_live_fields()` — this file's render logic depends on that
  field existing.
- The exact "LIVE" label and "Live via config file (no restart or /reload needed)"
  wording are this Plan's proposed phrasing (per its own Assumptions) — the
  implementer may adjust exact wording as long as it does not claim a restart is
  required.

## Design decisions

- Add `result.always_live` as a third condition in the initial `if`/`elif` chain
  (per this Plan's Design section), reusing the existing additive
  `if result.<category>:` + `_write_item_list()` pattern already used for
  `applied`/`skipped`/`startup_only` — do not introduce new nested branching.
- The "No changes detected." branch (currently `if not result.applied and not
  result.needs_restart: if result.startup_only: ... else: "No changes detected."`)
  must additionally require `not result.always_live`, so a `diagnostics.*`-only
  reload does not falsely report no changes.
- After REQ-003 lands, re-run `radon cc scripts/agent/commands/cmd_config.py -s -n
  C` and treat any complexity-grade regression beyond the pre-existing baseline
  (`_cmd_reload` currently grade C(11), per this Plan's Design section) as a signal
  to extract a small helper — not to broaden this item's scope.

## Alternatives considered

- Introducing a new nested branch structure or nested nested handling for
  `always_live` was considered and rejected — the Design section specifies reusing
  the flat additive pattern to avoid pushing `_cmd_reload`'s complexity meaningfully
  above its current grade-C(11) baseline.

## Implementation
### Target file
`scripts/agent/commands/cmd_config.py`

### Procedure
1. Change the initial `if not result.applied and not result.needs_restart:` block's
   inner condition from `if result.startup_only:` to also check `always_live` (see
   Details below for exact branch text).
2. Add `not result.always_live` to whatever condition currently triggers "No
   changes detected."
3. Add a new `if result.always_live: self._write_item_list(result.always_live,
   "Live via config file (no restart or /reload needed)", "LIVE")` call, alongside
   the existing `applied`/`skipped`/`startup_only` `_write_item_list()` calls.
4. Run `uv run pytest tests/agent/commands/test_cmd_config_char.py -v` (will show
   the new assertions failing until seq 04 test-file item in this pass is also
   applied — or passing if this item lands after that test update).
5. Run `uv run radon cc scripts/agent/commands/cmd_config.py -s -n C` and confirm no
   meaningful complexity regression beyond the pre-existing grade-C(11) baseline.

### Method
Direct code edits (Edit tool) — extend the existing branch condition, add one
`_write_item_list()` call.

### Details
Current code (verified 2026-08-27, lines 62-88):
```python
            result = ConfigReloadService(self._ctx).apply_config_dict(new_cfg)
            result.source_files = list(_BASE_CONFIG_FILES)

            if not result.applied and not result.needs_restart:
                if result.startup_only:
                    self._out.write(
                        "Config reloaded — startup-only settings cannot apply without restart"
                    )
                else:
                    self._out.write("No changes detected.")
            elif result.needs_restart:
                self._out.write("Config reloaded — some changes require restart")
            else:
                self._out.write("Config reloaded — all changes applied")
            ...
            if result.applied:
                self._write_item_list(result.applied, "Applied (runtime)", "OK")
            if result.skipped:
                self._write_item_list(result.skipped, "Skipped", "SKIP")
            if result.startup_only:
                self._write_item_list(
                    result.startup_only, "Startup-only (ignored)", "STARTUP-ONLY"
                )
```
Change the top-level message-selection branch so that the "no changes" fallback
also accounts for `always_live` (a `diagnostics.*`-only change must not print "No
changes detected."):
```python
            if not result.applied and not result.needs_restart:
                if result.startup_only:
                    self._out.write(
                        "Config reloaded — startup-only settings cannot apply without restart"
                    )
                elif result.always_live:
                    self._out.write(
                        "Config reloaded — no /reload action needed for changed settings"
                    )
                else:
                    self._out.write("No changes detected.")
            elif result.needs_restart:
                self._out.write("Config reloaded — some changes require restart")
            else:
                self._out.write("Config reloaded — all changes applied")
```
Add a new render block adjacent to the existing `startup_only` block:
```python
            if result.always_live:
                self._write_item_list(
                    result.always_live,
                    "Live via config file (no restart or /reload needed)",
                    "LIVE",
                )
```
Verify the exact wording/branch placement against the file's actual current content
before finalizing — the excerpt above is based on this Plan's own Design section
quote, re-confirm line numbers have not drifted since 2026-08-26.

## Compatibility considerations

- Additive: existing `applied`/`skipped`/`startup_only`/`needs_restart` rendering is
  unchanged; only a new `elif`/`if` branch is added.
- Depends on seq 01 (`config_reload.py`) landing in the same change — without
  `ConfigReloadOutcome.always_live`, this file would reference a nonexistent
  attribute.

## Security considerations

- Confirm the "LIVE" render line lists only field *names* (e.g.
  `"diagnostics.encryption_key"`), never the field's actual value — especially
  important since one of the three fields is `encryption_key` itself.

## Rollback considerations

- Revert via `git diff`/`git checkout -- scripts/agent/commands/cmd_config.py`;
  must be reverted together with seq 01 (`config_reload.py`) in this same pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/commands/cmd_config.py` | Characterization | `uv run pytest tests/agent/commands/test_cmd_config_char.py -v` | New "LIVE" render-line assertions pass once seq 04 test-file item is also applied |
| `scripts/agent/commands/cmd_config.py` | Complexity | `uv run radon cc scripts/agent/commands/cmd_config.py -s -n C` | No meaningful regression beyond the pre-existing grade-C(11) baseline for `_cmd_reload` |

## Completion criteria

- `result.always_live` is rendered via `_write_item_list()` with accurate,
  non-misleading wording.
- A `diagnostics.*`-only reload does not print "No changes detected."
- No field value (especially `encryption_key`) is printed — only field names.

## Out of scope

- Any other command in this file.
- `ConfigReloadService`/`ConfigReloadOutcome` themselves.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend the message-selection branch for `always_live` | Completed | 2026-08-28 | 2026-08-28 | Adversarial verification confirmed: line 66 shows `and not result.always_live` — REQ-003 completed by `plans/done/20260826-120102_plan.md`. No code changes needed. |
| 2 | Exclude `always_live` from "No changes detected." | Completed | 2026-08-28 | 2026-08-28 | Same as above. |
| 3 | Add `_write_item_list()` call for `result.always_live` | Completed | 2026-08-28 | 2026-08-28 | Adversarial verification confirmed: line 93-95 shows the render block. |
| 4 | Run `uv run pytest tests/agent/commands/test_cmd_config_char.py -v` | Completed | 2026-08-28 | 2026-08-28 | Validated below. |
| 5 | Run `radon cc` and confirm no complexity regression | Completed | 2026-08-28 | 2026-08-28 | Validated below. |

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
- **Requirement ID**: REQ-003
- **Source issue**: `issues/20260821_06_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-120102_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-111437
- **Related target files**: `scripts/agent/commands/cmd_config.py`
