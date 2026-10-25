# Implementation Procedure — scripts/agent/diagnostic_store.py

## Goal

Resolve `DiagnosticsConfig` exactly once per public `DiagnosticStore` operation in
`scripts/agent/diagnostic_store.py` and thread it into the private helpers, so one
`save()` makes internally consistent redaction/encryption/purge decisions from a
single config snapshot (REQ-001..REQ-005).

## Scope

- Modify only `scripts/agent/diagnostic_store.py`: `save()` load placement and the
  private helper signatures `_filter_sensitive_fields` and `_purge_old_diagnostics`.
- No change to `fetch()` (already a single load) or to `__init__` (loads nothing).
- Tests: procedure 02 (`20261025-161253_02_tests_agent_test_diagnostic_store.py.md`);
  docs: procedure 03 (`20261025-161253_03_docs_23_agent_agent_10_05_operations-and-observability-monitoring.md.md`).

## Assumptions

- Verified 2026-10-25 against master @ d41092a81 (273-line file): load sites are
  `_purge_old_diagnostics` (115), `_filter_sensitive_fields` (90, JSON-object payloads
  only; early-returns at 84/86 skip it), and the unconditional encryption-check load
  in `save()` (164); `fetch()` loads once (187). `save()` itself is 135-183;
  `_load_diagnostics_config` 43-67 (`ConfigLoader().load("agent.toml")` at 52).
- `scripts/shared/config_loader.py` `load` (79-87) has no cache: each call re-reads
  and re-merges, so per-operation freshness already holds today; the fix is load
  count and intra-call consistency, not staleness.
- `_filter_sensitive_fields` and `_purge_old_diagnostics` have no callers outside
  the class (only `save()` calls them: 151 and 153-162 region); mypy enforces the
  new required parameters.
- `DiagnosticsConfig` is already imported at module level
  (`agent.config_dataclasses`); no new import and no `.importlinter` contract change
  (6 contracts stay kept).

## Design decisions

- Per-operation resolve-and-thread, no caching (plan Design, issue UQ1 decision):
  store-level caching rejected (undefined staleness contract; hot-reload is an
  operational property today).
- `save()` assigns the snapshot at the top under the existing local name
  `diagnostics_cfg` so the encryption gate and `_encrypt_content` call sites
  (165-174) are untouched text.
- The config load moves outside the filter `try` (`# noqa: BLE001` containment at
  153-162): net exception contract for identical inputs is unchanged because
  `save()` already loads unconditionally at 164 today (plan Re-verification
  containment nuance).

## Alternatives considered

- Store-level cached config + refresh rule: rejected (plan Design).
- Keeping the load at its current mid-`save()` position and only threading
  `_purge_old_diagnostics`: rejected — leaves 2 loads per `save()` and the mid-call
  consistency gap.

## Implementation

### Target file

`scripts/agent/diagnostic_store.py` (modify).

### Procedure

1. `save()` (135-183): make `diagnostics_cfg = self._load_diagnostics_config()` the
   first statement (replacing the mid-body assignment at 164); then call
   `self._purge_old_diagnostics(diagnostics_cfg)` and
   `self._filter_sensitive_fields(content, diagnostics_cfg)`. The RuntimeError gate
   (165-171) and insert (176-183) are unchanged.
2. `_filter_sensitive_fields` (69-99): signature becomes
   `(self, content: str, cfg: DiagnosticsConfig)`; replace the internal load at 90
   with `cfg.sensitive_fields`. Docstring line "The set of sensitive fields is
   loaded from DiagnosticsConfig" becomes "provided by the caller's DiagnosticsConfig
   snapshot".
3. `_purge_old_diagnostics` (113-133): signature becomes `(self, cfg: DiagnosticsConfig)`;
   replace the internal load at 115 with `cfg.retention_days`. Docstring states the
   config is supplied by the caller.
4. `fetch()` (185-216): unchanged — its single load at 187 is the snapshot.
5. After the change `self._load_diagnostics_config()` appears exactly twice as a
   call site (top of `save()`, top of `fetch()`).

### Method

Direct in-class edit; no signature change to any public method
(`__init__(session_id=None)`, `save(...)`, `fetch(...)`, `save_serialization_event`,
`save_partial_completion`, `save_transport_failure`, `_encrypt_content(content, key)`
all unchanged).

### Details

- `_SENSITIVE_FIELDS` merge semantics (`frozenset` union) and the `RuntimeError`
  trigger condition are byte-preserved for the same inputs (REQ-003).
- Order of decisions inside `save()` is preserved: purge → filter → encryption gate →
  encrypt → insert; only the config source moves.

## Compatibility considerations

- Private helper parameter additions only; all production call sites construct
  `DiagnosticStore()` with no arguments (`repl.py:80`, `session.py:52`,
  `orchestrator.py:87` — verified at HEAD) and pass explicit ids per call.
- `self.session_id` is assigned only in `__init__` (41) and never read; stays as-is
  (U-001 resolved in plan).

## Security considerations

- The security-gating decision chain (redaction → encryption gate → RuntimeError)
  now reads one snapshot, removing the mid-call inconsistency window (plan Problem).
- No change to what is redacted, encrypted, or rejected; behavior-neutral for
  identical inputs (REQ-003).

## Rollback considerations

- Single-file, single commit; `git checkout -- scripts/agent/diagnostic_store.py`
  reverts cleanly. The load-count tests from procedure 02 then fail red, which is
  the rollback signal, not a hidden breakage.

## Validation plan

- After procedure 02 lands red-first:
  `uv run pytest tests/agent/test_diagnostic_store.py tests/agent/test_diagnostic_store_security.py tests/agent/test_session_persister.py tests/agent/test_regression_diagnostic_persist.py -q`
- `uv run ruff check scripts/agent/diagnostic_store.py && uv run mypy scripts/agent/diagnostic_store.py`
- `grep -c 'self\._load_diagnostics_config()' scripts/agent/diagnostic_store.py` → 2
  (was 3 call sites before the change).
- `tests/agent/test_diagnostic_store_security.py` uses
  `patch.object(DiagnosticStore, "_purge_old_diagnostics")` (verified at 42, 58, 78,
  94, 110, 130, 147, 171, 192, 228, 278, 304): `MagicMock` accepts the new `cfg`
  positional argument, so the file passes unmodified.

## Completion criteria

- Existing 37 tests in `tests/agent/test_diagnostic_store.py` and the security file
  pass unmodified.
- Procedure 02 load-count tests turn green (1 load per `save()`/`fetch()`).
- ruff/mypy clean; `lint-imports` unchanged (no import edits).

## Out of Scope

- Global cache in `ConfigLoader`, schema/encryption scheme changes, config injection
  via `AgentContext`, `session_id` construction binding (plan Out of scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Move the `save()` config snapshot to the top and thread it into both private helpers | Completed | — | — | After procedure 02 (tests red first) grep=2 load sites; helpers require cfg |
| 2 | Run targeted validation + static checks | Completed | — | — | targeted 73 passed; ruff/mypy clean; lint-imports 6 kept |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005
- **Source issue**: `issues/20261025-115935_sess006_diagnostic-store-config-reload.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-124341_sess006_diagnostic-store-config-reload.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure