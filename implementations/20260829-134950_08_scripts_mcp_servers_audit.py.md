# Implementation Procedure: Modify audit.py

## Goal

Add pre/post condition snapshot fields to `AuditRecord` TypedDict; update `_audit_log()` function to capture both snapshots; ensure audit records include correct repository identity.

## Scope

- Add pre/post condition snapshot fields to `AuditRecord` TypedDict
- Update `_audit_log()` function to capture both snapshots
- Ensure audit records include correct repository identity

## Assumptions

1. `RepositoryState` module exists and is importable
2. Existing `AuditRecord` TypedDict can be extended without breaking other callers
3. `_audit_log()` function can be updated without breaking audit trail integrity

## Design decisions

- `AuditRecord` gains `pre_condition` and `post_condition` fields for snapshot comparison
- `_audit_log()` captures both pre-condition (before operation) and post-condition (after operation) snapshots
- Audit records include correct repository identity via `RepositoryState.path`

## Alternatives considered

- Keep `AuditRecord` unchanged: Would require importing `RepositoryState` elsewhere; cleaner to centralize
- Create separate `AuditRecordV2` TypedDict: Would duplicate code; updating existing TypedDict is simpler
- Pass both `RepositoryState` and `git.Repo`: Would defeat the purpose of eliminating duplicate instantiation

## Implementation

### Target file

`scripts/mcp_servers/audit.py`

### Procedure

1. Import `RepositoryState` from `repository_state` module
2. Add `pre_condition` and `post_condition` fields to `AuditRecord` TypedDict
3. Update `_audit_log()` function to capture both snapshots
4. Ensure audit records include correct repository identity

### Method

#### Step 1: Add imports

```python
from mcp_servers.git.repository_state import RepositoryState
```

#### Step 2: Add `pre_condition` and `post_condition` fields to `AuditRecord` TypedDict

Current definition (line ~10):
```python
@total_ordering
class AuditRecord(TypedDict):
    timestamp: str
    tool: str
    repo_path: str
    user: str
    action: str
    status: str
    error: str | None
```

Update to:
```python
@total_ordering
class AuditRecord(TypedDict):
    timestamp: str
    tool: str
    repo_path: str
    user: str
    action: str
    status: str
    error: str | None
    pre_condition: dict[str, Any] | None
    post_condition: dict[str, Any] | None
```

#### Step 3: Update `_audit_log()` function

Current body (lines 40-80):
```python
def _audit_log(record: AuditRecord) -> None:
    """Append an audit record to the log file."""
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "audit.log"
    with open(log_file, "a") as f:
        f.write(json.dumps(record))
        f.write("\n")
```

Replace with:
```python
def _audit_log(record: AuditRecord) -> None:
    """Append an audit record to the log file."""
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "audit.log"
    with open(log_file, "a") as f:
        # Serialize pre/post conditions if present
        if record.get("pre_condition") is not None:
            record["pre_condition"] = {
                k: v for k, v in record["pre_condition"].items()
                if isinstance(v, (str, int, float, bool, type(None)))
            }
        if record.get("post_condition") is not None:
            record["post_condition"] = {
                k: v for k, v in record["post_condition"].items()
                if isinstance(v, (str, int, float, bool, type(None)))
            }
        f.write(json.dumps(record))
        f.write("\n")
```

#### Step 4: Ensure audit records include correct repository identity

In the audit record creation function (around line 30), add:
```python
def _build_audit_record(
    tool: str,
    repo_path: str,
    user: str,
    action: str,
    status: str,
    error: str | None = None,
    pre_condition: RepositoryState | None = None,
    post_condition: RepositoryState | None = None,
) -> AuditRecord:
    """Build an audit record with pre/post condition snapshots."""
    return AuditRecord(
        timestamp=datetime.now().isoformat(),
        tool=tool,
        repo_path=repo_path,
        user=user,
        action=action,
        status=status,
        error=error,
        pre_condition=_serialize_state(pre_condition),
        post_condition=_serialize_state(post_condition),
    )

def _serialize_state(state: RepositoryState | None) -> dict[str, Any] | None:
    """Serialize a RepositoryState to a JSON-safe dict."""
    if state is None:
        return None
    return {
        "path": state.path,
        "is_dirty": state.is_dirty,
        "head_type": state.head_type,
        "active_branch": state.active_branch,
        "untracked_file_count": state.untracked_file_count,
        "protected_branch": state.protected_branch,
        "ref_valid": state.ref_valid,
    }
```

### Details

- `pre_condition` captures state before operation execution
- `post_condition` captures state after operation execution
- `_serialize_state()` converts `RepositoryState` to JSON-safe dict for serialization
- Audit records include correct repository identity via `RepositoryState.path`

## Compatibility considerations

- `AuditRecord` gains optional `pre_condition` and `post_condition` fields — existing consumers are unaffected
- `_build_audit_record()` gains optional parameters — existing callers are unaffected
- Backward compatibility: existing audit log format is preserved

## Security considerations

- Frozen dataclass immutability must hold under all code paths
- `RepositoryState._repo` weak reference must not prevent garbage collection
- Pipeline early-exit must not skip required audit entries
- Option-injection prevention via `_is_safe_ref()` must be enforced before any `git.Repo` query

## Rollback considerations

- If `RepositoryState` causes behavioral regression, revert callers to direct `git.Repo` queries
- If removed methods are still needed temporarily, restore them as delegation wrappers

## Validation plan

- Verify existing test suite passes without modification (behavioral equivalence)
- Compare output of old vs new guards on identical inputs
- Verify pipeline ordering: Stage 4 → Stage 5 → Stage 6 → Stage 7
- Verify no behavioral regression in dirty-worktree, detached-HEAD, or protected-branch checks

## Completion criteria

- [ ] All write-protection guards use `RepositoryState` exclusively — zero direct `git.Repo` queries in guard logic
- [ ] Pipeline ordering verified via test: Stage 4 → Stage 5 → Stage 6 → Stage 7
- [ ] Existing test suite passes without modification (behavioral equivalence)
- [ ] No behavioral regression in dirty-worktree, detached-HEAD, or protected-branch checks
- [ ] Lint/type check passes: `ruff check scripts/mcp_servers/git/` and `mypy scripts/mcp_servers/git/`

## Out of scope

- GitHub MCP's existing `protected_branches`/force-push handling (already implemented separately)
- Redesign of Agent-side approval risk-tier mapping (tracked separately as Known Issue MCP-004)
- Any capability to allow Force Push, even as an administrative feature

## execution_status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20260828-162303_mcp003_git_write_protection_pipeline.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-134950_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-134950
- **Related target files**: scripts/mcp_servers/audit.py
