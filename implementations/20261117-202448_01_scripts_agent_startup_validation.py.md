## Goal

Add a `pipeline.has_fatal` short-circuit after the MCP tool discovery block in
`StartupValidationPipeline.check_services` so a tool-discovery FATAL skips the RAG
consistency check instead of running it unconditionally (`REQ-001`, `REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit

### Companion test files
- `tests/agent/test_startup_validation.py`
  - Procedure: add a regression test injecting a tool-discovery FATAL and asserting the
    RAG service is not called and no `rag_consistency` outcome is recorded, plus a
    warning-only path test confirming the RAG check still runs.
  - Validation: `uv run pytest tests/agent/test_startup_validation.py`.

## Assumptions
- The fix is confined to runtime-stage control flow; the config-only stage and the RAG
  check's soft/fail-closed-downstream contract are unchanged.
- The operations-doc update (`DOC-001`, `REQ-004`) is a required part of this plan but its
  target file is **not** a row of the plan's frozen `Implementation Target Files` table; it
  is tracked separately (see Compatibility considerations).

## Design decisions
- Mirror the readiness short-circuit exactly: `if pipeline.has_fatal: return pipeline`
  placed immediately after the MCP tool discovery block and before the RAG consistency
  step. No new design decision beyond placement is required.
- Preserve the RAG check's existing soft semantics (fatal findings stay fatal, timeout and
  other failures stay warnings, startup proceeds) for every path that still reaches it.

## Alternatives considered
- Placing the early return after the RAG step: rejected — it would not skip the RAG check
  and changes nothing (the regression test "RAG service not called" fails if misplaced).
- Short-circuiting other runtime-stage checks or the config-only stage: rejected — out of
  scope; only the RAG step follows tool discovery.

## Implementation
### Target file
- `scripts/agent/startup_validation.py`

### Procedure
In `check_services`, after the MCP tool discovery block (lines 201-223) and before the RAG
consistency step (line 225), add:
```python
# A tool-discovery FATAL skips the RAG check too.
if pipeline.has_fatal:
    return pipeline
```
directly mirroring the readiness short-circuit at lines 190-192. Leave the readiness block
and the RAG block untouched.

### Method
- Locate the readiness short-circuit (`if pipeline.has_fatal:` at line 191) and the RAG
  step (`# 6. RAG consistency` at line 225) with `rg`.
- Insert the early return between the closing of the discovery `try/except` (line 223) and
  the RAG comment (line 225), preserving indentation.
- Confirm no `has_fatal` re-check already exists after discovery (none does today).

### Details
- `check_services` runs readiness (178-188), the readiness FATAL short-circuit (190-192),
  MCP tool discovery (201-223), then the RAG consistency check (225-276). There is no
  re-check after discovery, so a discovery FATAL currently does not prevent the RAG check.
- The discovery block sets `pipeline.has_fatal` via `add_fatal("mcp_tool_discovery", ...)`
  (lines 213-214, 219-223); the new guard returns before line 225 when that is set.
- Existing `_run_check_services` helper mocks discovery with `findings=[]`; inject a FATAL
  finding via `findings=[MagicMock(status=StartupCheckStatus.FATAL, message=...)]` for the
  skip assertion, and keep a `findings=[]` / warning-only case for the still-runs assertion.

## Compatibility considerations
- Behavior change is observable only on an already-failing path (tool-discovery FATAL): the
  RAG check no longer runs, so one `rag_consistency` warning is dropped from an aborting
  startup. For every non-fatal path the behavior is byte-for-byte unchanged.
- The plan's `DOC-001` requires updating
  `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` to state
  the RAG check is skipped on any runtime-stage FATAL (readiness or tool discovery). That
  file is **not** a row of the frozen `Implementation Target Files` table, so it is handled
  as a separate amendment (see the plan's `### Work Items Created` / `Blocker Log`); this
  document must not contain modification instructions for it.

## Security considerations
- Fail-closed preserved: a tool-discovery FATAL still routes through
  `pipeline.add_fatal()` unconditionally (ADR-004 Decision #14); the guard only skips the
  downstream soft RAG check, it does not weaken the fatal path.

## Rollback considerations
- N/A: revert the commit; the single early-return is isolated.

## Validation plan
- Unit: drive `check_services` with a tool-discovery FATAL (RAG service not called, no
  `rag_consistency` outcome) and a warning-only discovery (RAG check still runs).
- Static: `uv run ruff check scripts/agent/startup_validation.py` and
  `uv run mypy --no-namespace-packages scripts/agent/startup_validation.py`.
- Suite: `uv run pytest tests/agent/test_startup_validation.py`.

## Completion criteria
- A tool-discovery FATAL returns before the RAG consistency check runs (`AC-001`).
- The RAG check still runs on a non-fatal (OK or warning-only) discovery path (`AC-002`).
- The readiness FATAL short-circuit still skips tool discovery and the RAG check (`AC-003`).
- New regression tests pass and existing startup-validation tests still pass (`AC-005`).
- ruff and mypy are clean on the touched file.

## Out of Scope
- Changing the readiness short-circuit logic or its position.
- Changing what the RAG consistency check verifies or how it classifies severity.
- Making other runtime-stage checks short-circuit each other.
- Touching the config-only stage or the non-RAG pipeline checks.

## Execution Status

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
- **Requirement ID**: `REQ-001` (tool-discovery FATAL skips the RAG check) and `REQ-002` (RAG soft semantics preserved on still-reached paths)
- **Source issue**: `issues/20261117-175055_startup001_rag-skip-tool-fatal.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261117-201048_startup001_rag-skip-tool-fatal.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-202448
- **Related target files**: `scripts/agent/startup_validation.py`, `tests/agent/test_startup_validation.py`
