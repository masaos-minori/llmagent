## Goal

Replace the Known-Limitations bullet at `:144` — which states that WAL checkpoint *and*
backup timeouts are "fixed in `ResourceShutdownCoordinator.close_resources()`" — with the
single bound the code actually reads after this Plan, and state what a bound-expired
shutdown leaves behind (AC-1, AC-2, AC-7).

## Scope

Docs edit to `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
only. One bullet in the "Known Limitations / Unresolved Issues" section (`:142-146`).
Reference reads: `scripts/agent/resource_shutdown_coordinator.py` (the single bound,
Phase 3), `scripts/agent/wal_checkpoint_manager.py` (abandoned-step effect). Depends on
row 2 (the single named bound) so the doc names the correct value.

## Assumptions

- The current bullet is the single line at `:144`: "The WAL checkpoint and backup
  timeouts at shutdown are fixed in `ResourceShutdownCoordinator.close_resources()` and
  are not configurable; a timeout is recorded as a shutdown error and logged".
- After Phase 3 there is exactly one shutdown-path timeout bound (UNK-01 owns the
  number); the doc must not claim two fixed values or a value the code no longer reads.

## Design decisions

- Rewrite the bullet to state: the shutdown path enforces **one** named timeout bound
  (name/value per UNK-01), it is not externally configurable, a bound expiry is recorded
  as a shutdown error and logged, and a checkpoint abandoned mid-write leaves the WAL to
  be replayed or checkpointed on the next open — "timed out" means "not rolled back",
  never "left clean" (REQ-010, AC-7).
- Do not hardcode a number into the doc; reference the single bound the code reads so
  the doc stays correct regardless of UNK-01's choice.
- The cleanup-order list (`:76-82`) is left unchanged unless the order text itself
  changes (it does not — AC-6).

## Alternatives considered

- Listing both the old 30 s / 10 s literals — rejected: after REQ-003 only one bound is
  read, so two literals would be stale (AC-2).
- Adding a new section — rejected: `governance_03_issue-and-uncertainty-management.md`
  manages known limitations centrally; edit the existing bullet in place.

## Implementation

### Target file

`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure

1. Locate the "Known Limitations / Unresolved Issues" section and the bullet at `:144`.
2. Replace that bullet's text with a statement of the single bound the code reads, that
   it is not configurable, that a bound expiry is recorded as a shutdown error and
   logged, and that an abandoned checkpoint leaves the WAL to be replayed/checkpointed on
   next open (never "left clean").
3. Keep the "(Explicit in code — …)" attribution style used by sibling bullets.

### Details

- The exact bound name/number is decided by UNK-01 during implementation; the doc
  references "the single shutdown-path timeout bound" rather than a literal so it does
  not drift.
- After editing, run the doc checks required by `routing.md` for any edited `docs/*.md`:
  `tools/check_docs_quality.py`, `tools/check_docs_structure.py`,
  `tools/check_docs_content_policy.py`, `tools/check_docs_consistency.py --domain agent`.

## Compatibility considerations

- Doc-only; no code change. The bullet remains accurate through Phase 3's single-bound
  collapse.

## Security considerations

- N/A: documentation edit.

## Rollback considerations

- Revert the bullet. Single logical commit; reversible.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain agent` (all pass; `routing.md` "Any `docs/*.md` file was added or edited").

## Completion criteria

The Known-Limitations bullet states the single bound the code reads (not two fixed
values), records that a bound expiry is a logged shutdown error, and states the
abandoned-step effect; all four doc checks pass.

## Out of Scope

- Production bound edits — row 2. The other doc — row 7.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the `:144` Known-Limitations bullet with the single bound + abandoned-step effect | Pending | — | — | Gated on row 2 (single bound) |
| 2 | Run doc checks (`routing.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Bound name/number is UNK-01; doc references the single bound generically until decided | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-010, AC-2, AC-7
- **Source issue**: `issues/20261021-093421_shutdown001-wal-checkpoint-timeout-guard-cannot-fire.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-043330_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-084708
- **Related target files**: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
