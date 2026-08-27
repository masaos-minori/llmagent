## Goal

Add an `always_live` reporting category to `ConfigReloadOutcome` and a
`_detect_diagnostics_live_fields()` detector (REQ-001, REQ-002), per
`plans/20260826-120102_plan.md`, so `/reload` accurately reports `diagnostics.*`
fields as live-via-config-file rather than silently saying nothing about them.

## Scope

- In scope: add `always_live: list[str]` field to `ConfigReloadOutcome`; add
  `_detect_diagnostics_live_fields()` to `ConfigReloadService`; wire it into
  `apply_config_dict()`.
- Out of scope: any change to `DiagnosticStore.save()`/`fetch()` behavior; making
  `AgentConfig.diagnostics` an actual source of truth for `DiagnosticStore`; any
  change to `_detect_startup_only()` itself (read-only reference for this new
  detector's shape).

## Assumptions

- `DiagnosticStore._load_diagnostics_config()` (`diagnostic_store.py:43-65`,
  re-verified 2026-08-27) reads `agent.toml` directly via `ConfigLoader().load()` on
  every `save()`/`fetch()` call — `ctx.cfg.diagnostics` is never read by any runtime
  code path (`rg "cfg\.diagnostics\b" scripts/` returns no hits, re-verified
  2026-08-27) — so this detector's only purpose is diffing against the
  last-startup snapshot for reporting, not driving any behavior.
- `config/agent.toml`'s `[diagnostics]` table (verified 2026-08-27, lines 172-177)
  currently sets only `encryption_key`/`retention_days`; `sensitive_fields` has no
  TOML key today (uses `DiagnosticsConfig`'s dataclass default, an empty
  frozenset) — the detector must still compare all three fields per REQ-002, since
  an operator could add `sensitive_fields` to the TOML at any time.
- **Correction (plan-to-implementation-procedure adversarial verification,
  2026-08-27)**: this Plan's Problem section originally cited `_detect_startup_only()`
  at lines 431-444 comparing two fields; re-verified current source has it at lines
  598-616, comparing three fields (`use_memory_layer`, `routing_drift_strict`,
  `memory_embed_enabled`). This does not change REQ-001/REQ-002's design — only the
  reference implementation's exact location/field-count was stale in the Plan.

## Design decisions

- Follow `_detect_startup_only()`'s existing shape exactly (per this Plan's Design
  section): read a value via a typed getter, compare against the corresponding
  `ctx.cfg.diagnostics.<field>` attribute, append the field name to a `list[str]` if
  they differ.
- `new_cfg["diagnostics"]` is a nested dict (confirmed via `config/agent.toml`'s
  `[diagnostics]` table shape) — extract it with `_get_dict(new_cfg,
  "diagnostics")` (the same helper `_build_diagnostics_config()` uses in
  `config_builders.py`), then compare its `encryption_key`/`retention_days`/
  `sensitive_fields` keys against `ctx.cfg.diagnostics`'s matching attributes.
- Add a docstring to the new `always_live` field mirroring `startup_only`'s
  docstring style (lines 82-87), explaining it is fields that take effect
  independently of `/reload` because the owning component re-reads its own config
  file directly.

## Alternatives considered

- Wiring `ctx.cfg.diagnostics` into `DiagnosticStore` so it becomes the actual
  source of truth (making the diff meaningful for behavior, not just reporting) was
  considered and rejected — explicitly out of scope per this Plan; `DiagnosticStore`'s
  direct-from-disk read is already strictly more current than anything `/reload`
  could push into `ctx.cfg`, so this would be a freshness regression, not an
  improvement.

## Implementation
### Target file
`scripts/agent/services/config_reload.py`

### Procedure
1. Add `always_live: list[str] = field(default_factory=list)` with a docstring to
   `ConfigReloadOutcome` (near `startup_only`, verified at lines 74-87 as of
   2026-08-27).
2. Add `_detect_diagnostics_live_fields()` method to `ConfigReloadService`, adjacent
   to `_detect_startup_only()` (verified at lines 598-616 as of 2026-08-27).
3. In `apply_config_dict()` (verified at lines 116-144 as of 2026-08-27), add a call
   `result.always_live = self._detect_diagnostics_live_fields(new_cfg)` alongside
   the existing `result.startup_only = self._detect_startup_only(new_cfg)` line
   (143).
4. Run `uv run pytest tests/agent/services/test_config_reload.py -v` (regression;
   expected to pass unchanged, since this only adds a field/method).

### Method
Direct code edits (Edit tool) — one field addition, one new method, one call-site
addition; no changes to existing detector logic.

