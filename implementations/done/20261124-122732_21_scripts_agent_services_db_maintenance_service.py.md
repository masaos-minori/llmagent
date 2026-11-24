## Goal

Pass the cancellation event through the Session maintenance wrapper and return verified results, so the service layer does not drop the parameters the primitives need (REQ-002: cancellation; REQ-004: success only after the postcondition).

## Scope
**Release unit**: R1-registry-core (Phase 1, pass-through); the result contract is R4-verified-results (Phase 4)

- In scope: `DbMaintenanceService` method signatures and return values.
- Out of scope: `scripts/db/maintenance.py` (row 19), the command layer (row 4).

## Assumptions

- The wrapper stays a thin wrapper over `scripts/db/maintenance.py`; behavior and postconditions live in the primitives and in `db_session_ops.py`.

## Design decisions

- The service instance is injected rather than constructed per call, so the registry sees one writer per store; the command layer currently constructs it per call (`scripts/agent/commands/db_session_ops.py:21-24,34-36,43`).

## Alternatives considered

- Keeping the wrapper's `None` returns and verifying at the command layer — rejected: the caller could then report success without the check, which is what REQ-004 removes.

## Implementation
### Target file
`scripts/agent/services/db_maintenance_service.py`

### Procedure
1. Add `stop: threading.Event | None` to `checkpoint` (`:62`), `vacuum` (`:74`), `purge` (`:81`), and `recover_session` (`:100`) and forward it to the primitives.
2. Return the result objects the primitives produce instead of `None` (`vacuum` at `:74`).
3. Keep `stats` (`:43`) and `health` (`:52`) read-only.

### Method
- No logic added to the wrapper; each method forwards and returns.

### Details
- Configuration loading and the retention guards remain in `scripts/db/maintenance.py`.

### Companion test files
- `tests/agent/commands/test_command_blocking_offload.py`
  - Procedure: replace the "the offloaded callable runs to completion" lock with the cooperative-interruption behavior for an offloaded maintenance call.
  - Validation: `uv run pytest tests/agent/commands/test_command_blocking_offload.py -q` (REQ-002; AC-2).

## Compatibility considerations

- The consumer scan for `DbMaintenanceService` lists importers in the command layer and the service tests; the signature change lands with them in the same phase.

## Security considerations

- N/A: no approval decision here; the guard is decided at registration.

## Rollback considerations

- N/A: revert the Phase 1 commit for the pass-through and the Phase 4 commit for the result contract separately.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/services/db_maintenance_service.py` | Unit | `uv run pytest tests/db/test_db_maintenance.py tests/agent/commands/test_command_blocking_offload.py -q` | Cancellation event passed through; verified results returned |
| Same file | Quality gates | `uv run ruff check scripts/agent/services/db_maintenance_service.py`, `uv run mypy scripts/agent/services/db_maintenance_service.py` | No finding |

## Completion criteria

- A cancelled run through this wrapper reports the interrupted outcome, and no call through it can report success without the postcondition.

## Out of Scope

- The primitives, the command messages, the registry.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Forward the cancellation event | Completed | — | 20261124-160831 | Phase 1 Phase 1 part done: stop is passed through to each operation. |
| 2 | Return the result objects | Completed | — | 20261124-192923 | Phase 4 Phase 4 part done here, recorded as a deviation to row 4 per the 2026-11-24 decision: the measurement lives in this service and is measured on the same connection the run used. checkpoint re-reads journal_mode and the WAL file size; vacuum reads page_count before and after plus freelist_count; purge re-counts sessions rows after the commit; recover re-runs quick_check. A stopped run carries no postcondition values and is never verified. Helper functions _pragma_text, _pragma_int, _file_size were added. |
| 3 | Update the companion test per Validation plan | Completed | — | 20261124-160831 | Covered by this document Phase 1 part covered by tests/db/test_db_maintenance.py and tests/agent/commands/test_command_blocking_offload.py; both pass. |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261124-192923 | Phase 1 part: ruff, mypy pass. Phase 4 part: ruff, ruff format, mypy, bandit (0 Medium/High), module-size gate and radon pass on this file. Deviation on the test location: the postcondition is asserted in tests/agent/commands/test_agent_cmd_session.py (row 42), because tests/db/test_db_maintenance.py covers the primitives only and no service-layer test file exists for this wrapper. |

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
- **Requirement ID**: REQ-002 (cancellation), REQ-004 (verified result before the success line)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `scripts/agent/services/db_maintenance_service.py`, `tests/agent/commands/test_command_blocking_offload.py`