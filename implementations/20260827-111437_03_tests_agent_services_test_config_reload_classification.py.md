## Goal

Add unit tests for `_detect_diagnostics_live_fields()` (REQ-004), mirroring the
existing `_detect_startup_only` test pattern, per `plans/20260826-120102_plan.md`.

## Scope

- In scope: new `test_detect_diagnostics_live_fields_*` test functions in this file.
- Out of scope: existing `_detect_startup_only` tests (unaffected reference
  pattern, not modified); any other detector.

## Assumptions

- `scripts/agent/services/config_reload.py`'s `_detect_diagnostics_live_fields()`
  has been (or is being, in this same pass, seq 01) added, following
  `_detect_startup_only()`'s comparison shape — this file's tests depend on that
  method existing with the signature `_detect_diagnostics_live_fields(self,
  new_cfg: dict[str, Any]) -> list[str]`.
- This file's shared `_make_ctx()` fixture (verified 2026-08-27, lines 15-26) does
  NOT currently set any `ctx.cfg.diagnostics.*` attribute — since `ctx` is a
  `MagicMock`, an unset attribute auto-returns a new `MagicMock` instance rather
  than a real string/int/frozenset, which would make equality comparisons in the
  new detector always `False` (a `MagicMock != "some_string"` is always true) and
  could produce false-positive "changed" results in tests that do not explicitly
  set the diagnostics fields.

## Design decisions

- Extend `_make_ctx()` to set `ctx.cfg.diagnostics.encryption_key = ""`,
  `ctx.cfg.diagnostics.retention_days = 30`, `ctx.cfg.diagnostics.sensitive_fields =
  frozenset()` (matching `DiagnosticsConfig`'s dataclass defaults, verified
  2026-08-27 at `config_dataclasses.py:406-416`) — this keeps the shared fixture
  usable for the new tests without every existing test needing to set these
  fields, and matches the pattern already used for `use_memory_layer`/
  `llm_temperature`/etc.
- Mirror `test_detect_startup_only_empty_dict`/`test_detect_startup_only_non_startup_keys_ignored`'s
  exact test shape (empty dict → `[]`; irrelevant keys → `[]`) plus one changed-value
  case, per REQ-004's specification (empty dict, non-diagnostics keys ignored, an
  actually-changed `diagnostics.*` field detected).

## Alternatives considered

- Constructing a fresh, diagnostics-specific `MagicMock` per new test (instead of
  extending the shared `_make_ctx()` fixture) was considered and rejected — it would
  duplicate the fixture pattern already established for every other detector's
  tests in this file, and this file's own docstring frames it as a shared
  "classification snapshot" suite across all detectors.

## Implementation
### Target file
`tests/agent/services/test_config_reload_classification.py`

### Procedure
1. Extend `_make_ctx()` (lines 15-26) to set the three `ctx.cfg.diagnostics.*`
   attributes to their `DiagnosticsConfig` defaults.
2. Add `test_detect_diagnostics_live_fields_empty_dict`,
   `test_detect_diagnostics_live_fields_non_diagnostics_keys_ignored`, and
   `test_detect_diagnostics_live_fields_changed_field_detected`.
3. Run `uv run pytest tests/agent/services/test_config_reload_classification.py -v`.

### Method
Direct file edits (Edit tool) — extend one fixture, add three new test functions
adjacent to the existing `_detect_startup_only` tests.

### Details
Fixture extension (add to `_make_ctx()`, near the existing `ctx.cfg.memory.*`/
`ctx.cfg.llm.*` lines):
```python
    ctx.cfg.diagnostics.encryption_key = ""
    ctx.cfg.diagnostics.retention_days = 30
    ctx.cfg.diagnostics.sensitive_fields = frozenset()
```
New tests (mirroring `test_detect_startup_only_empty_dict`/
`test_detect_startup_only_non_startup_keys_ignored` at lines 44-50):
```python
def test_detect_diagnostics_live_fields_empty_dict(svc: ConfigReloadService) -> None:
    result = svc._detect_diagnostics_live_fields({})
    assert result == []


def test_detect_diagnostics_live_fields_non_diagnostics_keys_ignored(
    svc: ConfigReloadService,
) -> None:
    result = svc._detect_diagnostics_live_fields(
        {"llm_temperature": 0.3, "use_memory_layer": True}
    )
    assert result == []


def test_detect_diagnostics_live_fields_changed_field_detected(
    svc: ConfigReloadService,
) -> None:
    result = svc._detect_diagnostics_live_fields(
        {"diagnostics": {"retention_days": 90}}
    )
    assert result == ["diagnostics.retention_days"]
```
Verify the exact new_cfg shape the detector expects (a nested `{"diagnostics":
{...}}` dict, matching `config/agent.toml`'s `[diagnostics]` table structure) against
the seq 01 implementation before finalizing these test bodies — confirm the exact
returned field-name strings (e.g. `"diagnostics.retention_days"` vs.
`"retention_days"`) match the seq 01 detector's actual output format.

## Compatibility considerations

- Test-only change; no production code path is affected.
- Extending `_make_ctx()` could affect other existing tests in this file if any of
  them currently rely on `ctx.cfg.diagnostics.*` being an unset `MagicMock` — `rg -n
  "cfg\.diagnostics" tests/agent/services/test_config_reload_classification.py`
  should be re-run after this edit to confirm no existing test's behavior changes.

## Security considerations

- N/A: test-only change, no security-relevant code path.

## Rollback considerations

- Revert via `git diff`/`git checkout -- <path>`; depends on seq 01
  (`config_reload.py`) landing in the same change for the new tests to pass, but the
  fixture extension itself is backward-compatible with existing tests (adds
  attributes, does not change existing ones).

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/agent/services/test_config_reload_classification.py` | Unit | `uv run pytest tests/agent/services/test_config_reload_classification.py -v` | New tests pass once seq 01 has also landed; existing tests unaffected |

## Completion criteria

- `_detect_diagnostics_live_fields()` has direct unit-test coverage for the empty,
  irrelevant-keys, and changed-field cases.

## Out of scope

- Existing `_detect_startup_only` tests.
- Any other detector in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend `_make_ctx()` with `diagnostics.*` defaults | Pending | — | — | |
| 2 | Add 3 new `test_detect_diagnostics_live_fields_*` tests | Pending | — | — | |
| 3 | Run `uv run pytest tests/agent/services/test_config_reload_classification.py -v` | Pending | — | — | Requires seq 01 applied first |

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
- **Requirement ID**: REQ-004
- **Source issue**: `issues/20260821_06_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-120102_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-111437
- **Related target files**: `tests/agent/services/test_config_reload_classification.py`
