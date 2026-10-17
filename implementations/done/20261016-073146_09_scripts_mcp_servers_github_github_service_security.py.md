## Goal

Turn the GitHub server's existing guard mixin into a self-validation entry point that returns the
common Security Posture, so github-mcp validates its own policy instead of being audited by the
Agent (`REQ-007`, `AC-005`).

## Scope

- One modified module `scripts/mcp_servers/github/github_service_security.py`: add a GitHub
  self-validation function that produces `SecurityCheckResult` values from the rules this mixin
  already enforces at call time.
- Existing guard methods keep their signatures and behavior; only a startup-time validator is
  added.
- Publishing on `/health` is row `44` (`scripts/mcp_servers/github/github_server.py`).

## Assumptions

- Current mixin verified: `GitHubSecurityGuards` at `scripts/mcp_servers/github/github_service_security.py:31`,
  `__init__(gh, cfg)` at `:34-39`, `_clamp_per_page()` at `:41-44`, `_assert_allowed_repo()` at
  `:46-62` (empty `allowed_repos` denies all), `_assert_allowed_path()` at `:64-74`
  (`path_denylist` globs), `_assert_max_file_size()` at `:76-89` (`max_file_size_kb <= 0` disables
  the check), `_write_github_audit_log()` at `:91-112` (empty `audit_log_path` returns silently at
  `:101-102`), `_assert_allowed_branch()` at `:114-128` (empty `protected_branches` means no
  branch restrictions), `_resolve_and_check_branch()` at `:134-151`.
- The rules the removed Agent audit enforced for GitHub are: empty `allowed_repos` DENY-ALL warning
  (`scripts/agent/services/security_audit.py:174-182`), `allow_force_push=true` warning
  (`security_audit.py:205-208`), `require_pr_review=false` warning (`security_audit.py:209-212`).
- **Needs confirmation**: the GitHub check ids below are finalized here from `REQ-007`;
  `memo2.md`'s original list is unrecoverable (Plan `UNK-01`).

## Design decisions

- Add `validate_github_security(cfg: GitHubConfig) -> list[SecurityCheckResult]` (new module-level
  function). It is a pure function of the server's own config object, so it runs before any GitHub
  API call and before HTTP bind (`REQ-003`).
- Warning-only policy settings map to status `WARNING` (row `02`), not `FAILED`:
  `allow_force_push=true` and `require_pr_review=false` keep the server startable, exactly as the
  old audit left them startable. `validated` stays `true` (`REQ-013` treats only `validated=false`
  as a Safety/Integrity abort).
- Check ids (finalized here, Needs confirmation):
  - `server.repo_allowlist` — empty `allowed_repos` is `FAILED` with reason `allowlist_empty`.
  - `server.force_push_policy` — `allow_force_push=true` is `WARNING` with reason
    `force_push_enabled`; otherwise `OK`.
  - `server.pr_review_required` — `require_pr_review=false` is `WARNING` with reason
    `destructive_guard_missing`; otherwise `OK`.
  - `server.protected_branches` — empty `protected_branches` is `NOT_APPLICABLE` with reason
    `not_applicable`, matching the documented "empty list means no branch restrictions" behavior
    (`:118-119`), instead of being silently skipped.
  - `server.path_denylist` — empty `path_denylist` is `NOT_APPLICABLE` with reason
    `not_applicable`.
  - `server.max_file_size` — `max_file_size_kb <= 0` is `NOT_APPLICABLE` with reason
    `not_applicable`, matching the existing "0 disables the limit" behavior (`:83-84`).
  - `server.audit_log_writable` — empty `audit_log_path` is `NOT_APPLICABLE`; a configured path
    whose parent directory is missing or unwritable is `FAILED` with reason
    `dependency_unreachable`, because today that failure only appears as a `GitHubAuditError` on
    the first guarded call (`:110-112`).
  - `server.per_page_bounds` — `max_per_page <= 0` or `default_per_page > max_per_page` is `FAILED`
    with reason `config_invalid`; `_clamp_per_page()` (`:43`) silently clamps today, so a reversed
    bound is currently invisible.
