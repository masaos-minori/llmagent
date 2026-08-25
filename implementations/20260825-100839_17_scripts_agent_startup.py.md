## Goal
- Remove `startup.py`'s read of `RuntimeToolRegistry.degraded_servers`, which
  `scripts/shared/runtime_tool_registry.py`'s document in this same batch removes —
  without this fix, startup's readiness-log rendering would raise `AttributeError`
  (REQ-007, cascading fix discovered during investigation of
  `scripts/agent/services/mcp_tool_discovery.py`).

## Scope
- In scope: the readiness-log block in `scripts/agent/startup.py` that reads
  `runtime_tools.degraded_servers` and appends an "Excluded tools (degraded): ..."
  log line.
- Out of scope: any other startup/readiness-log behavior; the `unavailable_servers`-
  based exclusion reporting (unaffected, since `unavailable_servers` is not removed).

## Assumptions
- **This file was not listed in the Plan's (`plans/20260825-095817_plan.md`)
  "Related target files."** It was discovered during Step 3 investigation of
  `scripts/agent/services/mcp_tool_discovery.py` (REQ-007) as a required companion
  change: `startup.py` is the only real reader of
  `RuntimeToolRegistry.degraded_servers` in the codebase. This document exists to
  keep REQ-007 mergeable without a startup crash; the Plan should be updated to add
  this file to its Related target files' list on next revision.
- Pending UNK-02 sign-off (same gate as the other REQ-007 documents) — this file's
  change is only needed if the "remove" default is confirmed; if the sign-off instead
  chooses to wire `degraded_servers` to real behavior, this file's change does not
  apply and should be revisited against the new design instead.

## Design decisions
- Remove the readiness-log block for `degraded_servers` entirely, since the property
  it reads no longer exists after `runtime_tool_registry.py`'s change. Do not replace
  it with a stub or empty-collection placeholder — that would misleadingly suggest
  the mechanism still exists.

## Alternatives considered
- Adding a `getattr(runtime_tools, "degraded_servers", frozenset())` guard to avoid
  the `AttributeError` without removing the log block — rejected; this would silently
  paper over the property's removal instead of cleanly retiring the dead readiness-
  log line, and would leave dead-looking code that always reports zero degraded
  servers.

## Implementation
### Target file
`scripts/agent/startup.py`

### Procedure
1. Remove the `degraded_servers = runtime_tools.degraded_servers` assignment in the
   readiness-log rendering code.
2. Remove the `if degraded_servers: lines.append(...)` block that follows it.
3. Confirm the `degraded_keys`/`unavailable`-related readiness-log lines (the
   separate `unavailable_servers`-based reporting) are unaffected and remain as-is.

### Method
- Pure deletion in the readiness-log rendering function; no other startup logic
  (agent construction, `_recover_pending_approvals()`, etc.) is touched.

### Details
- This change must land in the same commit/PR as
  `scripts/shared/runtime_tool_registry.py`'s `degraded_servers` property removal —
  landing one without the other either leaves dead code (this file unchanged) or
  causes a startup crash (property removed first).

## Compatibility considerations
- Removes one line from the startup readiness log output; no other observable
  behavior change, since the removed line always reported an empty set in practice
  (confirmed: no production call site ever populated `degraded_servers`).

## Security considerations
- N/A: readiness-log rendering only; no security/approval logic involved.

## Rollback considerations
- Restoring the two deleted lines from the commit fully reverts this change,
  provided `RuntimeToolRegistry.degraded_servers` is also restored in the same
  rollback (the two changes are coupled).

## Validation plan
- Add or confirm a startup test asserts the readiness log no longer references
  "Excluded tools (degraded)" and does not raise `AttributeError` after
  `RuntimeToolRegistry.degraded_servers` is removed.
- `uv run pytest tests/agent/ -v -k startup` (or the actual startup test module name,
  to be confirmed at implementation time) — full pass with no `AttributeError`.

## Out of scope
- `scripts/shared/runtime_tool_registry.py`'s property removal itself — separate
  document (must ship together with this one).
- Updating `plans/20260825-095817_plan.md`'s Related target files list to formally
  add this file — a plan-maintenance action, not a code change; flagged here for the
  Plan owner's awareness.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocked on UNK-02 sign-off; must land in the same change as `scripts/shared/runtime_tool_registry.py`. This target file was not in the Plan's original Related target files list — discovered during investigation. |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no doc update required by this item |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | UNK-02 (Plan `plans/20260825-095817_plan.md`): maintainer sign-off needed on wiring vs. removing `degraded_servers`/`requires_approval` | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: issues/20260821_h3-h4-m1-followup-implementation-tasks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-095817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-100839
- **Related target files**: scripts/agent/startup.py
