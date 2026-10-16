## Goal

Keep the cross-cutting ADR-004 failure-handling assertions alive after the audit is removed, by re-basing
them on the surviving fail-closed paths: published posture and Agent startup classification (`REQ-017`,
`AC-008`, ADR-004 `INV-01`, `INV-02`, `INV-07`, `INV-10`).

## Scope

- One modified test file `tests/agent/test_failure_handling_policy_cross_cutting.py` (194 lines): keep the
  eight test names and their ADR-004 invariant mapping, replace the audit mechanism they drive with the
  posture mechanism from rows `17`-`18`.
- No ADR cites this file, so the bodies may be rewritten freely.

## Assumptions

- Current file verified: docstring at `:1-5` ("Cross-cutting tests for ADR-004 environment failure handling
  policy. Covers ADR-004 INV-01, INV-02, INV-07 and INV-10."), `from agent.security_audit_config import
  (GitAuditConfig, GitHubAuditConfig, ShellAuditConfig)` at `:12-16`,
  `from agent.services.security_audit import audit_security_defaults` at `:17`, `_make_ctx(lockdown=False)`
  at `:20-28` (sets `ctx.cfg.mcp.security_lockdown_enabled`, `ctx.cfg.tool.allowed_tools`,
  `ctx.cfg.approval.tool_safety_tiers`), the `_SHELL_OK`/`_GIT_OK`/`_GITHUB_OK`/`_CICD_OK` fixtures at
  `:31-40`, the autouse `_patch_cicd` fixture at `:46-53` (patches
  `agent.services.security_audit.load_cicd_audit_config`), and `TestFailureHandlingPolicy` at `:56` with
  eight tests: `test_shell_config_failure_production_raises` `:57`, `test_git_config_failure_production_raises`
  `:69`, `test_github_config_failure_production_raises` `:86`,
  `test_lockdown_does_not_suppress_production_failure` `:107`,
  `test_all_configs_load_success_returns_no_warnings` `:119`,
  `test_partial_config_failure_produces_targeted_exception` `:138`,
  `test_lockdown_mode_validates_required_configs` `:159`,
  `test_non_production_profile_raises_on_config_failures` `:176`.
- The module-level imports at `:12-17` make this file fail at **collection time** once rows `20`-`21` land.
- ADR-004 invariants (`docs/10_adr/adr_02_004_environment-failure-handling-policy.md:215-224`): `INV-01`
  single common failure policy for every environment; `INV-02` environment names do not relax
  safety/validation requirements; `INV-07` authentication, authorization, Allowlist, Safety Tier, Config
  Isolation, and approval-control failures are Fail-Closed (Fail-Fast) at startup; `INV-10`
  Safety/Integrity failures are not converted to partial availability.
- No ADR cites this file: `grep -rn "failure_handling_policy" docs/` returns no match. ADR-004's
  `Implementation References` bullet at `:358` lists only
  `tests/agent/shared/test_startup_validation_pipeline.py` and `tests/agent/test_startup.py`, and
  `tools/check_adr_preservation.py:148-154` makes changing that bullet an ERROR, so this row must not
  touch it.
- The surviving fail-closed path is row `18`: `check_readiness()` raises when a server posture is missing
  or contains a `FAILED` Safety/Integrity check, and `scripts/agent/startup_validation.py:84-93` converts
  that raise into `pipeline.add_fatal("readiness", ...)`.
- `security_lockdown_enabled` is the suppression flag the audit honored
  (`scripts/agent/services/security_audit.py:75-80`); Plan `UNK-02` records that no suppression may be
  re-added in the new validators.

## Design decisions

- Keep all eight test names and their invariant mapping, and change only the mechanism they drive. The
  file's purpose is to prove ADR-004's invariants hold, not to prove the audit's behavior; keeping the
  names keeps the invariant-to-test mapping in `docs/10_adr/adr_02_004_*` readable.
- Drive the tests through `agent.services.mcp_health.check_readiness()` with mocked `/health` posture
  payloads, exactly as `tests/agent/shared/test_startup_validation_pipeline.py` drives the pipeline through
  `agent.startup_validation.check_readiness`. This keeps the assertions on the Agent's decision, which is
  what `INV-07` and `INV-10` are about.
- Re-map each case:
  - the three `*_config_failure_production_raises` cases become "a server posture whose config-validation
    check is `FAILED` produces a FATAL and raises", one case per server family (shell, git, github).
  - `test_lockdown_does_not_suppress_production_failure` becomes "a posture failure is FATAL even when
    `security_lockdown_enabled` is set", which is the executable form of the Plan's no-suppression rule.
  - `test_all_configs_load_success_returns_no_warnings` becomes "all-green postures produce no FATAL and
    no WARNING".
  - `test_partial_config_failure_produces_targeted_exception` becomes "one failed server names that server
    key in the message while the other servers remain OK", which is the posture equivalent of targeted
    exceptions.
  - `test_lockdown_mode_validates_required_configs` becomes "a posture missing a required check is
    rejected", i.e. the contract-completeness rule from row `17` (`check_set_mismatch`).
  - `test_non_production_profile_raises_on_config_failures` becomes "a non-production profile name does not
    downgrade a Safety/Integrity posture failure to a warning", which is `INV-02` and `INV-10` stated
    against the new mechanism.
- Delete `_make_ctx`'s audit-specific fields, the four `*_OK` fixtures, and the `_patch_cicd` autouse
  fixture; replace them with a posture fixture that builds `SecurityPosture` objects from rows `02`-`03`.
- Do not move these cases into `tests/agent/shared/test_startup_validation_pipeline.py`. That file tests
  pipeline aggregation; this file tests the failure-classification policy, and merging them would collapse
  two distinct ADR-004 verification rows.

## Alternatives considered

- Delete the file with the audit — rejected: `INV-01`, `INV-02`, `INV-07`, `INV-10` would lose their only
  cross-cutting test, and ADR-004's own verification story depends on a test that spans environments rather
  than one check.
- Re-base the cases on `ProductionConfigValidator` instead of posture — rejected: that validator covers
  Agent-side tool settings, not server config validity, so it cannot express "a server's allowlist is
  empty" or "sandbox backend is none".
- Re-base them on per-server validator tests — rejected for this file: those live in `tests/mcp_servers/*`
  and prove each server's own decision; this file's role is the Agent-side consequence at startup.
- Keep the audit cases but mark them `xfail` until Phase 3 — rejected: `xfail` asserts nothing, and the
  module-level imports at `:12-17` fail collection before any marker is evaluated.

## Implementation
### Target file

`tests/agent/test_failure_handling_policy_cross_cutting.py` (modify)

### Procedure

1. Replace the imports at `:12-17` with the posture DTO imports from `shared.security.result_dto` and
   `shared.security.posture_contract` plus `agent.services.mcp_health`.
2. Replace `_make_ctx` (`:20-28`) with a context builder that carries `mcp.mcp_servers` entries for the
   servers under test, and replace `_SHELL_OK`/`_GIT_OK`/`_GITHUB_OK`/`_CICD_OK` (`:31-40`) with posture
   fixtures (green, failed-with-reason-code, missing-posture).
3. Delete the `_patch_cicd` autouse fixture (`:46-53`).
4. Rewrite the eight test bodies per the mapping above, keeping each test's name and its `"""ADR-004
   INV-NN..."""` docstring invariant reference.
5. Keep `TestFailureHandlingPolicy` as the class name.

### Method

- Land this row after rows `17`-`18`, because the replacement mechanism must exist before the tests can
  drive it.
- Keep the invariant tags in the docstrings accurate: if a rewritten case no longer covers a named
  invariant, remove that invariant from the docstring rather than leaving a false claim.

### Details

- The file stays roughly the same size (about 190 lines) because eight cases are replaced, not removed.
- `pytest.mark.asyncio` becomes necessary for the posture cases if `check_readiness()` is awaited, matching
  how `tests/agent/shared/test_startup_validation_pipeline.py` marks its async cases.
- `shutil.which` patches (`:64`, `:165`, `:182`) disappear: sandbox-binary presence is now shell-mcp's own
  check (row `7`) and is asserted in `tests/mcp_servers/shell/`.

## Compatibility considerations

- Collection-time `ImportError` is the failure mode if this row lands after rows `20`-`21` and before this
  rewrite.
- `docs/10_adr/adr_02_004_environment-failure-handling-policy.md`'s `Verification` section is row `39`'s
  concern; this row must not edit that file.
- `tests/agent/test_audit_security_failures.py` (row `26`) overlaps these cases and is deleted; this file
  is the surviving home for the invariant.

## Security considerations

- This row is the test-side guarantee that removing the audit does not weaken fail-closed behavior:
  `INV-07` and `INV-10` remain asserted against the new mechanism.
- The no-suppression case is the most important rewritten test: it makes "posture failures cannot be
  silenced by a flag" a regression-checked property.

## Rollback considerations

- Restore with `git checkout -- tests/agent/test_failure_handling_policy_cross_cutting.py` together with
  rows `20`-`21`. Restoring it alone fails collection, because it imports modules those rows delete.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Rewritten suite passes | `uv run pytest tests/agent/test_failure_handling_policy_cross_cutting.py` | eight tests pass against the posture mechanism |
| Fail-closed actually asserted | temporarily make `check_readiness()` swallow a `FAILED` posture, run the suite, then revert | the three `*_raises` cases plus the non-production case fail |
| No-suppression case bites | temporarily add a suppression branch to posture validation, run the suite, then revert | `test_lockdown_does_not_suppress_production_failure` fails |
| ADR gate | `uv run python tools/check_adr_preservation.py` | no finding for `adr_02_004_*` (this file is not cited) |
| Suite integrity | `uv run pytest tests/agent/` | collects without `ImportError` |
| Static gates | `uv run ruff check tests/` | clean |

## Completion criteria

- Plan `AC-008` for this suite: no import of `agent.security_audit_config` or
  `agent.services.security_audit` remains, and all eight ADR-004 cases pass against the posture mechanism.
- ADR-004 `INV-01`, `INV-02`, `INV-07`, `INV-10` each map to at least one passing test in this file.
- No suppression path is introduced by the rewritten tests.

## Out of scope

- Deleting `security_audit.py` (row `20`) or `security_audit_config.py` (row `21`).
- Implementing posture validation (rows `17`-`18`).
- `docs/10_adr/adr_02_004_environment-failure-handling-policy.md` updates (row `39`).
- Per-server validator tests (rows `7`-`16`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace imports and fixtures with posture DTOs | Pending | — | — | depends on rows `02`, `03` |
| 2 | Rewrite the eight test bodies | Pending | — | — | depends on rows `17`, `18` |
| 3 | Delete the `_patch_cicd` fixture | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `tests/agent/test_failure_handling_policy_cross_cutting.py`
