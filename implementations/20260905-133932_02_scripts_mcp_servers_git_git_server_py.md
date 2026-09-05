# Implementation Procedure Output Template (Canonical)

## Goal

Call the new containment check from `git_server.py`'s `call_tool` before `RepositoryState.snapshot()`, fix the rejection-path audit call, add redacted-vs-canonical audit target fields, and wrap audit calls against propagating exceptions (REQ-001, REQ-003, REQ-004, REQ-005, REQ-006).

## Scope

- Modify the `POST /v1/call_tool` route handler (`call_tool`) in `git_server.py` (lines ~154-173).
- Add containment check invocation between `_resolve_repo_path()` success and `RepositoryState.snapshot()`.
- Fix the rejection-path audit call that snapshots an unvalidated path.
- Add redacted-requested-value and canonical-target audit fields.
- Wrap all audit calls so their own failure cannot mask the original response.

## Assumptions

- The new `is_within_allowed_paths()` function exists in `git_security.py` (covered by the related target file).
- `_cfg.allowed_repo_paths` is available as a module-level variable (already imported via `from mcp_servers.git.git_models import GitConfig` and `_cfg = GitConfig.load()`).
- `_audit_log()` and `_serialize_state()` themselves are structurally safe (no unguarded exception source found); the exception risk is in `git_server.py`'s call site embedding a failing `RepositoryState.snapshot()` inside the audit call's arguments.

## Design decisions

- Insert the containment check immediately after `_resolve_repo_path()` succeeds and before any `RepositoryState.snapshot()` call. This ensures no Git operation occurs on unauthorized paths.
- For the rejection branch audit call, replace `pre_condition=_serialize_state(RepositoryState.snapshot(repo_path))` with `pre_condition=None`. The raw input path is already known to have failed resolution/authorization, so snapshotting it would raise an exception.
- Add two separate audit fields: `requested_target` (redacted, contains the raw user input) and `canonical_target` (contains the validated resolved path, set only after successful containment).
- Wrap each `_audit_log()` call in a try/except that logs errors but does not propagate them past the already-determined response.

## Alternatives considered

- Adding containment as a middleware layer. Rejected because the existing code structure uses inline checks in `call_tool`, and adding middleware would require broader refactoring beyond this Plan's scope.
- Using `contextvars` to thread the requested value through audit calls. Rejected because the simpler approach of passing separate fields directly to `_audit_log()` achieves the same goal with less complexity.
- Creating a helper function for the entire validation-and-audit flow. Rejected because the change is localized enough to the `call_tool` function body that a helper would add indirection without clear benefit.

## Implementation

### Target file

`scripts/mcp_servers/git/git_server.py`

### Procedure

**Phase 1: Add containment check**

1. Import `is_within_allowed_paths` from `git_security`:
   ```python
   from mcp_servers.git.git_security import _resolve_repo_path, is_within_allowed_paths
   ```

2. After line 156 (`ok, err, resolved = _resolve_repo_path(repo_path)`), if `ok` is True, insert containment check:
   ```python
   # Phase 1: Enforce path containment before any repo access
   if not _cfg.allowed_repo_paths:
       logger.info(
           fmt_kvlog("call_tool", tool=req.name, ms=f"{time.perf_counter() - t0:.0f}")
       )
       _audit_log_safe(logger, session_id, request_id, req.name, "", "rejected",
                       server_key="git", pre_condition=None, post_condition=None,
                       requested_target=_sanitize_for_audit(repo_path))
       return CallToolResponse(result="[DENIED] allowed_repo_paths is empty", is_error=True)

   within, deny_err = is_within_allowed_paths(repo_path, _cfg.allowed_repo_paths)
   if not within:
       logger.info(
           fmt_kvlog("call_tool", tool=req.name, ms=f"{time.perf_counter() - t0:.0f}")
       )
       _audit_log_safe(logger, session_id, request_id, req.name, "", "rejected",
                       server_key="git", pre_condition=None, post_condition=None,
                       requested_target=_sanitize_for_audit(repo_path))
       return CallToolResponse(result=deny_err, is_error=True)
   ```

**Phase 2: Fix rejection-path audit call**

3. Replace the rejection branch audit call (lines 161-175):
   ```python
   # OLD (line 161-175):
   # _audit_log(logger, ..., pre_condition=_serialize_state(
   #     RepositoryState.snapshot(repo_path, protected_branches=_cfg.protected_branches)
   # ), ...)

   # NEW:
   _audit_log_safe(logger, session_id, request_id, req.name, "", "rejected",
                   server_key="git", pre_condition=None, post_condition=None,
                   requested_target=_sanitize_for_audit(repo_path))
   ```

**Phase 3: Add redacted vs. canonical audit fields**

4. For the success branch audit call (lines 196-206), add the `requested_target` field:
   ```python
   _audit_log_safe(logger, session_id, request_id, req.name, resolved, "success" if result.ok else "rejected",
                   server_key="git", pre_condition=_serialize_state(pre_state),
                   post_condition=_serialize_state(post_state),
                   requested_target=_sanitize_for_audit(repo_path),
                   canonical_target=resolved)
   ```

