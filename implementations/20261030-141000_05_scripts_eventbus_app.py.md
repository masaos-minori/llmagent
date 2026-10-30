# Implementation Procedure: `scripts/eventbus/app.py` (EBAUTHGEN001 Phase 2)

**Plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` (REQ-005, REQ-006; Design `:172`)

## Goal
Wire the TTL sweep task into the app lifespan (start/stop) and emit the startup
restart-baseline audit record.

## Scope
- `_DLQ_INTERVAL = 60.0` `:65`; lifespan `:69-92`: `_populate_token_maps` `:76`,
  sweep task `app.state.dlq_task = asyncio.create_task(_dlq_loop(app))` `:80`.
- `_shutdown_lifespan` `:95-136`: task cancel + await pattern `:107-112`.
- `_dlq_loop` `:139-158` (loop pattern to mirror).
- Admin route registration `@app.post("/admin/topics/authorization")`
  `admin_topics_authorization` `:304-305` — unchanged by this row.

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Startup (`lifespan`, after `_populate_token_maps` `:76`): emit one restart-baseline
   audit record (REQ-006, Design `:172`):
   `log_privileged_action(consumer_id="system", request_id="", route="/startup",
   target="authz_baseline", detail="baseline_hash:<hex>;runtime_overrides:removed",
   actor="")` with the hash of the loaded baseline generation. `consumer_id="system"`
   and `target="authz_baseline"` are the documented vocabulary (plan Risk `:206`).
2. Start the sweep task next to the DLQ task (mirror `:80`):
   `app.state.authz_sweep_task = asyncio.create_task(authz_sweep_loop(app))`.
3. Shutdown (`_shutdown_lifespan` `:107-112` pattern): cancel and await
   `authz_sweep_task` exactly like `dlq_task`, before broker shutdown.
4. Module-level import `from eventbus.authz_ttl import authz_sweep_loop` (top-level
   `eventbus.*` layer contract).

## Compatibility considerations
**Dependencies**:
- Upstream: docs 01, 02 (generation + sweep interval config), doc 04 (`authz_sweep_loop`)
**Blocks**: docs 05-dependent tests (08, 09), docs 14/15

## Security considerations
- Existing authentication/authorization boundaries are unchanged except where this procedure states otherwise; secret values must never appear in logs, audit records, or error messages (plan Risk).

## Rollback considerations
- Revert this file together with its paired test rows in the same commit; the change is additive and gated by the plan's checkers.

## Validation plan
- `uv run pytest tests/eventbus/test_authz_generation_ttl.py` (restart audit record
  present, baseline-only state after restart — AC-4; sweep stops cleanly at shutdown).
- Regression: existing lifespan tests (dlqbox001 pattern) stay green.

## Completion criteria
- AC-4 observable at every startup; sweep starts and stops within the lifespan without
  affecting the DLQ loop shutdown ordering.

## Out of Scope
- Everything outside the target file and the anchors recorded above; cross-plan boundaries and sequencing are recorded in the Source plan.

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify cited anchors before editing | Pending | — | — | |
| 2 | Apply the Implementation procedure | Pending | — | — | |
| 3 | Run the Validation plan gates | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-141000_01_scripts_eventbus_auth.py.md` | 1 (dependency) | Procedure | Pending | — | — |
| `20261030-141000_04_scripts_eventbus_authz_ttl.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- `(new)` markers applied: `authz_sweep_task` state field; the audit vocabulary route
  /startup and target "authz_baseline" (unbacktick'd to avoid stale-detector path false
  positives).

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005, REQ-006
- **Source issue**: `issues/20261029-104509_ebauthgen001_eventbus-authz-generation-ttl.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` — Implementation Target Files row 05
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-141000
- **Related target files**: `scripts/eventbus/app.py`