- `NOT_APPLICABLE` is used instead of omission so the posture's check set is identical for every
  configuration, which row `05`'s CHECKSET comparison requires.

## Alternatives considered

- Map `allow_force_push=true` and `require_pr_review=false` to `FAILED` — rejected: the old audit
  treated both as warnings (`security_audit.py:205-212`), so `FAILED` would make currently working
  configurations unstartable. The Plan's Design section records the `WARNING` status decision.
- Add the validator to `GitHubService.__init__` — rejected: `github_service.py` is not a row in the
  Plan's frozen table, and constructor-time raising cannot produce the posture.
- Validate `path_denylist` patterns by compiling each glob — rejected as a startup check: a pattern
  that matches nothing is a policy choice, not a technical failure, and reporting it `FAILED` would
  add no safety.

## Implementation
### Target file

`scripts/mcp_servers/github/github_service_security.py` (modify)

### Procedure

1. Import `SecurityCheckResult`, `SecurityCheckStatus`, and the reason-code constants from
   `shared.security.result_dto` (row `02`).
2. Add `validate_github_security()` (new) after the mixin class (`:197`).
3. Keep every existing guard method unchanged.

### Method

- The function reads only `cfg` fields; it performs no network call and no filesystem write. The
  audit-log check tests the parent directory with `os.access(..., os.W_OK)` rather than writing a
  probe record, so validation stays side-effect free.
- Fixed check order: `server.repo_allowlist`, `server.force_push_policy`,
  `server.pr_review_required`, `server.protected_branches`, `server.path_denylist`,
  `server.max_file_size`, `server.audit_log_writable`, `server.per_page_bounds`.
- Messages name the setting and its state (`allow_force_push=true`), never the repository names or
  the denylist patterns. `allowed_repos` values and `path_denylist` patterns are raw allowlist
  values under `REQ-002`, so only their counts may appear.

### Details

- The mixin is 197 lines; the addition is roughly 55 lines. If the file would exceed the 200-line
  convention, the validator goes into a new sibling module
  `scripts/mcp_servers/github/github_security_validation.py` and this row's target keeps only the
  import-free guard logic. **Needs confirmation** at implementation: the Plan's frozen table names
  only `github_service_security.py`, so creating a sibling module requires a Plan amendment.
- `GitHubConfig` is already the annotated type of `cfg` at `:34`, so no new import of the config
  model is needed for the signature.
- `_write_github_audit_log()`'s silent skip when `audit_log_path` is empty (`:101-102`) is
  preserved; the posture makes the skip visible rather than changing it.

## Compatibility considerations

- Additive change: no signature, return contract, or raised exception type changes.
- `tests/mcp_servers/github/*` that assert `GitHubAuthorizationError` / `GitHubAuditError` behavior
  keep passing.
- Behavior change is limited to startup: a github-mcp with an empty `allowed_repos` now reports a
  failed posture and cannot report `ready=true` (row `06` / row `44`). Its runtime denial behavior
  was already fail-closed (`:49`, `:55-62`).
- No `docs/*.md` change is in scope for this row.

## Security considerations

- `REQ-007` / Plan `INV-05`: github-mcp validates its own policy before Ready; the Agent stops
  reading `github_mcp_server.toml` (row `21` removes `load_github_audit_config()`).
- `REQ-002` / Plan `INV-09`: repository identifiers and denylist patterns are raw allowlist values
  and must not appear in the posture or messages.
- The `WARNING` mapping is a deliberate non-fatal choice; it must not be widened to `FAILED`
  without a Plan amendment, because it changes which configurations can start.

## Rollback considerations

- Revert this commit. The mixin returns to its previous behavior with no further action, and row
  `44` must be reverted together with it because it imports the new function.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Empty repo allowlist | `uv run pytest tests/mcp_servers/github/test_github_security_validation.py` (new test file) | `server.repo_allowlist` `FAILED`, reason `allowlist_empty` |
| Warning-only policy settings | same new test file | `allow_force_push=true` and `require_pr_review=false` produce `WARNING` and leave the posture `validated=true` |
| Inapplicable checks | same new test file | empty `protected_branches`, empty `path_denylist`, `max_file_size_kb=0`, empty `audit_log_path` each produce `NOT_APPLICABLE`, never an omitted check |
| Reversed page bounds | same new test file | `server.per_page_bounds` `FAILED`, reason `config_invalid` |
| Deterministic check set | same new test file | the same eight check ids appear for every configuration |
| Existing GitHub suite | `uv run pytest tests/mcp_servers/github/` | passes |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Completion criteria

- Plan `AC-005` for GitHub: github-mcp validates its own configuration and returns the common
  posture.
- The eight finalized check ids are always present, with `NOT_APPLICABLE` used instead of omission.
- No repository name or denylist pattern appears in any posture field or message.

## Out of scope

- Editing `scripts/mcp_servers/github/github_server.py` (row `44`) or `github_service.py`.
- Changing runtime guard behavior or raised exception types.
- Agent-side validation and classification (rows `17`-`18`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `validate_github_security()` | Completed | 20261016-205509 | 20261016-205509 | check ids are Needs-confirmation Check ids finalized as the eight frozen ids in REQUIRED_CHECK_IDS for github: server.repo_allowlist, server.force_push_policy, server.pr_review_required, server.protected_branches, server.path_denylist, server.max_file_size, server.audit_log_writable, server.per_page_bounds. validate_github_security reads only cfg fields, performs no network call and no filesystem write, and never raises. The audit-log check inspects the parent directory with os.path.isdir and os.access instead of writing a probe record, and also fails when the configured path is itself a directory. allow_force_push=true and require_pr_review=false stay WARNING as the removed audit had them, so a working configuration remains startable. Empty protected_branches, empty path_denylist, non-positive max_file_size_kb, and empty audit_log_path are NOT_APPLICABLE rather than omitted. Messages name the setting and its state and report only counts for allowed_repos and path_denylist. The module docstring separator was added so the advisory docstring checker reports no finding in the changed file. |
| 2 | Decide single-file vs sibling module (Details) | Completed | 20261016-205509 | 20261016-205509 | sibling module needs a Plan amendment User decision: keep the validator in github_service_security.py. The file is 394 lines, above the 200-line convention in Details, accepted as a deviation as with rows 04 and 08; the split trigger in skills/DESIGN.md is 400 lines. No sibling module was created and the Plan's frozen table is unchanged. |
| 3 | Add `tests/mcp_servers/github/test_github_security_validation.py` | Completed | 20261016-205509 | 20261016-205509 | tests/mcp_servers/github/test_github_security_validation.py: 23 tests, all pass, and tests/mcp_servers/github reports 288 passed. Covers the empty allowlist, both WARNING settings, warnings alone leaving no FAILED check, the four not_applicable rules, audit log ok, missing parent, parent that is a file, path that is a directory, and a failure message that does not name the path, per-page bounds in three states, the frozen id set and fixed order, identical check sets across four configurations, and messages that never name a repository slug or a denylist pattern. No test writes outside tmp_path and none touches the network. |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261016-210018 | 20261016-210018 | Full validation sequence: ruff clean, mypy clean on 421 source files, lint-imports 6 kept 0 broken, bandit reports no finding in github_service_security.py (the github package keeps 1 pre-existing Low finding elsewhere and no High), check_mock_patch_targets no findings, check_docstrings reports no finding in the changed file after the module docstring separator was added, no bare except. Full suite: 8675 passed, 19 skipped, 9 failed, and all 9 are the pre-existing tests/agent/test_startup_rollback.py schema-version failures. Coverage and diff-cover are deferred to the end of the procedure batch. |

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
- **Requirement ID**: `REQ-007` (GitHub self-validation)
- **Source issue**: `issues/done/20261015-102802_audit001_move-security-validation-to-each-mcp-server.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261015-112526_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-073146
- **Related target files**: `scripts/mcp_servers/github/github_service_security.py`