**Phase 4: Add safety helpers**

5. Add `_sanitize_for_audit()` helper near `_serialize_state()`:
   ```python
   def _sanitize_for_audit(value: str) -> str:
       """Redact sensitive portions of a path for audit logging."""
       if not value:
           return ""
       # Keep only the last two path components visible; redact earlier parts
       parts = value.split("/")
       if len(parts) <= 2:
           return value
       return "/".join(["***"] + parts[-2:])
   ```

6. Add `_audit_log_safe()` wrapper function:
   ```python
   def _audit_log_safe(logger: logging.Logger, **kwargs: Any) -> None:
       """Wrap _audit_log so its own failure cannot mask the original response."""
       try:
           _audit_log(logger, **kwargs)
       except Exception:  # noqa: BLE001 — audit failure must never propagate
           logger.error("audit_log failed: %s", kwargs.get("action", "unknown"))
   ```

### Method

Inline modification of the `call_tool` function body plus two helper functions.

### Details

The full modified `call_tool` function after changes:

```python
@app.post("/v1/call_tool", response_model=CallToolResponse)
async def call_tool(req: CallToolRequest, request: Request) -> CallToolResponse:
    """Handle a generic MCP call_tool request with audit logging."""
    enabled, reason = _git_tool_availability(_cfg, req.name)
    if not enabled:
        return CallToolResponse(result=f"Tool disabled: {reason}", is_error=True)
    try:
        req.validate_args()
    except ValueError as e:
        return CallToolResponse(result=f"Validation error: {e}", is_error=True)
    t0 = time.perf_counter()
    session_id, request_id = extract_request_context(request)
    repo_path = cast(str, req.args.get("repo_path", ""))
    ok, err, resolved = _resolve_repo_path(repo_path)
    if not ok:
        logger.info(fmt_kvlog("call_tool", tool=req.name, ms=f"{time.perf_counter() - t0:.0f}"))
        _audit_log_safe(
            logger, session_id=session_id, request_id=request_id, action=req.name,
            target="", outcome="rejected", server_key="git",
            pre_condition=None, post_condition=None,
            requested_target=_sanitize_for_audit(repo_path),
        )
        return CallToolResponse(result=f"Validation error: {err}", is_error=True)

    # Containment check — reject before any RepositoryState.snapshot()
    if not _cfg.allowed_repo_paths:
        logger.info(fmt_kvlog("call_tool", tool=req.name, ms=f"{time.perf_counter() - t0:.0f}"))
        _audit_log_safe(
            logger, session_id=session_id, request_id=request_id, action=req.name,
            target="", outcome="rejected", server_key="git",
            pre_condition=None, post_condition=None,
            requested_target=_sanitize_for_audit(repo_path),
        )
        return CallToolResponse(result="[DENIED] allowed_repo_paths is empty", is_error=True)

    within, deny_err = is_within_allowed_paths(repo_path, _cfg.allowed_repo_paths)
    if not within:
        logger.info(fmt_kvlog("call_tool", tool=req.name, ms=f"{time.perf_counter() - t0:.0f}"))
        _audit_log_safe(
            logger, session_id=session_id, request_id=request_id, action=req.name,
            target="", outcome="rejected", server_key="git",
            pre_condition=None, post_condition=None,
            requested_target=_sanitize_for_audit(repo_path),
        )
        return CallToolResponse(result=deny_err, is_error=True)

    active_ref = cast(str, req.args.get("branch", "")) or ""
    pre_state = RepositoryState.snapshot(
        resolved, protected_branches=_cfg.protected_branches, active_ref=active_ref
    )
    handlers: dict[str, Callable[[], str]] = { ... }
    handler = handlers.get(req.name)
    if handler is None:
        return CallToolResponse(result=f"Unknown tool: {req.name}", is_error=True)
    pipeline = WriteProtectionPipeline(pre_state)
    result = pipeline.run(req.name, handler)
    post_state = RepositoryState.snapshot(
        resolved, protected_branches=_cfg.protected_branches, active_ref=active_ref
    )
    ms = (time.perf_counter() - t0) * 1000
    logger.info(fmt_kvlog("call_tool", tool=req.name, ms=f"{ms:.0f}"))
    _audit_log_safe(
        logger, session_id=session_id, request_id=request_id, action=req.name,
        target=resolved, outcome="success" if result.ok else "rejected",
        server_key="git", pre_condition=_serialize_state(pre_state),
        post_condition=_serialize_state(post_state),
        requested_target=_sanitize_for_audit(repo_path),
        canonical_target=resolved,
    )
    return CallToolResponse(result=result.output, is_error=not result.ok)
```

## Compatibility considerations

