## Goal

Extend the existing Git security logic into a full self-validation entry point that returns the
common Security Posture, so git-mcp validates its own configuration instead of being audited by the
Agent (`REQ-006`, `AC-005`).

## Scope

- One modified module `scripts/mcp_servers/git/git_security.py`: add a Git self-validation entry
  point that produces `SecurityCheckResult` values from the rules this module already implements.
- The existing runtime guards (`is_within_allowed_paths()`, `GitSecurityGuards._check_repo_path()`,
  `_check_write()`, `_check_protected_branch()`) keep their current signatures and behavior.
- Publishing on `/health` uses row `06`; git-mcp's server module is not a Plan row.

## Assumptions

- Current module contents verified: `_resolve_repo_path()` at `:15-28`,
  `is_within_allowed_paths()` at `:31-60` (fail-closed empty list at `:44-45`, component-aware
  containment at `:55`), `GitSecurityGuards` at `:63-102` with `_check_repo_path()` delegating the
  allowlist decision to subclasses at `:89-90`.
- The rule the removed Agent audit enforced for Git is the empty-allowlist DENY-ALL warning
  (`scripts/agent/services/security_audit.py:161-171`), which this module already enforces at call
  time (`git_security.py:44-45`) but never reports at startup.
- `GitConfig.allowed_repo_paths` is the config input the audit read through
  `load_git_audit_config()` (`scripts/agent/security_audit_config.py:63-73`).
- **Needs confirmation**: the Git check ids and reason codes below are finalized here from `REQ-006`;
  `memo2.md`'s original list is unrecoverable (Plan `UNK-01`).

## Design decisions

- Add `validate_git_security(allowed_repo_paths: Sequence[str], read_only: bool) -> list[SecurityCheckResult]`
  (new) as the startup-time entry point. It is a pure function of config values, so it can run
  before any repository state exists and before HTTP bind (`REQ-003`).
- Add `GitSecurityGuards.validate_security(self) -> list[SecurityCheckResult]` (new) as the
  instance-level variant that also reports the guards' installed state. The class-level function is
  what the startup flow calls; the instance method exists so a service that already holds config can
  produce the same checks without re-reading it.
- Check ids (finalized here, Needs confirmation): `server.repo_allowlist` (non-empty),
  `server.repo_allowlist_resolvable` (every configured root resolves without `OSError`),
  `server.read_only_mode` (status `NOT_APPLICABLE` with reason `not_applicable` when writes are
  disabled, never silently skipped), `server.protected_branch_config` (the protected-branch rule is
  installed).
- Empty `allowed_repo_paths` is `FAILED` with reason code `allowlist_empty`. The existing
  "[DENIED] allowed_repo_paths is empty" runtime message (`:45`) is preserved unchanged; the new
  startup check does not replace it, because per-call denial is still required even after a passing
  startup check.
- The containment rule is not re-implemented: `validate_git_security()` calls
  `is_within_allowed_paths()` with each configured root as the probe path to prove the root is
  contained in itself. Reusing the function is what keeps the startup check and the runtime check
  from diverging.

## Alternatives considered

- Add the validation to `git_models.py`'s `GitConfig.load()` — rejected: `git_models.py` is not a row
  in the Plan's frozen table, and config loading is the `SCHEMA_VALIDATION` stage, not the
  `SERVER_SECURITY_VALIDATION` stage of `REQ-003`.
- Validate through `GitSecurityGuards.__init__` by raising on bad config — rejected: raising in a
  constructor cannot produce the posture, and `REQ-002` requires the failure to be reportable on
  `/health`, not only as an exception.
- Report empty allowlist as a warning-only check — rejected: the Plan `Assumptions` retire lockdown
  suppression, and an empty allowlist means git-mcp rejects every operation, which is a validation
  failure the Agent must see.

## Implementation
### Target file

`scripts/mcp_servers/git/git_security.py` (modify)

### Procedure

1. Import `SecurityCheckResult` and the reason-code vocabulary from `shared.security.result_dto`
   (row `02`).
2. Add `validate_git_security()` (new) after `is_within_allowed_paths()` (`:60`).
3. Add `GitSecurityGuards.validate_security()` (new) to the class at `:63-102`.
4. Keep `_resolve_repo_path()`, `is_within_allowed_paths()`, `_check_repo_path()`, `_check_write()`,
   `_check_protected_branch()` unchanged.

### Method

- `server.repo_allowlist_resolvable` calls `_resolve_repo_path(root)` for each configured root and
  maps a `False` result to `FAILED` with reason code `allowed_dir_invalid`. This catches a configured
  root that cannot be canonicalized, which today only surfaces on a tool call.
- `server.read_only_mode` uses reason code `not_applicable` when `read_only=True`. Plan `Design`
  requires an explicitly `not_applicable` check id rather than silently skipping a check, so the
  posture's check set stays identical across configurations (needed by row `05`'s CHECKSET
  comparison).
- `server.protected_branch_config` reports whether the protected-branch rule can be evaluated, i.e.
  whether a repository state source is wired. With no repository state it is `FAILED` with reason
  code `dependency_unreachable`, because `_check_protected_branch()` (`:98-102`) would then always
  report "not protected" without evidence.
- Messages name the check and the reason only. Configured repository roots are sensitive paths under
  `REQ-002`, so a failing message may report the count of roots, never their values.

### Details

