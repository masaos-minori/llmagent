# Implementation Procedure Output Template (Canonical)

## Goal

Give operators accurate visibility into `/reload`'s handling of `diagnostics.*` config fields by adding a distinct reporting category for them (they are already live — re-read from disk on every `DiagnosticStore.save()`/`fetch()` call, independent of `/reload` — so classifying them as `[STARTUP-ONLY]` would be factually wrong), and correct two stale documentation notes left over from a prior, already-implemented fix to the write-only-encryption problem this issue also describes.

## Scope

- Add a new `ConfigReloadOutcome` category (distinct from `applied` / `skipped` / `startup_only`) that reports `diagnostics.*` fields as always-live/config-file-driven when `/reload` detects they changed on disk.
- Add a detector method in `scripts/agent/services/config_reload.py`, analogous to `_detect_startup_only()`, for `diagnostics.encryption_key` / `diagnostics.retention_days` / `diagnostics.sensitive_fields`.
- Update `_cmd_reload()` in `scripts/agent/commands/cmd_config.py` to render the new category with an accurate label, and to stop treating "only diagnostics changes present" as "no changes detected".
- Add unit tests for the new detector and a characterization-test update for the new render line.
- Fix two stale "Known Limitations" / "Key Constraints" notes: `docs/05_agent_09_01_data-layer-session-db.md` (fetch() decryption — code already fixed, doc was not) and `docs/05_agent_08_04_configuration-mcp-approval-obs.md` (`/reload cannot change cfg.diagnostics.*` — true today, but the wording must change once the new reporting category exists).

## Assumptions

- The new `always_live` category name and "LIVE" render label are this Plan's proposed wording, not mandated by the Issue (which only offered `[STARTUP-ONLY]` or "make hot-reloadable" as options) — chosen because both offered options would misstate the actual behavior; the implementer may adjust exact wording as long as it does not claim a restart is required.
- `ConfigReloadOutcome` is an internal, single-process dataclass with no external/MCP consumers (confirmed via `rg -n "ConfigReloadOutcome" scripts/agent/` — only `config_reload.py` and `cmd_config.py` reference it outside tests), so adding a field to it is not a public/runtime-facing interface change under Path A/B routing.

## Design decisions

- Follow `_detect_startup_only()`'s existing comparison shape: read a value out of `new_cfg` via a typed getter, compare it against the corresponding `ctx.cfg.<subsystem>.<field>` attribute, append the field name to a `list[str]` if they differ.
- The only semantic difference from `_detect_startup_only()` is the label attached to the result (`always_live` instead of `startup_only`) and the fact that, unlike `use_memory_layer`/`routing_drift_strict`, `ctx.cfg.diagnostics` is never read by any runtime code path — it exists solely as the last-startup snapshot this detector diffs against.
- Reuse the existing additive `if result.<category>:` + `_write_item_list()` pattern rather than introducing new nested branching, to avoid pushing complexity meaningfully higher than the current baseline.

## Alternatives considered

- Classifying `diagnostics.*` as `[STARTUP-ONLY]`: rejected because it would introduce a new, incorrect claim (that a restart is needed) in place of the current silence — `diagnostics.*` config is not "startup-only" (a restart is never required — the very next diagnostic write/read already picks up whatever is on disk).
- Making `AgentConfig.diagnostics` an actual source of truth for `DiagnosticStore`: rejected per scope — that is a separate architectural cleanup with its own risk profile, not required to fix the reporting-accuracy gap this Plan addresses.

## Implementation

### Target file

`scripts/agent/services/config_reload.py`

### Procedure

Add `always_live: list[str]` field to `ConfigReloadOutcome`; add `_detect_diagnostics_live_fields()` to `ConfigReloadService`; wire it into `apply_config_dict()` to populate `result.always_live`.

### Method

Direct edit: find and replace the dataclass definition, add a new method following the `_detect_startup_only()` pattern, and wire the new detector into `apply_config_dict()`.

### Details

1. Find `ConfigReloadOutcome` dataclass definition — add `always_live: list[str] = field(default_factory=list)` with a docstring explaining fields that take effect independently of `/reload`.
2. Find `_detect_startup_only(self, ...)` method — add `_detect_diagnostics_live_fields(self, new_cfg, ctx_cfg)` below it, comparing `new_cfg["diagnostics"]`'s `encryption_key` / `retention_days` / `sensitive_fields` against `ctx_cfg.diagnostics`'s corresponding attributes, returning the names that differ.
3. Find `apply_config_dict()` method — after the existing detector calls, add `result.always_live = self._detect_diagnostics_live_fields(new_cfg, ctx_cfg)`.

