# Implementation Procedure: `scripts/eventbus/authz_ttl.py` (EBAUTHGEN001 Phase 2)

**Plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` (REQ-005; Design `:171`)

## Goal
New module implementing the TTL expiry sweep: detect expired authorization pairs with an
injectable clock and remove them as one atomic generation update through the same
build-first path, auditing each removal.

## Scope

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions
- `async def authz_sweep_loop(app, clock=time.time) -> None` (new): loop pattern
  mirroring `_dlq_loop` (`scripts/eventbus/app.py:139-158`): sleep
  `cfg.authz_sweep_interval_seconds`, catch `(OSError, ValueError)` per cycle, never
  crash the lifespan task. `clock` is an injectable zero-arg callable returning unix
  epoch seconds (tests inject a controllable clock; production uses the default).
- Expiry data source: `current_generation().expiries`
  (`(consumer_id, topic, expires_at)`); pairs with `expires_at <= clock()` are expired.
- Removal generation (compare-and-swap): capture `gen = current_generation()` first; if
  no expiry has elapsed, do nothing. Otherwise build removal config via
  `dataclasses.replace` minus the expired pairs, principals via `auth._build_principal_map`,
  remaining `expiries`, `baseline_hash` recomputed, `generation = gen.generation + 1`.
  Before publishing, re-check `current_generation() is gen`; if a concurrent admin update
  bumped the generation, abort this cycle and retry on the next interval (plan Risk `:205`).
- On publish: `app.state.config = new_gen.config`, then `publish_generation(new_gen)`,
  then `log_privileged_action(consumer_id="system", request_id="", route="/ttl_sweep",
  target="ttl_expiry", detail="<name>:<count>;...;persistent:false;gen:<prev>-><new>",
  actor="", previous_generation=prev, new_generation=new)` (Design `:171`; vocabulary
  documented in doc 15).
- Failed rebuild keeps the previous generation active (same guarantee as doc 03; a raise
  from `_build_principal_map` aborts the cycle without publishing).

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
### Evidence (new file)
- Absence verified 2026-10-30: no `ttl`/`expires`/`epoch` symbols in `scripts/eventbus/`
  (plan Background `:29`); `ls scripts/eventbus/authz_ttl.py` -> no such file.

1. Create the module with the loop above; module-level `logger` like `dlq.py`/`app.py`.
2. Keep all cross-module imports at the top-level `eventbus.*` layer contract
   (`skills/DESIGN.md` Shared Vocabulary).

## Compatibility considerations
**Dependencies**:
- Upstream: doc 01 (`AuthzGeneration.expiries`, `current_generation()`,
**Blocks**: doc 05 (app.py wiring), doc 09 (expiry tests)

## Security considerations
- Existing authentication/authorization boundaries are unchanged except where this procedure states otherwise; secret values must never appear in logs, audit records, or error messages (plan Risk).

## Rollback considerations
- Revert this file together with its paired test rows in the same commit; the change is additive and gated by the plan's checkers.

## Validation plan
- `uv run pytest tests/eventbus/test_authz_generation_ttl.py` (row 09: injected-clock
  expiry, sweep atomicity, abort-on-bump, failed-rebuild preservation).

## Completion criteria
- AC-2: expiry is deterministic under the injected clock, one atomic generation update
  plus one audit record; concurrent admin bumps make the sweep abort, never publish out
  of order.

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

## Marker record
- `(new)` markers applied: `authz_sweep_loop` (Contract section); the audit vocabulary
  route /ttl_sweep and target "ttl_expiry" (written unbacktick'd to avoid stale-detector
  path false positives); the file itself is new.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005
- **Source issue**: `issues/20261029-104509_ebauthgen001_eventbus-authz-generation-ttl.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` — Implementation Target Files row 04
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-141000
- **Related target files**: `scripts/eventbus/authz_ttl.py`