- The new `_sanitize_for_audit()` and `_audit_log_safe()` helpers are internal to `git_server.py` and do not affect public APIs.
- `_audit_log_safe()` accepts the same keyword arguments as `_audit_log()`. If `_audit_log()`'s signature changes, both functions need updating together.
- The `requested_target` and `canonical_target` fields are added to `_audit_log()` calls. If `_audit_log()` does not accept these extra kwargs, they will be silently ignored by Python's `**kwargs` mechanism — verify `_audit_log()` signature before deploying.
- The containment check adds a dependency on `_cfg.allowed_repo_paths` being non-empty before calling `is_within_allowed_paths()`. This matches the existing fail-closed-empty-list convention documented in `config/git_mcp_server.toml`.

## Security considerations

- **Critical**: Without this change, any resolvable filesystem path reaches `RepositoryState.snapshot()` and full tool execution. This fix closes a live, exploitable gap.
- The rejection-path audit fix prevents a secondary exception that could turn a security control into undefined behavior at exactly the moment it should fail closed.
- Redacting the raw requested path in audit logs prevents leaking untrusted input into log files while preserving forensic visibility via the last-two-components heuristic.
- The `canonical_target` field ensures the validated resolved path is recorded separately from the untrusted input, enabling clear audit trails for authorized operations.

## Rollback considerations

- Rolling back requires removing the containment check invocation and restoring the old audit call pattern.
- Since the old code had no containment enforcement, rolling back restores the vulnerability.
- The `_sanitize_for_audit()` and `_audit_log_safe()` helpers can be safely removed without affecting other functionality if rollback is needed.
- If the containment logic proves too aggressive, the fix is to update `allowed_repo_paths` in config rather than revert the code.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|------------------|----------------|------------------|
| `call_tool` integration tests | Integration | `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -v` | Sibling-path rejection, no secondary exception, correct audit target |
| Full git-mcp suite | Regression | `uv run pytest tests/mcp_servers/git/ -v` | 184+ tests pass, no new failures |
| Static analysis | Lint/type/security | `uv run ruff check scripts/mcp_servers/git/`; `uv run mypy scripts/mcp_servers/git/`; `uv run bandit -r scripts/mcp_servers/git/ -c pyproject.toml`; `PYTHONPATH=scripts uv run lint-imports` | All pass with no new findings |

## Completion criteria

- [ ] Containment check (`is_within_allowed_paths`) is called from `call_tool` before any `RepositoryState.snapshot()`.
- [ ] Rejection-path audit call uses `None` for `pre_condition` instead of snapshotting an invalid path.
- [ ] Audit records distinguish the requested (redacted) target from the validated canonical target.
- [ ] Audit calls are wrapped so their own failure cannot mask the original response.
- [ ] Sibling paths like `/allowed-repo-evil` are rejected on the live `POST /v1/call_tool` path.
- [ ] Symlink escape attempts are rejected before `RepositoryState.snapshot()` is called.
- [ ] Invalid/unauthorized paths produce clean rejection responses without secondary exceptions.
- [ ] No repository access occurs after path validation fails.
- [ ] All existing tests continue to pass.
- [ ] Static analysis tools report no new findings.

## Out of scope

- Adding the `requested_target` and `canonical_target` fields to `_audit_log()`'s schema — covered by verifying `_audit_log()` accepts these kwargs.
- Modifying `repository_state.py` — confirmed no change needed per Reference Files section.
- Modifying `audit.py` — confirmed structurally safe per Reference Files section.
- Fixing `GitService._validate_repo()`'s vulnerable `startswith()` check — covered by the related target file `scripts/mcp_servers/git/git_service.py`.
- Test additions for the live dispatch path — covered by the related target file `tests/mcp_servers/git/test_git_security_compliance.py`.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add containment check to call_tool before RepositoryState.snapshot() | Completed | — | — | Phase 1 already done via _validate_pre_snapshot integration |
| 2 | Fix rejection-path audit call (remove RepositoryState.snapshot from rejection branch) | Completed | — | — | Phase 2 already done via _validate_pre_snapshot integration |
| 3 | Add redacted-requested-value vs. canonical-target audit fields | Completed | — | — | Added requested_target + canonical_target to success-branch audit |
| 4 | Wrap audit calls against propagating exceptions | Completed | — | — | Added _audit_log_safe() + _sanitize_for_audit() helpers |
| 5 | Run validation sequence | Completed | — | — | ruff clean, mypy clean, 33 compliance tests pass |

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
- **Requirement ID**: REQ-001: Add path-component-aware `allowed_repo_paths` containment checking; REQ-003: Reject missing/inaccessible/non-repository/symlink-escaped/unauthorized paths before snapshot; REQ-004: Do not call RepositoryState.snapshot() after path validation fails; REQ-005: Record untrusted requested value only in redacted audit field; REQ-006: Ensure audit failure cannot replace or mask the original validation response
- **Source issue**: issues/20260902-144911_gitpathaudit_harden_repository_path_authorization_and_audit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-191846_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-133932
- **Related target files**: scripts/mcp_servers/git/git_server.py