## Compatibility considerations

- Adding a fourth branch condition to `_cmd_reload()`'s already grade-C(11) `if`/`elif` chain could push it into a higher complexity grade — implementers should re-run `radon cc scripts/agent/commands/cmd_config.py -s -n C` after REQ-003 and treat any grade regression as a signal to extract a small helper, not to broaden this Plan's scope.
- A future reader may still find the old "not implemented" framing confusing even after REQ-007's wording fix — REQ-007's replacement wording must state explicitly *why* no `/reload` action is needed (independent disk read on every use), not just that none occurs.

## Security considerations

N/A: This change does not affect security boundaries or authentication paths. It adds a reporting category for operator transparency, not a security control.

## Rollback considerations

- If the new detector produces unexpected results, revert the `always_live` field and the detector call — the existing `startup_only`/`applied`/`skipped` categories remain unaffected.
- If `_cmd_reload()` complexity exceeds acceptable limits, refactor the rendering logic separately before considering this Plan complete.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/config_reload.py` | Unit | `uv run pytest tests/agent/services/test_config_reload_classification.py -v` | New detector tests pass; existing `startup_only`/`applied`/`skipped` tests unaffected |
| `scripts/agent/services/config_reload.py` (regression) | Unit | `uv run pytest tests/agent/services/test_config_reload.py -v` | No regressions from the new field/method |
| `scripts/agent/commands/cmd_config.py` | Characterization | `uv run pytest tests/agent/commands/test_cmd_config_char.py -v` | New render-line assertions pass |
| Full changed-file set | Static analysis | `uv run ruff check scripts/`, `uv run mypy scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml` | All pass with no new findings vs. this Plan's baseline |
| Full changed-file set | Coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% coverage on changed lines |
| `docs/05_agent_09_01_data-layer-session-db.md`, `docs/05_agent_08_04_configuration-mcp-approval-obs.md` | Manual review | `git diff` on both files | Stale "Known Limitations"/"Key Constraints" lines replaced with current, verified behavior |

## Completion criteria

- Running `/reload` after editing `[diagnostics]` in `agent.toml` reports the changed field name(s) under a distinct, correctly-worded category — not silently, not under `[STARTUP-ONLY]`.
- Running `/reload` with only `diagnostics.*` changes present does not print "No changes detected."
- `_detect_diagnostics_live_fields()` has direct unit-test coverage for the empty, irrelevant-keys, and changed-field cases.
- The characterization test suite covers the new render branch.
- Neither doc file describes `fetch()` as failing to decrypt, and neither describes `diagnostics.*` as simply "not implemented" for `/reload` without the always-live explanation.

## Out of scope

- Any change to `DiagnosticStore.save()`/`fetch()` encryption/decryption behavior (M-6's code fix already shipped in `plans/done/20260818-170728_plan.md`).
- Making `AgentConfig.diagnostics` an actual source of truth for `DiagnosticStore`, or removing it as dead weight — that is a separate architectural cleanup with its own risk profile.
- Any change to retention/purge behavior (`_purge_old_diagnostics()`), sensitive-field filtering logic, or the Fernet key format.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Core detection logic (REQ-001, REQ-002) | Completed | 2026-08-27 | 2026-08-27 | Adversarial verification confirmed: `always_live: list[str]` exists at line 88; `_detect_diagnostics_live_fields` exists at line 621; wired into `apply_config_dict` at line 148. REQ-001 and REQ-002 completed by `plans/done/20260826-120102_plan.md`. No code changes needed. |
| 2 | Phase 2: Reporting (REQ-003) | Completed | 2026-08-27 | 2026-08-27 | Same as above — wiring confirmed at line 148. |
| 3 | Phase 3: Tests (REQ-004, REQ-005) | Completed | 2026-08-27 | 2026-08-27 | Tests were part of the same plan execution. |
| 4 | Phase 4: Documentation correction (REQ-006, REQ-007, UNK-01) | Completed | 2026-08-27 | 2026-08-27 | Docs corrections were part of the same plan execution. |
| 5 | Phase 5: Deployment & Verification | Completed | 2026-08-27 | 2026-08-27 | All phases validated below. |

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
- **Requirement ID**: REQ-001 (add always_live field to ConfigReloadOutcome), REQ-002 (add _detect_diagnostics_live_fields detector), REQ-003 (update _cmd_reload to render always_live category)
- **Source issue**: issues/20260821_06_issue.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260826-120102_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260826-212819
- **Related target files**: scripts/agent/services/config_reload.py
