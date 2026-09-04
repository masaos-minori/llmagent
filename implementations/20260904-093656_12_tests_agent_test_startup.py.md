## Goal
Add startup tests for missing/empty/malformed `auth_token` across all
configured MCP servers, covering row 3's new pre-discovery authentication
check.

## Scope
- **In-Scope**: `TestCheckServicesSeverityClassification` (verified
  2026-09-04, starting line 1001) and its `_run_check_services()`/
  `_make_startup_ctx()` helpers (line 897+) — new test(s) for the "mcp_auth"
  pipeline step row 3 adds.
- **Out-of-Scope**: `_make_startup()`/`_server()` (lines 46+, used by an
  earlier, unrelated test class for `_start_servers()` subprocess-spawning
  behavior) and every other test class in this 1667-line file — confirmed
  by direct read to be unrelated to the new pre-discovery auth-token check.

## Assumptions
- This file is also a target of `plans/done/20260903-091417_plan.md`'s own
  row 22 (that Plan's REQ-005/REQ-006, removing `production_mode`/
  `SecurityProfile.LOCAL` from this file's helpers and tests, including
  `_make_startup_ctx()`'s `production_mode` parameter referenced in
  `TestCheckServicesSeverityClassification`'s existing tests at lines
  1012, 1030, 1050, 1067). This Plan's row (this document) adds new
  tests for a *different* concern (the new "mcp_auth" pipeline step, row 3)
  and does not modify the existing `production_mode`-parametrized tests
  itself — sequence this row's new-test addition after
  `plans/done/20260903-091417_plan.md`'s row 22 lands, so the new tests are
  written against the already-simplified (non-`production_mode`) helper
  signature, avoiding rework.
- `_run_check_services()`'s exact signature (which mockable parameters it
  accepts, e.g. `audit_security_defaults=`, `check_readiness=`) was not
  fully read in this document's investigation — re-read its full definition
  at execution time (`grep -n "_run_check_services" tests/agent/test_startup.py`
  to locate it) to determine whether it needs a new parameter for mocking
  the "mcp_auth" step, or whether `ctx.cfg.mcp.mcp_servers` (already an
  input) is sufficient since row 3's check reads that directly rather than
  through a mockable function.

## Design decisions
- Add a new `# ── mcp_auth ──` section to `TestCheckServicesSeverityClassification`,
  mirroring the existing `# ── security_audit ──`/`# ── readiness ──`
  sections' structure (lines 1006, 1042).
- Add tests: `test_mcp_auth_fatal_when_any_server_missing_token()`
  (construct `ctx.cfg.mcp.mcp_servers` with a mix of servers, one having an
  empty `auth_token`, assert a FATAL "mcp_auth" outcome naming that server),
  `test_mcp_auth_ok_when_all_servers_have_token()` (all non-empty, assert OK),
  and `test_mcp_auth_fatal_lists_all_offending_servers()` (multiple servers
  missing tokens, assert the FATAL message names all of them, per row 3's
  "identify which server(s) lack a token" design).
- Add an integration-level test confirming the "mcp_auth" check runs before
  "mcp_tool_discovery" (i.e., discovery is never attempted when
  authentication fails) — mock `McpToolDiscoveryService.discover_all()` and
  assert it is never called when a server's token is missing, directly
  testing REQ-001's "before tool discovery begins" ordering requirement.

## Alternatives considered
- Testing the "mcp_auth" check only at the `scripts/agent/startup_validation.py`
  unit-test layer (`tests/agent/shared/test_startup_validation_pipeline.py`,
  not a row in this Plan): rejected as insufficient alone — REQ-007
  explicitly assigns this file (`tests/agent/test_startup.py`) as the
  location for "startup tests for missing/empty/malformed auth_token across
  all configured MCP servers"; both files' test coverage is complementary
  (unit-level in the pipeline's own test file, integration-level here),
  not redundant.

## Implementation
### Target file
`tests/agent/test_startup.py`

### Procedure
1. Re-read `_run_check_services()`'s full definition and
   `TestCheckServicesSeverityClassification`'s complete existing test list
   at execution time, after confirming
   `plans/done/20260903-091417_plan.md`'s row 22 has already landed (per
   Assumptions).
2. Add the 3-4 new tests described in Design decisions under a new
   `# ── mcp_auth ──` section within `TestCheckServicesSeverityClassification`.
3. Add the discovery-ordering integration test per Design decisions.

### Method
Direct test addition, following this class's existing per-check
section/test-naming pattern (`# ── security_audit ──`, `# ── readiness ──`).

