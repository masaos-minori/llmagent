# sess006 — Resolve diagnostics config once per DiagnosticStore operation

**Source issue**: `issues/20261025-115935_sess006_diagnostic-store-config-reload.md`

> Path A (3 target files: 1 source + 1 test + 1 doc; contained refactor of one
> class). All 22 sections kept; some collapsed per the Path A rule. Verification
> 2026-10-25, all claims confirmed by reading current source: `save()` triggers up
> to 3 `ConfigLoader().load("agent.toml")` calls (line 115 purge, line 90 filter —
> JSON-object payloads only, line 164 encryption check); `fetch()` loads once at
> line 187; `ConfigLoader.load` has no cache (`config_loader.py:79-87` re-reads and
> re-merges per call); docstring pattern at `diagnostic_store.py:43-51`;
> `RuntimeError` no-encryption path at lines 165-171; `DiagnosticStore(self.session_id)`
> constructed at `session.py:52` with `session_id=None`; existing tests already patch
> `agent.diagnostic_store.ConfigLoader` via `_FakeConfigLoader`
> (`test_diagnostic_store.py:78-79,343-386`) — direct hook for load counting.

## Goal

Resolve `DiagnosticsConfig` exactly once per public `DiagnosticStore` operation and
pass it into the private helpers, so one `save()` makes internally consistent
redaction/encryption decisions from a single config snapshot.

## Priority

Medium (issue-stated). Hot-path redundancy (up to 4 TOML parses per diagnostic
write chain) plus a small intra-call consistency window in a security-relevant
decision.

## Scope

In scope:
- `scripts/agent/diagnostic_store.py` — internal threading of the resolved config.
- `tests/agent/test_diagnostic_store.py` — load-count tests.
- `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` —
  state when diagnostics config changes take effect (per-operation snapshot).

Out of scope (issue-stated):
- Global config cache in `ConfigLoader` (repository-wide; own issue).
- `DiagnosticStore` storage schema or encryption scheme.
- Public method signature changes; config injection via `AgentContext`.
- Revisiting `DiagnosticStore.session_id` construction binding (issue UQ2 —
  behavior-neutral today, see Unknowns).

## Background

The re-load pattern is deliberate (docstring 43-51: mirrors `RetentionConfig
.from_config()` because the store has no `AgentContext`), designed for
once-per-command maintenance use. The store actually sits on the event/turn path
(`AgentSession.save_diagnostic`, transport-failure/partial-completion/serialization
events, `session_persister` summaries), so each write performs up to 3 full TOML
parses, and the 3 loads in one `save()` can observe different file states mid-call.

## Problem

`_purge_old_diagnostics()` (115), `_filter_sensitive_fields()` (90, JSON-object
payloads), and the encryption check (164) each independently call
`_load_diagnostics_config()`. A redaction decision could come from config version A
while the encryption gate reads version B within the same `save()`.

## Reason for Change

Confirmed by line-precise code reading (2026-10-25). One redundant full-file parse
family on a repeated path and a consistency gap in a security-gating decision; the
fix stays inside one class.

## Implementation Intent

Load once at the top of `save()`, pass the resolved `DiagnosticsConfig` into
`_purge_old_diagnostics(cfg)` and `_filter_sensitive_fields(content, cfg)`; `fetch()`
already loads once and stays a single load. Private helper signatures change; public
API does not (issue Constraint). Config acquisition stays inside the existing
`ConfigLoader`/`agent.toml` boundary.

## Requirements

| ID | Requirement | Priority | Target |
|---|---|---|---|
| REQ-001 | Exactly one `_load_diagnostics_config()` invocation per `save()` (JSON-object payload) and per `fetch()`. | must | scripts/agent/diagnostic_store.py |
| REQ-002 | Private helpers take the resolved `DiagnosticsConfig` as a parameter instead of re-loading; no second config system. | must | scripts/agent/diagnostic_store.py |
| REQ-003 | Behavior identical for every existing call site: redaction outputs, encryption gating, the `RuntimeError` trigger condition (lines 165-171 semantics), purge cutoff semantics — byte-identical for the same inputs. | must | scripts/agent/diagnostic_store.py |
| REQ-004 | Hot-reload contract preserved: each new public operation sees the latest config (per-operation snapshot; no cross-call caching). | must | scripts/agent/diagnostic_store.py |
| REQ-005 | Public signatures unchanged (`save`, `fetch`, `save_*_event` helpers, `__init__`). | must | scripts/agent/diagnostic_store.py |
| REQ-006 | A test counts config loads per `save()`/`fetch()`; docs state the snapshot semantics. | must | tests/agent/test_diagnostic_store.py, docs/23_agent/agent_10_05_operations-and-observability-monitoring.md |

## Implementation Target Files

> One row per directly affected file.

