## Goal

Keep the pipeline-aggregation and ADR-004 `INV-07` tests valid after the audit step is removed, by moving the
FATAL injection point from the audit to the surviving `readiness` path (`REQ-017`, `AC-008`).

## Scope

- One modified test file `tests/agent/shared/test_startup_validation_pipeline.py` (474 lines): delete seven
  `patch(f"{MODULE}.audit_security_defaults", ...)` blocks, and re-base the three tests that used the audit as
  their only FATAL injection onto `check_readiness`.
- No production behavior changes in this row; row `22` removes the pipeline step.

## Assumptions

- Current file verified: `MODULE = "agent.startup_validation"` at `:21`; the audit patches are at `:132`
  (`return_value=[]`), `:176-179` (`side_effect=RuntimeError("security audit failed")`), `:297-300`
  (`side_effect=RuntimeError("security audit failed")`), `:332` (`return_value=[]`), `:373`
  (`return_value=[]`), `:421-424` (`side_effect=RuntimeError("Allowlist verification failed")`), and `:456`
  (`return_value=[]`).
- Test map: `test_validation_result_*` at `:27-58` (pure `StartupValidationResult` unit tests, no patches);
  `test_warnings_only_no_raise` `:91`, `test_routing_drift_strict_true_raises_fatal` `:103`,
  `test_routing_drift_strict_false_warns_only` `:114`, `test_skipped_live_routing_no_raise` `:127`,
  `test_validation_pipeline_reports_fatal_when_config_missing` `:158`,
  `test_build_agent_config_requires_agent_toml` `:199`, `test_check_routing_safety_tiers_context` `:241`,
  `TestFaltyOwnConfigFileScenario` `:273` (`test_falsy_own_config_file_produces_fatal` `:283`,
  `test_truthy_own_config_file_does_not_produce_fatal` `:318`), `TestUnknownTopLevelKeyScenario` `:349`
  (`test_unknown_top_level_key_produces_error_in_production` `:359`), and `TestInv07EnvironmentFailureHandling`
  `:393` (`test_allowlist_failure_produces_fatal` `:407`, `test_safety_tier_failure_produces_fatal` `:442`).
- Three tests inject their only FATAL through the audit `side_effect`: `:158`, `:283`, and `:407`. Each asserts
  `pytest.raises(RuntimeError, match="Startup validation failed")`. The other four audit patches are clean-pass
  entries that only neutralize the audit while another check produces the outcome under test.
- `scripts/agent/startup_validation.py:84-93` already converts a `check_readiness()` raise into
  `pipeline.add_fatal("readiness", ...)` and raises `RuntimeError("Startup validation failed: ...")`, so
  `check_readiness` is a live FATAL injection point after row `22`.
- `docs/10_adr/adr_02_003_runtime-tool-registry-routing-authority.md:254` and
  `docs/10_adr/adr_02_004_environment-failure-handling-policy.md:358` reference this file as a bare backtick
  path. `tools/check_adr_preservation.py:148-154` makes changing the ADR-004 `Implementation References` bullet
  an ERROR, and `:181-185` warns when a backtick path token disappears, so the file path must stay present in
  both ADRs. No ADR cites a `path.py::name` test from this file.
- The class docstrings at `:276-279` and `:352-354` already state that Config Isolation and unknown-key
  validation happen outside the pipeline, and that this file verifies aggregation only.

## Design decisions

- Re-base the three FATAL injections onto `patch(f"{MODULE}.check_readiness", side_effect=RuntimeError(...))`.
  These tests assert that the pipeline aggregates a check failure into a FATAL and aborts startup; the audit was
  only a convenient failing check. `check_readiness` is the surviving check that carries security failures, so
  the re-based tests assert the same aggregation property against the mechanism that now exists.
- Keep each test's message text meaningful to its subject instead of reusing "security audit failed":
  `:158` uses a readiness/config message, `:283` uses a config-isolation message, and `:407` keeps
  `"Allowlist verification failed"`. After this Plan an allowlist failure is a server-side posture `FAILED`
  result that makes `check_readiness()` raise, so the message becomes more accurate rather than less.
- Keep all test names, class names, and the `MODULE` constant unchanged. `docs/10_adr/adr_02_004_*:358` names
  this file, and the aggregation tests are the pipeline's regression net.
- Delete the four clean-pass audit patches outright rather than replacing them with `check_readiness` clean
  mocks: each of those tests already patches `check_readiness` (`:133-137`, `:301-303`, `:333-335`, `:374-376`,
  `:425-427`, `:457-459`), so adding a second clean mock would be redundant.
- Do not merge this file into `tests/agent/test_startup_severity_classification.py` (row `33`). This file
  asserts aggregation and raise behavior; that file asserts per-source severity mapping.

## Alternatives considered

- Delete the three FATAL tests with the audit — rejected: they are the only tests that prove a failing check
  becomes `RuntimeError("Startup validation failed")` at the orchestrator boundary, which is ADR-004 `INV-07`'s
  pipeline-level assertion.
- Re-base the injections onto `mcp_auth` instead of `readiness` — rejected: `mcp_auth` is driven by
  `ctx.cfg.mcp.mcp_servers` contents, which would make each test assert token shape rather than aggregation,
  and `tests/agent/test_startup_severity_classification.py` already owns the `mcp_auth` cases.
- Re-base them onto `check_routing_safety_tiers` — rejected: that would make the allowlist case assert a safety
  tier, blurring the `INV-07` distinction between Allowlist and Safety Tier failures that the two tests
  deliberately separate.
