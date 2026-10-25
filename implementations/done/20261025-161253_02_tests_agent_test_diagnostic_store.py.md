# Implementation Procedure — tests/agent/test_diagnostic_store.py

## Goal

Add load-count and snapshot-consistency tests to `tests/agent/test_diagnostic_store.py`
that are red against the current code and pin REQ-001/REQ-004/REQ-006 (one config
load per `save()`/`fetch()`, one snapshot per operation).

## Scope

- Append one counting loader subclass and one test class to
  `tests/agent/test_diagnostic_store.py`. No existing test is edited.
- Source-side green step lives in procedure 01
  (`20261025-161253_01_scripts_agent_diagnostic_store.py.md`); docs in procedure 03.

## Assumptions

- Verified 2026-10-25 against master @ d41092a81: 37 tests collected in this file;
  `_FakeConfigLoader` at 78-85 (fixed-dict `load(*names)` drop-in); established patch
  pattern `patch("agent.diagnostic_store.ConfigLoader", return_value=fake_cfg_loader)`
  (first use 348-349, further uses through 799) — a counting subclass slots in with
  no change to existing tests.
- Red baselines (verified by source reading): JSON-object payload `save()` = 3 loads
  (115, 90, 164); non-JSON `save()` = 2 (90 early-returns before the load);
  `fetch()` = 1 (already green, pinned against regression).
- The security file is untouched characterization coverage; it is included in the
  validation command of procedure 01.

## Design decisions

- Count at the `ConfigLoader` seam (patch `agent.diagnostic_store.ConfigLoader`
  class with a counting instance via `return_value`) — the same seam the production
  code uses inside `_load_diagnostics_config`, so the count equals full
  read-and-merge operations, the metric the plan targets.
- Test-first ordering: procedures 02 → 01 → 03; tests 1-2 red before procedure 01,
  test 3 green throughout.

## Alternatives considered

- Counting `_load_diagnostics_config` calls via `patch.object`: rejected — it counts
  helper invocations, not full config parses, and the security file already shows
  instance-level patching is fragile against signature churn.

## Implementation

### Target file

`tests/agent/test_diagnostic_store.py` (modify — append only).

### Procedure

1. After `_FakeConfigLoader` (78-85) add `_CountingConfigLoader (new)`:

   ```python
   class _CountingConfigLoader(_FakeConfigLoader):  # (new)
       """_FakeConfigLoader variant that counts load() invocations."""  # (new)

       def __init__(self, cfg: dict) -> None:  # (new)
           super().__init__(cfg)  # (new)
           self.load_calls = 0  # (new)

       def load(self, *names: str) -> dict:  # (new)
           self.load_calls += 1  # (new)
           return self._cfg  # (new)
   ```

2. At the end of the file (after `TestFetchEncryptedRoundTrip`) append
   `TestPerOperationConfigSnapshot (new)` with four tests:
   - `test_save_json_object_payload_loads_config_once (new)` — payload
     `'{"q": "x", "artifacts": ["a.png"]}'` (JSON object with a sensitive list field,
     forcing the redaction merge path); `loader.load_calls == 1`. Red before
     procedure 01 (currently 3).
   - `test_save_non_json_payload_loads_config_once (new)` — content `"plain text"`;
     `loader.load_calls == 1`. Red before procedure 01 (currently 2).
   - `test_fetch_loads_config_once (new)` — pre-insert one row via `fake_db.execute` +
     commit (outside the patched loader), then `store.fetch(1)`;
     `loader.load_calls == 1`. Green before and after (pins the property).
   - `test_save_uses_single_snapshot_across_helpers (new)` — loader whose `load()` returns
     `{"diagnostics": {"retention_days": 45}}` on the first call and
     `{"diagnostics": {"retention_days": 1}}` afterwards; assert
     `loader.load_calls == 1` after `store.save(1, kind="k", content="text")`,
     proving no helper re-reads (guards future regressions). Green trivially after
     procedure 01.
3. Every test uses the established two-patch pattern
   (`SQLiteHelper` fake + `ConfigLoader` counting instance) and the `fake_db`
   fixture; the counting instance is created per test so counts never leak.

### Method

Pure test addition; no production import changes; no edits to the existing 37 tests.

### Details

- Fake cfg dicts use the `{"diagnostics": {...}}` shape the production loader path
  produces (`raw_cfg.get("diagnostics", {})` in `_load_diagnostics_config`).
- Test 1 content passes the `_SENSITIVE_PATTERNS` gate (no `RuntimeError`) because
  the artifacts list is redacted to `{"_redacted": True, "count": 1}` before the
  gate runs.

## Compatibility considerations

- Existing tests pass unmodified (REQ-003/AC-002): the helper-parameter threading in
  procedure 01 is invisible to them because they patch at the `ConfigLoader` class
  seam, not the helper signatures.

## Security considerations

- No secrets in test fixtures; `encryption_key` stays `""` in the counting fakes
  (encryption gate behavior is covered by the existing `TestEncryption` class).

## Rollback considerations

- Appended-only diff: revert = delete the appended blocks. Tests 1-2 turning red is
  the expected state before procedure 01 lands, not a failure of this procedure.

## Validation plan

- `uv run pytest tests/agent/test_diagnostic_store.py -q` → 40 collected; 2 expected
  failures (tests 1-2) until procedure 01 lands.
- After procedure 01: same command fully green; plus the procedure 01 targeted set
  green.

## Completion criteria

- Four new tests present and executing; 37 pre-existing tests byte-identical and
  green.
- After procedure 01: load-count assertions green (1 load per operation).

## Out of Scope

- No changes to `tests/agent/test_diagnostic_store_security.py`,
  `tests/agent/test_session_persister.py`, `tests/agent/test_regression_diagnostic_persist.py`
  (read-only characterization).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append `_CountingConfigLoader (new)` + `TestPerOperationConfigSnapshot (new)` | Completed | — | — | Tests 1-2 must run red first red recorded: save=3, non-json=2, drift=2 loads; fetch green |
| 2 | Confirm 37 existing tests still pass | Completed | — | — | deviation: 5 TestFilterSensitiveFields direct helper calls updated for cfg param; all green after procedure 01 |

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
- **Requirement ID**: REQ-001 (tests 1-3), REQ-004 (test 4), REQ-006
- **Source issue**: `issues/20261025-115935_sess006_diagnostic-store-config-reload.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-124341_sess006_diagnostic-store-config-reload.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure