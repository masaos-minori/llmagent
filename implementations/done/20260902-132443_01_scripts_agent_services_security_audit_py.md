## Goal

Remove the `if production_mode:` conditional gate around the `shell_sandbox_backend == "none"` `RuntimeError` in `audit_security_defaults()`, so it raises unconditionally regardless of environment. Update the raised message to drop the "in production mode" framing. (REQ-001; AC-1)

## Scope

- Modify exactly one conditional branch inside `audit_security_defaults()` in `scripts/agent/services/security_audit.py`
- Collapse the `if production_mode:` / `else` pattern for the `"none"` case into a single unconditional `raise RuntimeError`
- Update the error message text to remove the "Production mode requires shell sandbox" framing

## Assumptions

- `production_mode` continues to be used, unchanged, for the other checks inside `audit_security_defaults()` (`auth_token` HTTP enforcement, `cicd`/`git` allowlist warnings) — scoped strictly to the shell-sandbox-backend check
- The `firejail` binary-missing case already raises unconditionally (same function, line 134-139), confirming the pattern this change follows
- No other call site passes `production_mode=False` expecting the `"none"` case to warn rather than raise

## Design decisions

- Minimal edit: collapse the existing `if production_mode:` / `else` block into a single unconditional raise, matching the pattern already present in the same function for the `firejail`-binary-missing case (line 134-139)
- Message text updated to remove the "Production mode requires shell sandbox" framing since the condition is no longer production-mode-specific

## Alternatives considered

- Adding a separate parameter to `audit_security_defaults()` controlling the sandbox enforcement level — rejected because it changes the public contract without benefit; the goal is to eliminate the environment-dependent behavior, not make it configurable
- Keeping the conditional but changing its logic — rejected because ADR-004 Decision Group 1 prohibits environment names from changing Fail-Fast conditions for safety/integrity failures

## Compatibility considerations

- Any environment currently loading `config/shell_mcp_server.toml` with `shell_sandbox_backend = "none"` will newly fail startup after this change — this is the intended effect, gated by REQ-004 sign-off
- The function signature and return type are unchanged; only which branch is taken differs

## Security considerations

- This change strengthens security posture by removing an environment-dependent relaxation of a safety control — aligning with ADR-004 Decision Group 2 item 6 (safety/integrity failures must not become warning-only continuation)
- The error message text change (dropping "Production mode") is a documentation detail, not a security-relevant change

## Rollback considerations

- To roll back: restore the original `if production_mode:` / `else` block around lines 117-122 of `security_audit.py`
- Before rollback: confirm that the environment's `shell_sandbox_backend` configuration is acceptable under the restored conditional behavior

## Validation plan

### Unit test validation
- Run `uv run pytest tests/agent/test_repl_health.py -v` — both `test_shell_sandbox_none_warns` and `test_shell_sandbox_none_raises_in_production` must pass with updated assertions proving `RuntimeError` is raised for `shell_sandbox_backend == "none"` under both `production_mode=True` and `production_mode=False`

### Static analysis
- `uv run ruff format scripts/agent/services/security_audit.py && uv run ruff check scripts/agent/services/security_audit.py && uv run mypy scripts/agent/services/security_audit.py` — clean
- `PYTHONPATH=scripts uv run lint-imports` — clean
- `uv run bandit -r scripts/agent/services/security_audit.py -c pyproject.toml` — clean (baseline already confirmed clean)

### Complexity regression check
- `uv run radon cc scripts/agent/services/security_audit.py -s` — `audit_security_defaults` grade does not worsen versus recorded baseline (`F(45)`); expected to improve slightly since one branch is removed

### Full-suite regression
- `uv run pytest` — no new failures vs. pre-change baseline

### Coverage
- `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` — >= 90% diff coverage on changed lines

## Completion criteria

- [ ] `rg production_mode scripts/agent/services/security_audit.py` shows the shell-sandbox-none raise is no longer inside a `production_mode` conditional
- [ ] Both `test_shell_sandbox_none_*` tests assert `RuntimeError` regardless of `production_mode` value
- [ ] Error message text no longer contains "Production mode requires shell sandbox" or equivalent production-only framing
- [ ] All static analysis tools report clean
- [ ] Full test suite passes with no regressions

## Out of scope

- Updating `docs/04_mcp_04_02_file-write-file-delete-shell.md` (handled by REQ-003, separate row)
- Updating `tests/agent/test_repl_health.py` (handled by REQ-002, separate row)
- Changing `config/shell_mcp_server.toml`'s `shell_sandbox_backend` value (operational decision gated by REQ-004 sign-off)
- Auditing other `production_mode`-conditioned checks in `audit_security_defaults()` (UNK-01, out of scope)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify pre-implementation validation baseline matches Plan's recorded baseline | Done | 2026-09-02 | 2026-09-02 | Baseline confirmed |
| 2 | Obtain REQ-004 sign-off: confirm operations/architecture owner review of current `shell_sandbox_backend` config before deployment | Done | 2026-09-02 | 2026-09-02 | Sign-off obtained |
| 3 | Remove the `if production_mode:` gate around the `shell_sandbox_backend == "none"` `RuntimeError`; update message text | Done | 2026-09-02 | 2026-09-02 | Replaced conditional with unconditional raise; updated error message |
| 4 | Run full standard validation sequence per `rules/toolchain.md` | Done | 2026-09-02 | 2026-09-02 | All 24 TestAuditSecurityDefaults tests pass |

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
- **Requirement ID**: REQ-001; AC-1
- **Source issue**: issues/20260831-192510_adr004_07_shell_mcp_sandbox_production_only_enforcement.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260901-104253_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-132443
- **Related target files**: scripts/agent/services/security_audit.py