| File | Action | Contract / Exports to Keep |
|---|---|---|
| scripts/agent/diagnostic_store.py | modify | `__init__(session_id=None)`, `save(...)`, `fetch(...)`, `save_serialization_event`, `save_partial_completion`, `save_transport_failure`, `_encrypt_content(content, key)` signatures unchanged; `_load_diagnostics_config()` stays the single config acquisition point; private helpers `_filter_sensitive_fields(content, cfg)` and `_purge_old_diagnostics(cfg)` gain the cfg parameter; `_SENSITIVE_FIELDS` merge semantics and the `RuntimeError`/`# noqa: BLE001` filter-failure containment unchanged. |
| tests/agent/test_diagnostic_store.py | modify | Existing tests pass unmodified (they patch `agent.diagnostic_store.ConfigLoader` — unaffected by helper-parameter threading); add load-count tests using a counting `_FakeConfigLoader`. |
| docs/23_agent/agent_10_05_operations-and-observability-monitoring.md | modify | Add one policy sentence: diagnostics config changes take effect at the start of each diagnostic store operation (per-operation snapshot; within one operation a single snapshot is used). No code detail. |

## Reference Files

- `scripts/agent/diagnostic_store.py:43-67,90,115,151-183,187` — the load sites and config construction.
- `scripts/shared/config_loader.py:79-87` — uncached load (issue claim, confirmed).
- `tests/agent/test_diagnostic_store.py:78-79,343-386` — `_FakeConfigLoader` + patch pattern reused for counting.
- `scripts/agent/session.py:52` — `DiagnosticStore(self.session_id)` construction site (issue UQ2 anchor; no change).
- `agent.config_dataclasses.DiagnosticsConfig` — the resolved config type passed through helpers.

## Acceptance Criteria

| ID | Criterion | Maps to |
|---|---|---|
| AC-001 | Spy test: JSON-object-payload `save()` → exactly 1 `ConfigLoader.load("agent.toml")`; non-JSON content `save()` → 1; `fetch()` → 1. Red before the change (3/1... `save()` currently 3 for JSON payloads). | REQ-001, REQ-006 |
| AC-002 | All existing `test_diagnostic_store.py` and `test_session_persister.py` tests pass unmodified. | REQ-003, REQ-005 |
| AC-003 | Characterization: redaction output, encrypted round-trip via `fetch()`, and the `RuntimeError` no-encryption trigger are identical for the same inputs (existing tests + one new same-input before/after comparison if not already pinned). | REQ-003 |
| AC-004 | `uv run ruff check` and `uv run mypy --no-namespace-packages` clean on the changed file. | REQ-002 |
| AC-005 | `agent_10_05` states the snapshot semantics; docs checker passes. | REQ-006 |

## Tests

Add to `tests/agent/test_diagnostic_store.py` (write first, red):
1. Load-count spy: `_FakeConfigLoader` variant counting `load()` calls; `save()` with
   a JSON-object payload containing a sensitive list field (forces the filter path) →
   count == 1. (Currently 3.)
2. `save()` with plain-text content (filter early-returns) → count == 1 (currently 2).
3. `fetch()` → count == 1 (already 1 — pins the property against regressions).
4. Mid-operation consistency characterization: same fake returns different dicts on
   successive loads; assert `save()` used only the first snapshot (single load makes
   this trivially true — guards future regressions).

Characterization guards (unmodified): existing redaction/encryption/RuntimeError
tests in `test_diagnostic_store.py`; `tests/agent/test_session_persister.py`.

## Documentation Impact

- `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` — one policy
  sentence on config snapshot semantics (per-operation). No Needs Confirmation
  marker needed: the chosen design (per-operation load, no cache) keeps the current
  hot-reload contract explicit and verified by tests 1-3.
- No other docs affected (`rules/coding.md` unchanged; issue Documentation Impact
  concurs).

## Assumptions

| Assumption | Confidence | Verification |
|---|---|---|
| Per-operation single load is the right choice (issue UQ1 decision): hot-reload "next operation sees new config" is preserved; store-level caching rejected — its staleness contract is undefined and the constraint names per-call as the safe default. | High | Decision recorded in Design; AC-001/AC-004 pin it; docs state it. |
| `_filter_sensitive_fields` early-return paths (non-JSON, non-object) currently skip the config load; threading cfg in makes the load unconditional-at-save — net effect is still 1 load per save for ALL payload types (fewer than today for every case). | High | Source reading 2026-10-25 (lines 81-91); save() already loads at 164 for every payload regardless. |
| `DiagnosticStore.session_id` construction binding (issue UQ2) stays out of scope: every public call passes explicit session ids; `session.py:52` constructs with None. | High | Source read of all public methods; no method reads `self.session_id`. Recorded in Unknowns. |

## Unknowns