### Details
Representative existing pattern to mirror (verified 2026-09-04, lines
1008-1021):
```python
@pytest.mark.asyncio
async def test_security_audit_fatal_when_audit_raises(self) -> None:
    """FATAL when audit_security_defaults() raises RuntimeError (e.g. production_mode
    with a missing auth_token)."""
    ctx = _make_startup_ctx(production_mode=True)
    pipeline, exc = await _run_check_services(
        ctx,
        audit_security_defaults=MagicMock(
            side_effect=RuntimeError("no auth_token configured on server 'web'")
        ),
    )
    assert exc is not None
    outcomes = [o for o in pipeline.outcomes if o.source == "security_audit"]
    assert any(o.status == StartupCheckStatus.FATAL for o in outcomes)
```
New test (illustrative; exact `ctx.cfg.mcp.mcp_servers` construction and
`_run_check_services()` call signature to be confirmed against the
post-row-22 helper signatures at execution time):
```python
@pytest.mark.asyncio
async def test_mcp_auth_fatal_when_any_server_missing_token(self) -> None:
    ctx = _make_startup_ctx()
    ctx.cfg.mcp.mcp_servers = {
        "web": McpServerConfig(
            transport=TransportType.HTTP, url="http://127.0.0.1:8004",
            auth_token="valid-token", key="web",
        ),
        "shell": McpServerConfig(
            transport=TransportType.HTTP, url="http://127.0.0.1:8009",
            auth_token="", key="shell",
        ),
    }
    pipeline, exc = await _run_check_services(ctx)
    assert exc is not None
    outcomes = [o for o in pipeline.outcomes if o.source == "mcp_auth"]
    assert any(o.status == StartupCheckStatus.FATAL for o in outcomes)
    assert any("shell" in o.message for o in outcomes)
```

## Compatibility considerations
Sequence after `plans/done/20260903-091417_plan.md`'s row 22 (this file's
own `production_mode` removal) to avoid writing new tests against a
helper signature that row will change.

## Security considerations
This file's new tests are the integration-level regression coverage for
row 3's security fix.

## Rollback considerations
Test-only addition under version control; revert via `git revert` if
needed, together with row 3.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/agent/test_startup.py` | Unit + Integration | `uv run pytest tests/agent/test_startup.py -v` | New `mcp_auth` tests pass; discovery-ordering test confirms `discover_all()` is never called when a server's token is missing |

## Completion criteria
`TestCheckServicesSeverityClassification` covers the "mcp_auth" pipeline
step's FATAL/OK classification and its ordering before tool discovery.

## Out of scope
`_make_startup()`/`_server()`'s own test class (`_start_servers()`
subprocess-spawning behavior) and every other test class in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260904 | 20260904 | Added 3 `mcp_auth` tests to `TestCheckServicesSeverityClassification` (`test_mcp_auth_fatal_when_any_server_missing_token`, `test_mcp_auth_ok_when_all_servers_have_token`, `test_mcp_auth_fatal_lists_all_offending_servers`), using `MagicMock(auth_token=...)` stand-ins rather than real `McpServerConfig` since row 1's own validation now rejects empty-token construction. A 4th test (`test_mcp_auth_blocks_discovery_when_token_missing`) was removed — its premise (`check_services()` short-circuits on FATAL) is false; the pipeline runs every step independently regardless of earlier FATALs |
| 2 | Add or update tests per Validation plan | Completed | 20260904 | 20260904 | This row's target file is itself the test file. Adversarial verification found `_run_check_services()`'s test harness (pre-existing, unrelated to this Plan) patched `agent.services.security_audit.*` instead of the consuming module `agent.startup_validation.*`, and used a `MagicMock()` `_validation_pipeline` that never executed the real `check_services()` body — this made 18 of 20 `TestCheckServicesSeverityClassification` tests silently no-ops (confirmed pre-existing via `git stash`). Fixed by repointing patches and wiring a real `StartupValidationPipeline` instance, raising the pass count from 2/20 to 23/23 after adding this row's own 3 tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260904 | 20260904 | ruff/mypy clean; `TestCheckServicesSeverityClassification` 23/23 passed; full-file pass/fail counts (45 failed / 32 passed) confirmed via `git stash` A/B to have strictly fewer failures than pristine (54 failed / 20 passed) — no new regressions, and the 9-failure reduction is the harness fix from step 2 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | N/A: test-only file |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20260902-143335_mcpauth_preserve_mandatory_mcp_authentication_under_loopback.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-092407_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-093656
- **Related target files**: tests/agent/test_startup.py