- The module is 102 lines; the addition is roughly 45 lines and stays under the 200-line convention.
- `is_within_allowed_paths()`'s documented "callers must enforce non-empty allowed_repo_paths"
  contract (`:42-43`) is now enforced at startup by `server.repo_allowlist`, which is the point where
  that precondition becomes verifiable.
- `GitSecurityGuards.__init__` (`:69-76`) is unchanged, so `GitService` construction and the existing
  tests that call `svc._check_repo_path()` / `svc._check_write()` keep working.

## Compatibility considerations

- No existing signature or return contract changes; the change is additive.
- `tests/mcp_servers/git/*` that assert `[DENIED]` messages keep passing because those strings are
  untouched.
- Behavior change is limited to startup: a git-mcp configured with an empty `allowed_repo_paths` now
  reports a failed posture and cannot report `ready=true` (row `06`). Its runtime denial behavior was
  already fail-closed.
- No `docs/*.md` change is in scope for this row.

## Security considerations

- `REQ-006` / Plan `INV-05`: git-mcp validates its own config before Ready; the Agent no longer reads
  `git_mcp_server.toml` (row `21` removes `load_git_audit_config()`).
- `REQ-002` / Plan `INV-09`: repository root paths are sensitive paths and must not appear in the
  posture or in check messages.
- Fail-closed semantics are preserved: empty allowlist remains deny-all at runtime (`:44-45`,
  `:53-60`) and becomes a startup failure.

## Rollback considerations

- Revert this commit. Nothing else in the module changes, so `GitService` and its tests return to the
  previous behavior with no further action.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Empty allowlist | `uv run pytest tests/mcp_servers/git/test_git_security_validation.py` (new test file) | `server.repo_allowlist` `FAILED`, reason `allowlist_empty` |
| Unresolvable root | same new test file | `server.repo_allowlist_resolvable` `FAILED`, reason `allowed_dir_invalid` |
| read_only mode | same new test file | `server.read_only_mode` present with status `NOT_APPLICABLE` when `read_only=True` |
| Deterministic check set | same new test file | the same four check ids appear for every configuration |
| Existing Git suite | `uv run pytest tests/mcp_servers/git/` | passes, `[DENIED]` assertions unchanged |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Completion criteria

- Plan `AC-005` for Git: git-mcp validates its own configuration and returns the common posture.
- The four finalized check ids are always present, with `not_applicable` used instead of omission.
- No configured repository path appears in any posture field or message.

## Out of scope

- Editing `scripts/mcp_servers/git/git_models.py` or `git_server.py` (not Plan rows).
- Changing runtime denial behavior or `[DENIED]` message text.
- Publishing on `/health` (row `06`) and Agent-side validation (rows `17`-`18`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `validate_git_security()` + `GitSecurityGuards.validate_security()` | Completed | 20261016-204345 | 20261016-204345 | check ids are Needs-confirmation Check ids finalized as the four frozen ids in REQUIRED_CHECK_IDS for git: server.repo_allowlist, server.repo_allowlist_resolvable, server.read_only_mode, server.protected_branch_config. validate_git_security is a pure function of config values and never raises. server.repo_allowlist_resolvable probes each configured root with is_within_allowed_paths so the startup and runtime containment decisions cannot diverge, and maps a failure to allowed_dir_invalid; a configured root whose own text is not canonical, for example one containing a dot-dot segment, is therefore rejected at startup. An empty allowlist is FAILED with allowlist_empty and server.repo_allowlist_resolvable becomes NOT_APPLICABLE instead of double-counting the same failure. Ambiguity resolved by user decision: the config-only view reports server.protected_branch_config as ok because the rule is installed by construction, and only GitSecurityGuards.validate_security reports dependency_unreachable, and only when _repo_state is None. GitSecurityGuards now carries a class-level _allowed_repo_paths default so the instance view is fail-closed when no host service provides it. Verified finding: GitSecurityGuards is not installed on GitService and no module imports it, so the instance method is exercised only by the new tests. Module is 261 lines, above the 200-line guideline in Details, accepted as a deviation as with row 04; the split trigger in skills/DESIGN.md is 400 lines. |
| 2 | Add `tests/mcp_servers/git/test_git_security_validation.py` | Completed | 20261016-204345 | 20261016-204345 | tests/mcp_servers/git/test_git_security_validation.py: 17 tests, all pass, and tests/mcp_servers/git reports 371 passed. Covers the empty allowlist, empty and non-canonical root entries, the count-only failure message, read_only in both modes, the config-view protected-branch check, the frozen id set and fixed order, identical check sets across four configurations, and the guards view including a missing repository state and an uninstalled allowlist. No test depends on a real repository or a host path. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261016-204847 | 20261016-204847 | Full validation sequence: ruff clean, mypy clean on 421 source files, lint-imports 6 kept 0 broken, bandit reports no finding in git_security.py (the git package keeps 10 pre-existing Low findings in format_output.py, git_server.py and git_service.py and no High), check_mock_patch_targets no findings, check_docstrings reports no finding in the changed file after the module docstring separator was added, no bare except. Full suite: 8652 passed, 19 skipped, 9 failed, and all 9 are the pre-existing tests/agent/test_startup_rollback.py schema-version failures. Coverage and diff-cover are deferred to the end of the procedure batch. |

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
- **Requirement ID**: `REQ-006` (Git self-validation)
- **Source issue**: `issues/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/mcp_servers/git/git_security.py`