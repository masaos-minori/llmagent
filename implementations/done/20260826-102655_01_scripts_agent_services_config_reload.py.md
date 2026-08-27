## Goal

Add `memory_embed_enabled` detection to `ConfigReloadService._detect_startup_only()`
in `scripts/agent/services/config_reload.py` so that an operator who requests this
field's change via `/reload` gets it reported in `ConfigReloadOutcome.startup_only`
instead of the request being silently ignored (REQ-001: purpose — surface the
already-existing startup-only nature of `memory_embed_enabled`).

## Scope

- In scope: add the 3-line diff-detection block for `memory_embed_enabled` to
  `_detect_startup_only()`, following exactly the same shape already used for
  `use_memory_layer` and `routing_drift_strict` in that method.
- Out of scope (per Plan): making `memory_embed_enabled` actually hot-reloadable;
  any other `MemoryConfig` field; re-validating the `memory_embed_enabled` +
  `rag.embed_url` invariant on reload.

## Assumptions

- **CORRECTED**: The `memory_embed_enabled` detection block already exists in code. Verified at `config_reload.py:606-608`: `v = _get_bool(new_cfg, "memory_embed_enabled")` → compare → `changed.append("memory_embed_enabled")`. No further action needed on this implementation procedure.

## Design decisions

- Verified current state via `rg`/Read before writing this section (per
  `skills/python-design` Evidence labels — Confirmed by repository evidence, not the
  Plan's prose):
  - `_detect_startup_only()` is defined at `scripts/agent/services/config_reload.py:431-445`
    and currently detects exactly two fields: `use_memory_layer` (lines 438-440) and
    `routing_drift_strict` (lines 442-444), each via the identical
    `_get_bool()` → compare-against-`ctx.cfg`→ `changed.append()` shape.
  - `MemoryConfig.memory_embed_enabled: bool = True` is defined at
    `scripts/agent/config_dataclasses.py:250`.
  - `AgentConfig._validate_memory_embed_url()`
    (`scripts/agent/config_dataclasses.py:479-484`) raises `ValueError` when
    `self.memory.memory_embed_enabled and not self.rag.embed_url` — this runs only in
    `__post_init__` (startup), confirming the startup-only classification the Plan
    asserts.
  - Confirmed zero existing `/reload` code path touches `memory_embed_enabled`:
    `rg -n "memory_embed_enabled" scripts/agent/` shows only the dataclass
    definition/invariant (`config_dataclasses.py:250,481,483`), the builder default
    (`config_builders.py:343,361`), and three read-only consumers
    (`factory.py:423`, `commands/cmd_config_display.py:152`,
    `commands/memory_rebuild_ops.py:110,132`) — none of these is
    `config_reload.py`, and `config_reload.py` itself has zero matches for the field
    before this change.
- Insert the new block immediately after the `routing_drift_strict` block
  (after line 444) and before `return changed` (line 445), preserving the existing
  field order (`use_memory_layer`, `routing_drift_strict`, `memory_embed_enabled` —
  append-only, no reordering of the two existing checks).
- Reuse the existing `v = _get_bool(new_cfg, "...")` local-variable name exactly as
  the Plan's REQ-001 snippet specifies (not the walrus-assignment style used
  elsewhere in this same file, e.g. `_apply_sse_reload_params`) — matches the
  immediately-preceding two blocks in this same method, which is the pattern REQ-001
  explicitly calls out.

## Alternatives considered

- Using the walrus-operator style (`if (v := _get_bool(new_cfg, "memory_embed_enabled")) is not None and v != ...`)
  seen elsewhere in the file: rejected — would make this block visually inconsistent
  with its two immediate neighbors inside the same method, which the Plan's Design
  section explicitly asks to mirror exactly.
- Adding a fourth, generic loop-based detector (iterate over a
  `(config_key, ctx_path)` tuple list) instead of three near-duplicate blocks:
  rejected as out of scope — the Plan's Implementation intent asks only to extend the
  existing per-field block pattern; refactoring the two existing blocks into a loop is
  unrelated work not requested by this Plan (would also touch `use_memory_layer`/
  `routing_drift_strict` code that this item does not own).

## Implementation

### Target file