### Details
New field (add near line 82, mirroring `startup_only`'s style):
```python
    always_live: list[str] = field(default_factory=list)
    """Fields present in the reload payload and differing from the last-startup
    snapshot, but requiring no /reload action at all — the owning component
    (e.g. DiagnosticStore) re-reads its own config file directly on every use,
    independent of ctx.cfg and /reload's sync methods."""
```
New method (add adjacent to `_detect_startup_only()`, following its exact
comparison shape verified at lines 598-616):
```python
    def _detect_diagnostics_live_fields(
        self,
        new_cfg: dict[str, Any],
    ) -> list[str]:
        """Return names of diagnostics.* fields that differ from the startup
        snapshot but are already live via DiagnosticStore's direct config-file
        read — not a /reload target."""
        changed: list[str] = []
        ctx = self._ctx
        diag = _get_dict(new_cfg, "diagnostics")
        if diag is None:
            return changed
        v = _get_str(diag, "encryption_key")
        if v is not None and v != ctx.cfg.diagnostics.encryption_key:
            changed.append("diagnostics.encryption_key")
        v_int = _get_int(diag, "retention_days")
        if v_int is not None and v_int != ctx.cfg.diagnostics.retention_days:
            changed.append("diagnostics.retention_days")
        v_list = diag.get("sensitive_fields")
        if v_list is not None and frozenset(v_list) != ctx.cfg.diagnostics.sensitive_fields:
            changed.append("diagnostics.sensitive_fields")
        return changed
```
Confirm the exact helper function names (`_get_dict`/`_get_str`/`_get_int`) and
their signatures by reading this module's existing helper definitions before
finalizing — the sketch above follows `_detect_startup_only()`'s pattern but the
precise helper names/return-type contracts must be verified against this file's
actual helpers (e.g. whether a `_get_dict` helper already exists, or whether
`new_cfg.get("diagnostics", {})` with an `isinstance` guard is this module's
established idiom instead — mirror `DiagnosticStore._load_diagnostics_config()`'s
own guard style if no shared helper exists).

Call-site addition (line ~143):
```python
        result.startup_only = self._detect_startup_only(new_cfg)
        result.always_live = self._detect_diagnostics_live_fields(new_cfg)
        return result
```

## Compatibility considerations

- Additive-only: new field, new method, one new call — does not change any existing
  field's behavior or `ConfigReloadOutcome`'s existing shape for current consumers
  (`cmd_config.py`, per this Plan's Assumptions confirming no other consumer via
  `rg -n "ConfigReloadOutcome" scripts/agent/`).
- `ConfigReloadOutcome` is an internal dataclass with no external/MCP exposure — not
  a public/runtime-facing interface change.

## Security considerations

- N/A: this only adds read-only diffing/reporting; it does not change what
  `/reload` applies, nor does it expose `encryption_key`'s actual value (only
  reports that the field name differs — verify the render side, seq 02, does not
  print the key's contents).

## Rollback considerations

- Revert via `git diff`/`git checkout -- scripts/agent/services/config_reload.py`;
  must be reverted together with seq 02 (`cmd_config.py`), which renders the new
  field — reverting this file alone leaves `cmd_config.py` referencing a
  nonexistent attribute if seq 02 has already landed.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/config_reload.py` | Unit | `uv run pytest tests/agent/services/test_config_reload_classification.py -v` | New detector tests pass once seq 03 (test file) is also applied |
| `scripts/agent/services/config_reload.py` | Regression | `uv run pytest tests/agent/services/test_config_reload.py -v` | No regressions — existing tests pass unchanged |

## Completion criteria

- `ConfigReloadOutcome` has an `always_live: list[str]` field with a docstring.
- `_detect_diagnostics_live_fields()` compares `encryption_key`/`retention_days`/
  `sensitive_fields` against `ctx.cfg.diagnostics` and returns differing field
  names.
- `apply_config_dict()` populates `result.always_live` from the new detector.

## Out of scope

- `DiagnosticStore.save()`/`fetch()` behavior.
- `AgentConfig.diagnostics` wiring into `DiagnosticStore`.
- `_detect_startup_only()` itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `always_live` field to `ConfigReloadOutcome` | Pending | — | — | |
| 2 | Add `_detect_diagnostics_live_fields()` method | Pending | — | — | |
| 3 | Wire detector into `apply_config_dict()` | Pending | — | — | |
| 4 | Run `uv run pytest tests/agent/services/test_config_reload.py -v` | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: `issues/20260821_06_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-120102_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-111437
- **Related target files**: `scripts/agent/services/config_reload.py`