- Keep the audit patches and add a permanent no-op `audit_security_defaults` to the pipeline — rejected: row
  `22` removes the source, and a no-op check makes the aggregation tests assert a placeholder.

## Implementation
### Target file

`tests/agent/shared/test_startup_validation_pipeline.py` (modify)

### Procedure

1. Delete the clean-pass audit patches at `:132`, `:332`, `:373`, and `:456`.
2. Replace the audit `side_effect` patch at `:176-179` with
   `patch(f"{MODULE}.check_readiness", new_callable=AsyncMock, side_effect=RuntimeError("readiness check failed"))`,
   and delete the now-duplicate clean `check_readiness` patch at `:180-184`.
3. Replace the audit `side_effect` patch at `:297-300` with a `check_readiness` `side_effect` patch carrying a
   config-isolation message, and delete the clean `check_readiness` patch at `:301-303`.
4. Replace the audit `side_effect` patch at `:421-424` with a `check_readiness` `side_effect` patch carrying
   `"Allowlist verification failed"`, and delete the clean `check_readiness` patch at `:425-427`.
5. Keep every other patch, assertion, test name, class name, and docstring unchanged, including the `INV-07`
   docstring at `:394-404`.

### Method

- Land this row in the same commit as row `22`. Before row `22` the audit patches still match real imports;
  after row `22` without this row every patched test fails with `AttributeError`.
- Verify each re-based test still asserts aggregation rather than the new mechanism: the assertion must remain
  `pytest.raises(RuntimeError, match="Startup validation failed")`.

### Details

- The file stays at 474 lines within a few lines: seven patch blocks are removed and three are converted.
- `AsyncMock` is already imported at `:7` and is used by the `check_readiness` patches, so no import changes
  are needed.
- `patch` blocks are parenthesized context managers; removing one entry must not change the remaining entries'
  indentation.

## Compatibility considerations

- `docs/10_adr/adr_02_003_runtime-tool-registry-routing-authority.md:254` and
  `docs/10_adr/adr_02_004_environment-failure-handling-policy.md:358` must keep naming this file; rows `38`
  and `39` own those ADR edits and must not drop the token.
- `tests/agent/test_startup.py` (row `30`), `tests/agent/test_startup_validation.py` (row `32`),
  `tests/agent/test_startup_severity_classification.py` (row `33`), and
  `tests/agent/test_startup_memory_failures.py` (row `34`) use the same patch-by-name pattern and land in the
  same phase.
- `tests/agent/test_failure_handling_policy_cross_cutting.py` (row `29`) asserts the policy level of the same
  invariants; this file asserts pipeline aggregation.

## Security considerations

- `INV-07`'s guarantee that Allowlist and Safety Tier failures are Fail-Closed at startup stays asserted after
  this row, and after this Plan it is asserted against the path that actually carries those failures: a server
  posture `FAILED` result reaching `check_readiness()`.
- Re-basing rather than deleting keeps the abort-on-security-failure boundary testable.

## Rollback considerations

- Revert this commit together with row `22`. Reverting row `35` alone fails with `AttributeError` on
  `agent.startup_validation.audit_security_defaults`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Aggregation tests pass | `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py` | all tests pass after row `22` lands, no `AttributeError` |
| FATAL injection is live | temporarily make `check_readiness` swallow the raise in `startup_validation.py`, run the file, then revert | the three re-based tests fail |
| `INV-07` cases intact | `uv run pytest "tests/agent/shared/test_startup_validation_pipeline.py::TestInv07EnvironmentFailureHandling"` | both tests pass |
| Audit patches gone | `grep -n "audit_security_defaults" tests/agent/shared/test_startup_validation_pipeline.py` | no matches |
| ADR gate | `uv run python tools/check_adr_preservation.py` | no ERROR for `adr_02_003_*` or `adr_02_004_*` |
| Suite integrity | `uv run pytest tests/agent/` | collects without `ImportError` |
| Static gates | `uv run ruff check tests/` | clean |

## Completion criteria

- Plan `AC-008` for this file: no `audit_security_defaults` patch remains.
- The three re-based tests still assert that a failing check produces `RuntimeError("Startup validation failed")`.
- Both `TestInv07EnvironmentFailureHandling` cases pass against the `readiness` injection point.

## Out of scope

- Removing the pipeline step (row `22`).
- Implementing posture gating in `check_readiness()` (row `18`).
- The severity matrix file (row `33`).
- `docs/10_adr/adr_02_003_*` and `docs/10_adr/adr_02_004_*` updates (rows `38`, `39`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the four clean-pass audit patches | Completed | 2026-10-17 | 2026-10-17 | four clean-pass patches deleted, landed with row 22 |
| 2 | Re-base the three FATAL injections onto `check_readiness` | Completed | 2026-10-17 | 2026-10-17 | three FATAL injections re-based onto check_readiness, the readiness step now carries posture validation |
| 3 | Confirm both ADR references to this file remain intact | Completed | 2026-10-17 | 2026-10-17 | ADR-004:358 and ADR-003:254 citations to this file intact |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-17 | 2026-10-17 | ruff clean, tests/agent 3332 passed with only the 9 known test_startup_rollback failures |

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
- **Requirement ID**: `REQ-017` (remove Agent-side cross-config audit)
- **Source issue**: `issues/done/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `tests/agent/shared/test_startup_validation_pipeline.py`