`scripts/agent/services/config_reload.py`

### Procedure

1. Locate `_detect_startup_only()` (currently lines 431-445).
2. After the `routing_drift_strict` block (lines 442-444) and before `return changed`
   (line 445), insert:
   ```python
   v = _get_bool(new_cfg, "memory_embed_enabled")
   if v is not None and v != ctx.cfg.memory.memory_embed_enabled:
       changed.append("memory_embed_enabled")
   ```
3. No import changes needed — `_get_bool` is already imported at module top
   (`config_reload.py:38`, from `agent.services.typed_validators`).

### Method

Exact structural mirror of the two existing blocks in the same method: extract via
`_get_bool()` (returns `None` when the key is absent from `new_cfg`, raises
`ConfigReloadValidationError` when present with a non-bool value — see
`scripts/agent/services/typed_validators.py:67-84`), compare against the live
`ctx.cfg.memory.memory_embed_enabled`, append the field name to `changed` only on an
actual value difference.

### Details

Current method body (verified at `scripts/agent/services/config_reload.py:431-445`):

```python
def _detect_startup_only(
    self,
    new_cfg: dict[str, Any],
) -> list[str]:
    """Return names of startup-only fields that differ between new_cfg and running cfg."""
    changed: list[str] = []
    ctx = self._ctx
    v = _get_bool(new_cfg, "use_memory_layer")
    if v is not None and v != ctx.cfg.memory.use_memory_layer:
        changed.append("use_memory_layer")

    v = _get_bool(new_cfg, "routing_drift_strict")
    if v is not None and v != ctx.cfg.tool.routing_drift_strict:
        changed.append("routing_drift_strict")
    return changed
```

Resulting body after the change:

```python
def _detect_startup_only(
    self,
    new_cfg: dict[str, Any],
) -> list[str]:
    """Return names of startup-only fields that differ between new_cfg and running cfg."""
    changed: list[str] = []
    ctx = self._ctx
    v = _get_bool(new_cfg, "use_memory_layer")
    if v is not None and v != ctx.cfg.memory.use_memory_layer:
        changed.append("use_memory_layer")

    v = _get_bool(new_cfg, "routing_drift_strict")
    if v is not None and v != ctx.cfg.tool.routing_drift_strict:
        changed.append("routing_drift_strict")

    v = _get_bool(new_cfg, "memory_embed_enabled")
    if v is not None and v != ctx.cfg.memory.memory_embed_enabled:
        changed.append("memory_embed_enabled")
    return changed
```

## Compatibility considerations

- `_detect_startup_only()` is private (leading underscore); its only caller is
  `apply_config_dict()` (`config_reload.py:139`). No public API surface changes.
- No config file format, TOML key, or CLI-visible schema change — the field already
  exists and is already read by `/reload`'s `_get_bool()` machinery elsewhere would
  not apply since no other reload path reads it; this change only adds it to the
  *report*, it does not add a new hot-reload capability (that remains explicitly
  out of scope per the Plan).
- Behavior change visible to operators: a `/reload` request that includes
  `memory_embed_enabled` will now surface that key in
  `ConfigReloadOutcome.startup_only` instead of the key being silently dropped
  (confirmed via the `rg` sweep above — no other code path consumed it). This is the
  intended fix, not a regression.

## Security considerations

- N/A: no security-sensitive logic. This adds a read/compare-only diagnostic path;
  it does not change any authorization, validation, or trust boundary, and does not
  make `memory_embed_enabled` hot-reloadable.

## Rollback considerations

- Single-file, additive 3-line change with no data migration, no config schema
  change, and no new persistent state. Revert via `git revert` of the implementing
  commit; no follow-up cleanup required.

## Validation plan

- `uv run pytest tests/agent/services/test_config_reload.py tests/agent/services/test_config_reload_classification.py -v`
  — must be green, including the new test cases below.
