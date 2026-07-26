## Goal

Add TTL-based expiration for pending approvals across sessions to prevent bypass of approval flows through session interruption/resumption.

## Scope

**In-Scope:**
- Add `expires_at` field to `ApprovalRecord` model
- Update database schema to include `expires_at` column with migration
- Update `find_all_pending_approvals()` to filter out expired approvals
- Update `_recover_pending_approvals()` to reject expired approvals with warning message
- Update `request_approval()` to set `expires_at` on new approvals

**Out-of-Scope:**
- Changes to other approval-related functions beyond expiration filtering
- Any changes to the approval resolution flow itself

## Assumptions

1. A reasonable default TTL for pending approvals should be defined (e.g., 24 hours)
2. Database migration can add the `expires_at` column without data loss
3. Expired approvals should be silently filtered during recovery rather than causing errors

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | What is the appropriate TTL for pending approvals? | Review business requirements | False |
| UNK-02 | Whether existing pending approvals need migration | Check production DB state | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - `scripts/agent/workflow/models.py` — add `expires_at` field to `ApprovalRecord`
  - `scripts/db/schema_sql.py` — add `expires_at` column to `approvals` table
  - `scripts/agent/workflow/approval_ops.py` — update `find_all_pending_approvals()`, `request_approval()`
  - `scripts/agent/startup.py` — update `_recover_pending_approvals()`

- **Blast Radius:**
  - Medium — spans models, schema, and multiple modules
  - Requires database migration

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of the affected files:
```python
# Current ApprovalRecord:
class ApprovalRecord:
    approval_id: str
    task_id: str
    stage_id: str | None
    status: str
    reason: str | None
    created_at: str
    resolved_at: str | None
    workflow_id: str = ""

# Proposed ApprovalRecord:
class ApprovalRecord:
    approval_id: str
    task_id: str
    stage_id: str | None
    status: str
    reason: str | None
    created_at: str
    resolved_at: str | None
    workflow_id: str = ""
    expires_at: str | None  # ISO-8601 timestamp

# Current schema:
CREATE TABLE IF NOT EXISTS approvals (
    approval_id TEXT PRIMARY KEY,
    task_id     TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    stage_id    TEXT,
    status      TEXT NOT NULL DEFAULT 'pending',
    reason      TEXT,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    resolved_at TEXT,
    workflow_id TEXT NOT NULL DEFAULT ''
);

# Proposed schema:
CREATE TABLE IF NOT EXISTS approvals (
    approval_id TEXT PRIMARY KEY,
    task_id     TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    stage_id    TEXT,
    status      TEXT NOT NULL DEFAULT 'pending',
    reason      TEXT,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    resolved_at TEXT,
    workflow_id TEXT NOT NULL DEFAULT '',
    expires_at  TEXT
);

# Current find_all_pending_approvals:
WHERE t.status = 'pending_approval'
  AND a.status = 'pending'

# Proposed find_all_pending_approvals:
WHERE t.status = 'pending_approval'
  AND a.status = 'pending'
  AND (a.expires_at IS NULL OR a.expires_at > strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
```

## Implementation

### Target files
- `scripts/agent/workflow/models.py`
- `scripts/db/schema_sql.py`
- `scripts/agent/workflow/approval_ops.py`
- `scripts/agent/startup.py`

### Procedure
1. Open `scripts/agent/workflow/models.py`
2. Add `expires_at: str | None` field to `ApprovalRecord` dataclass after `workflow_id`
3. Save the file
4. Open `scripts/db/schema_sql.py`
5. Add `expires_at TEXT` column to `approvals` table after `workflow_id` line
6. Save the file
7. Open `scripts/agent/workflow/approval_ops.py`
8. Update `request_approval()` to set `expires_at` based on TTL (24 hours from creation)
9. Update `find_all_pending_approvals()` to filter out expired approvals using SQL condition
10. Update `_recover_pending_approvals()` in `startup.py` to log warning when rejecting expired approvals
11. Save the files

### Method
Add expires_at field to model and schema, then filter expired approvals in queries.

### Details
- `models.py`: Add `expires_at: str | None` field to `ApprovalRecord` dataclass
- `schema_sql.py`: Add `expires_at TEXT` column to `approvals` table
- `approval_ops.py`:
  - In `request_approval()`: Calculate `expires_at = _now() + TTL` (24 hours)
  - In `find_all_pending_approvals()`: Add `AND (a.expires_at IS NULL OR a.expires_at > strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))` to WHERE clause
- `startup.py`: In `_recover_pending_approvals()`: Log warning when rejecting expired approvals

## Compatibility considerations

N/A — database migration is non-destructive (ALTER TABLE ADD COLUMN)

## Security considerations

N/A — this change improves security posture

## Rollback considerations

- Simple revert: remove the expires_at column from schema and restore original code from git history

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/workflow/models.py` | Verify `expires_at` field exists | Manual verification | Field present |
| `scripts/db/schema_sql.py` | Verify schema includes `expires_at` | Manual verification | Column present |
| `scripts/agent/workflow/approval_ops.py` | Expired approvals filtered from query | `uv run pytest -k "approval" -v` | No expired approvals returned |
| `scripts/agent/startup.py` | Expired approvals rejected during recovery | `uv run pytest -k "approval" -v` | Warning logged for expired |

## Out of scope

- Changes to other approval-related functions beyond expiration filtering
- Any changes to the approval resolution flow itself

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260726-165648_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-033004
- Related target files: scripts/agent/startup.py, scripts/agent/workflow/approval_ops.py, scripts/agent/tool_approval.py