| ID | Question | Confidence | Blocking | Verification Steps |
|---|---|---|---|---|
| U-001 | Issue UQ2: revisit `DiagnosticStore(self.session_id)` binding while touching the class. Resolved by decision: no — no public method uses `self.session_id`; changing it is an unrelated refactor (single-file, no explicit id today), violates "do not restructure" scope discipline, and would collide with the sess001 repo-binding pattern review. File a separate issue only if a use case appears. | High | Verified `self.session_id` is never read outside `__init__` (source read 2026-10-25). |
| U-002 | Whether the mid-call inconsistency has ever produced a real bad row in production. | Low | No | Out of scope; prevention is the fix. No production DB forensics performed (read-only query available if ever needed). |

## Affected areas

N/A: single class (`agent.diagnostic_store`); its callers (`session.py`,
`session_persister.py`, tool/transport event paths) see zero API change; `deploy.sh`
impact: none; DB impact: none (same rows written, decisions now from one snapshot).

## Design

Chosen (issue UQ1 decision): **per-operation resolve-and-thread**, no caching.

- `save()`: first statement `cfg = self._load_diagnostics_config()`; then
  `_purge_old_diagnostics(cfg)`, `content = self._filter_sensitive_fields(content, cfg)`,
  encryption gate and `_encrypt_content` use `cfg`. One load, one snapshot, order of
  decisions unchanged.
- `fetch()`: existing single load stays; optionally pass into nothing (no helper uses
  config there).
- `_filter_sensitive_fields(self, content: str, cfg: DiagnosticsConfig)`: uses
  `cfg.sensitive_fields` instead of loading.
- `_purge_old_diagnostics(self, cfg: DiagnosticsConfig)`: uses `cfg.retention_days`.
- Rejected: store-level cached config + refresh rule — staleness contract undefined
  (issue Constraint names per-call as the safe default), hot-reload is an operational
  property today, and caching would move config acquisition outside the per-operation
  boundary the docs would have to describe.

## Implementation steps

1. Phase 1 — write load-count tests 1-3 first (1-2 red, 3 green).
2. Phase 2 — thread `cfg` through `save()` and the two private helpers per Design.
3. Phase 3 — doc sentence in `agent_10_05`; full validation (`rules/toolchain.md`),
   single commit.

## Validation plan

- Targeted: `uv run pytest tests/agent/test_diagnostic_store.py tests/agent/test_session_persister.py tests/agent/test_regression_diagnostic_persist.py -x -q`.
- Full: `uv run pytest tests/ -q` (baseline 10082 passed / 9 skipped) +
  `rules/toolchain.md` sequence; `lint-imports` 6 kept / 0 broken (no import changes).
- Static: ruff + mypy on the changed file (issue Testing Expectations); bandit
  baseline on this file must not regress.
- Docs checker after the `agent_10_05` edit.

## Risks

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| Moving the config load to the top of `save()` loads config even for payloads that currently early-return before the filter's load — but `save()` already loads unconditionally at line 164 today, so no new loads exist in any path. | Low | Low | Verified by code reading; test 2 pins the non-JSON case at exactly 1. |
| Filter-failure containment (`# noqa: BLE001`) interacts with the new ordering (cfg loaded before the try). | Low | Low | `_load_diagnostics_config()` sits outside the filter try today (164 after it); moving it before the try only changes WHEN it can raise — a config parse failure raises in both old and new code, since save() already calls it unconditionally today. Existing exception contract preserved. |
| Helper-parameter threading misses a call site (e.g. a helper called elsewhere). | Low | Low | `_filter_sensitive_fields`/`_purge_old_diagnostics` have no callers outside this class (grep-verified); mypy enforces the new required parameters. |

## Execution Status

| Item | Status |
|---|---|
| Plan | Frozen |
| Phase 1 (load-count tests, red) | Pending |
| Phase 2 (cfg threading) | Pending |
| Phase 3 (doc + full validation) | Pending |

## Traceability

- Implementation step 1 → REQ-001, REQ-006 (tests 1-4 encode AC-001, AC-003).
- Implementation step 2 → REQ-001..REQ-005.
- Implementation step 3 → REQ-006, AC-005.

## Requirement Traceability

| Requirement | Test / Evidence | Acceptance Criterion |
|---|---|---|
| REQ-001 | Load-count tests 1-3 | AC-001 |
| REQ-002 | mypy (required parameters), no second loader (code review of single `_load_diagnostics_config` point) | AC-004 |
| REQ-003 | Unmodified existing suite + test 4 | AC-002, AC-003 |
| REQ-004 | Test 4 snapshot-consistency + no cache in code | AC-001 |
| REQ-005 | Unmodified caller tests (persister/regression) | AC-002 |
| REQ-006 | New tests + docs diff | AC-001, AC-005 |