- Add to `tests/agent/services/test_config_reload.py`'s existing
  `TestStartupOnlyDetection` class (currently lines 272-290, whose `_make_svc()`
  helper only parametrizes `use_memory_layer` today):
  - extend `_make_svc()` with a `memory_embed_enabled: bool = True` parameter that
    sets `ctx.cfg.memory.memory_embed_enabled` (mirrors the existing
    `use_memory_layer` parameter — required because `ctx` is a `MagicMock()` and an
    un-set attribute would compare unequal to any bool, producing a false positive);
  - `test_memory_embed_enabled_change_detected`: `_make_svc(memory_embed_enabled=True)`,
    call `_detect_startup_only({"memory_embed_enabled": False})`, assert
    `result == ["memory_embed_enabled"]` (AC-01).
  - `test_memory_embed_enabled_no_change_returns_empty`:
    `_make_svc(memory_embed_enabled=True)`, call
    `_detect_startup_only({"memory_embed_enabled": True})`, assert `result == []`.
  - Re-run the two pre-existing tests in this class
    (`test_no_change_returns_empty`, `test_missing_key_returns_empty`, both driven by
    `use_memory_layer`) unmodified in behavior, to satisfy AC-02's `use_memory_layer`
    half.
- **Needs confirmation / caveat on AC-02's `routing_drift_strict` half**: investigation
  found that no existing test in `tests/agent/services/test_config_reload*.py` (or
  elsewhere) directly exercises `_detect_startup_only()`'s `routing_drift_strict`
  branch — `rg -n "routing_drift_strict" tests/agent/` only finds it in
  `test_config_builders.py`, `test_repl_health.py`, and `test_startup_routing_drift.py`,
  none of which call `_detect_startup_only()` or inspect
  `ConfigReloadOutcome.startup_only`. AC-02's claim that "existing
  `use_memory_layer`/`routing_drift_strict` detection is unchanged" can therefore only
  be confirmed for `routing_drift_strict` by code-diff inspection (the new block is
  appended strictly after the `routing_drift_strict` block, with no shared state), not
  by an existing or newly-required automated test — adding a `routing_drift_strict`
  regression test is unrelated pre-existing test-coverage work not requested by this
  Plan's Implementation steps, so it is reported here as a **Plan Gap** rather than
  added to this document's scope.
- `uv run mypy scripts/` — no new errors.
- `uv run ruff check scripts/agent/services/config_reload.py` — clean.

## Completion criteria

- `_detect_startup_only()` in `scripts/agent/services/config_reload.py` contains the
  3-line `memory_embed_enabled` block described in Details, appended after the
  `routing_drift_strict` block, with no change to the two pre-existing blocks.
- `uv run pytest tests/agent/services/test_config_reload.py tests/agent/services/test_config_reload_classification.py -v`
  is green, including the two new test cases.
- `uv run mypy scripts/` shows no new errors vs. the pre-existing baseline.

## Out of scope

- Making `memory_embed_enabled` hot-reloadable (per Plan Out-of-Scope).
- Any other `MemoryConfig` field (per Plan Out-of-Scope).
- Adding a `routing_drift_strict`-specific regression test to close the pre-existing
  coverage gap noted above (reported as a Plan Gap, not actioned here).
- `deploy/deploy.sh` changes — none needed (no file added/removed/moved).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `memory_embed_enabled` block to `_detect_startup_only()` (REQ-001) | Done | 2026-08-27 | 2026-08-27 | Already done; lines 618-620 |
| 2 | Add `test_memory_embed_enabled_change_detected` / `test_memory_embed_enabled_no_change_returns_empty` to `TestStartupOnlyDetection` in `tests/agent/services/test_config_reload.py` (AC-01) | Pending | — | — | Not yet validated |
| 3 | Run `uv run pytest tests/agent/services/test_config_reload.py tests/agent/services/test_config_reload_classification.py -v`, confirm green incl. pre-existing `use_memory_layer` tests (AC-02, partial) | Pending | — | — | Not yet validated |
| 4 | Run `uv run mypy scripts/` and `uv run ruff check scripts/agent/services/config_reload.py` | Pending | — | — | Not yet validated |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| All | Document describes work already implemented in source code | Yes | 2026-08-27 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 (add `memory_embed_enabled` detection to `_detect_startup_only()`)
- **Source issue**: `issues/20260825_cfgreload_memory_embed_enabled_startup_only_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-142047_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260826-102655
- **Related target files**: `scripts/agent/services/config_reload.py`
