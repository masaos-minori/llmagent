# Implementation: cicd-mcp workflow_allowlist fail-closed standardization

## Goal

Standardize cicd-mcp `workflow_allowlist` as strictly fail-closed across implementation, documentation, and tests, fixing a docstring fail-open remark and adding missing dry-run denial tests.

## Scope

- **In-Scope**:
  - Fix fail-open wording in `scripts/mcp/cicd/server.py` docstring (line 9)
  - Add missing tests: `workflow_allowlist=[]` + `dry_run=True` denied; `workflow_allowlist` disallowed workflow + `dry_run=True` denied
  - Clarify in `docs/04_mcp_05_security_and_safety_model.md` that allowlist checks run before dry-run bypass
  - Fix production startup behavior doc: change "raises RuntimeError" to "emits a startup warning"
- **Out-of-Scope**:
  - Non-GitHub CI backends
  - `repo_allowlist` semantics changes
  - Any changes to the fail-closed runtime logic (already correct)

## Assumptions

- The runtime implementation in `service_guards.py` and `service_business.py` is already correctly fail-closed; only docstring and tests need correction
- Production startup behavior: warning-only is intentional (operational lockout avoidance); document the actual behavior
- `04_mcp_04_server_catalog.md` line 273 says "raises RuntimeError" but `repl_health.py` only emits a warning — fix the doc to match reality

## Implementation

### Target file: `scripts/mcp/cicd/server.py` (line 9)

#### Procedure

Fix fail-open wording in module docstring.

#### Method

Direct file edit — change line 9.

#### Details

**Replace line 9:**
```markdown
- workflow_allowlist: restrict triggerable workflows (empty = deny all (fail-closed))
```

### Target file: `docs/04_mcp_05_security_and_safety_model.md`

#### Procedure

Add note in Dry-Run Support section clarifying allowlist-before-dry_run ordering for cicd-mcp.

#### Method

Direct file edit — add paragraph after the cicd-mcp row in the dry_run table.

#### Details

**Add after line 287 (after `cicd-mcp | trigger_workflow`):**
```markdown
**cicd-mcp note:** Allowlist checks (`_assert_allowed_repo`, `_assert_allowed_workflow`) execute before the `dry_run` bypass in `handle_trigger_workflow`. A denied request is always rejected even with `dry_run=True`.
```

### Target file: `docs/04_mcp_04_server_catalog.md` (line 273)

#### Procedure

Fix "raises RuntimeError" to match actual warning-only behavior in repl_health.py.

#### Method

Direct file edit — change the production mode statement.

#### Details

**Replace line 273:**
```markdown
- `workflow_allowlist`: fail-closed (empty = deny all); in production mode (`security_profile = "production"`), empty list emits a startup warning (not RuntimeError)
```

### Target file: `tests/test_cicd_mcp_service.py`

#### Procedure

Add 2 new test cases in class `TestTriggerWorkflowDryRun`.

#### Method

Direct file edit — add new test methods after existing tests.

#### Details

**Add after line 553 (after `test_dry_run_denied_by_repo_allowlist`):**
```python
    @pytest.mark.asyncio
    async def test_dry_run_denied_by_empty_workflow_allowlist(self) -> None:
        """Empty workflow_allowlist denies dry_run (fail-closed)."""
        svc = _make_service(repo_allowlist=["owner/repo"], workflow_allowlist=[])
        with pytest.raises(CicdAuthorizationError):
            await svc.handle_trigger_workflow(
                {"repo": "owner/repo", "workflow": "ci.yml", "dry_run": True}
            )

    @pytest.mark.asyncio
    async def test_dry_run_denied_by_disallowed_workflow(self) -> None:
        """Disallowed workflow in allowlist denies dry_run."""
        svc = _make_service(repo_allowlist=["owner/repo"], workflow_allowlist=["ci.yml"])
        with pytest.raises(CicdAuthorizationError):
            await svc.handle_trigger_workflow(
                {"repo": "owner/repo", "workflow": "deploy.yml", "dry_run": True}
            )
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/mcp/cicd/server.py` | Manual review + consistency script | `uv run python scripts/check_mcp_docs_consistency.py docs/` | No fail-open wording detected |
| `tests/test_cicd_mcp_service.py` | pytest unit tests | `uv run pytest tests/test_cicd_mcp_service.py -v` | All tests pass including new dry_run denial cases |
| `docs/04_mcp_05_security_and_safety_model.md` | Manual review | Read + grep | Allowlist-before-dry_run ordering documented |
| `docs/04_mcp_04_server_catalog.md` | Manual review | Read + grep | "raises RuntimeError" corrected to match actual behavior |
| End-to-end policy consistency | grep across all affected files | `rg "workflow_allowlist.*fail.open\|fail.open.*workflow_allowlist"` | Zero matches |
