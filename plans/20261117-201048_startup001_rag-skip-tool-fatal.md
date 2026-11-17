## Goal
- Add a `has_fatal` short-circuit after the MCP tool discovery step in
  `StartupValidationPipeline.check_services` so a tool-discovery FATAL skips the RAG
  consistency check instead of running it unconditionally.

## Priority
Low

## Scope
- **In-Scope**:
  - Add an early return guarded by `pipeline.has_fatal` after the MCP tool discovery block
    in `check_services`, placed before the RAG consistency step.
  - Add regression tests asserting a tool-discovery FATAL skips the RAG check and that the
    RAG check still runs on a discovery warning-only path.
  - Update the startup validation operations doc to state the RAG check is skipped on any
    runtime-stage FATAL (readiness or tool discovery), not only on a readiness FATAL.
- **Out-of-Scope**:
  - Changing the readiness short-circuit logic or its position.
  - Changing what the RAG consistency check verifies or how it classifies severity.
  - Making other runtime-stage checks short-circuit each other.
  - Touching the config-only stage or the non-RAG pipeline checks.
- **Dependencies**: N/A: none. Related but independent issues exist (see below); implementing
  them first does not change this Plan.
  - **Depends on**: `N/A: none`

## Background
In `scripts/agent/startup_validation.py`, `StartupValidationPipeline.check_services` runs
the readiness check first, returns early when `pipeline.has_fatal` is set, then runs MCP tool
discovery, then runs the RAG consistency check. The early return after readiness means a
readiness FATAL skips both tool discovery and the RAG check. There is no equivalent re-check
after tool discovery, so a tool-discovery FATAL does not prevent the RAG check from running.
The operations doc
(`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`) scopes the
skip to readiness, which matches the current code but will be stale after this change.

## Problem
On a tool-discovery FATAL the process is already failing and will abort startup. The RAG
consistency check still runs anyway, consuming up to the startup bound and adding a further
`rag_consistency` warning to an already-failing path. The RAG result is only ever a warning
(the check stays soft), so it changes nothing about the outcome; it only delays the abort and
adds noise.

## Reason for Change
The wasted work happens on an already-failing path, so correctness is unaffected. It is Low:
it is a non-blocking efficiency and log-noise improvement, not a correctness,
data-integrity, or reliability defect.

## Implementation Intent
Mirror the readiness short-circuit: after the MCP tool discovery block, if
`pipeline.has_fatal` is set, return `pipeline` before the RAG consistency step. Keep the RAG
check's existing soft semantics (fatal findings stay fatal, timeout and other failures stay
warnings, startup proceeds) for every path that still reaches it. Do not touch the readiness
short-circuit or any other check.

## Requirements
- `REQ-001`: After the MCP tool discovery block in `check_services`, add an early return when
  `pipeline.has_fatal` is set, placed before the RAG consistency step.
- `REQ-002`: The RAG consistency check keeps its existing soft semantics for every path that
  still reaches it; the readiness FATAL short-circuit and its test are preserved.
- `REQ-003`: A regression test asserts a tool-discovery FATAL skips the RAG consistency check
  (the RAG service is not invoked and no `rag_consistency` outcome is recorded), and that the
  RAG check still runs on a discovery warning-only path.
- `REQ-004`: The operations doc states the RAG consistency check is skipped on any
  runtime-stage FATAL (readiness or tool discovery), not only on a readiness FATAL.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this table —
no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/startup_validation.py` | Modify | Add `if pipeline.has_fatal: return pipeline` after the MCP tool discovery block (lines 194-223) and before the RAG consistency step (line 225); mirrors the readiness short-circuit at lines 190-192. No such re-check exists today, so a tool-discovery FATAL currently does not skip the RAG check. (checked in Step 2) | REQ-001, REQ-002 | `StartupValidationPipeline.check_services` readiness short-circuit at lines 190-192; tool discovery block lines 194-223; RAG step lines 225-276 | `tests/agent/test_startup_validation.py` | Verified |
| `tests/agent/test_startup_validation.py` | Modify | Add a regression test injecting a tool-discovery FATAL and asserting the RAG service is not called and no `rag_consistency` outcome is recorded, plus a warning-only path test. (checked in Step 2) | REQ-003 | Existing `_run_check_services` helper mocks discovery with `findings=[]`; a FATAL finding is injected via `findings=[MagicMock(status=StartupCheckStatus.FATAL, message=...)]`. | `tests/agent/test_startup_validation.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tests/agent/test_startup_validation.py` | Read to mirror the existing `_run_check_services` helper and the readiness FATAL behavior when writing the new regression test. | `scripts/agent/startup_validation.py` |

## Acceptance Criteria
- `AC-001` (REQ-001): A tool-discovery FATAL returns before the RAG consistency check runs.
- `AC-002` (REQ-002): The RAG consistency check still runs when no fatal exists (readiness OK
  and discovery OK or warning-only).
- `AC-003` (REQ-002): The readiness FATAL short-circuit still skips tool discovery and the RAG
  check.
- `AC-004` (REQ-003): A regression test asserts a tool-discovery FATAL skips the RAG check and
  that the RAG check still runs on a discovery warning-only path.
- `AC-005` (REQ-002): Existing startup validation tests still pass.

## Tests
- `TEST-001` (REQ-003): Inject a tool-discovery FATAL and assert the RAG consistency service is
  not called and no `rag_consistency` outcome is recorded.
- `TEST-002` (REQ-002): Confirm the RAG check still runs on a discovery warning-only path.
- `TEST-003` (REQ-002): Run `uv run pytest tests/agent/test_startup_validation.py`.
- `TEST-004` (REQ-001): Run `uv run ruff check scripts/agent/startup_validation.py` and
  `uv run mypy --no-namespace-packages scripts/agent/startup_validation.py`.

## Documentation Impact
- `DOC-001` (REQ-004): Update `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
  to state that the RAG consistency check is skipped on any runtime-stage FATAL (readiness or
  tool discovery), not only on a readiness FATAL. Two occurrences describe the readiness-only
  skip (runtime-stage paragraph and the `mcp_auth` bullet). Keep it high-level (intent and
  failure behavior); do not add implementation-location detail or line numbers.

## Assumptions
- The fix is confined to runtime-stage control flow; the config-only stage and the RAG check's
  soft/fail-closed-downstream contract are unchanged.
- Updating the operations doc does not affect another document, so the doc update belongs in
  this change rather than a separate pass (resolves the Issue's Unresolved Question).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the operations doc should be updated as part of this change or left for a separate documentation pass. | Resolved by evidence: the doc describes the current readiness-only skip and becomes stale once the behavior changes; updating it does not affect another document. | Recorded as resolved; DOC-001 included. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/startup_validation.py` | Modify | Low — one early return in a startup pipeline; callers observe the same result shape | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_startup_validation.py` | Modify | Low — additive regression test; existing tests unaffected | N/A | N/A | not applicable (rsynced) |

## Design
Path A (small task). Classification rationale: affects 2 files (one source, one test), no
public or runtime-facing interface change, no database schema change. The change is a single
early-return mirroring the existing readiness short-circuit; no design decision beyond placing
it correctly is required. The RAG check's soft semantics (fatal findings stay fatal,
timeout/other failures stay warnings, startup proceeds) are preserved for every path that
still reaches it — this contract is the boundary the early return must not cross.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or
tests until another phase lands (for example a `NOT NULL` column added before its write path):
one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be
validated alone}`. Phases that land together in one commit cannot be validated alone: declare them
as a unit; `N/A` is only for a Plan whose every phase passes validation alone.

1. **Phase 1: Core logic**
   - [ ] REQ-001: In `scripts/agent/startup_validation.py` `check_services`, add
     `if pipeline.has_fatal: return pipeline` after the MCP tool discovery block (before the
     RAG consistency step). Preserve the readiness short-circuit and the RAG check's soft
     semantics.
2. **Phase 2: Tests**
   - [ ] REQ-003: In `tests/agent/test_startup_validation.py`, add a regression test that
     injects a tool-discovery FATAL and asserts the RAG service is not called and no
     `rag_consistency` outcome is recorded; add a warning-only path test confirming the RAG
     check still runs.
3. **Phase 3: Docs & verification**
   - [ ] REQ-004: Update `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
     to state the RAG check is skipped on any runtime-stage FATAL.
   - [ ] REQ-002/REQ-003: Run `uv run pytest tests/agent/test_startup_validation.py`,
     `uv run ruff check scripts/agent/startup_validation.py`, and
     `uv run mypy --no-namespace-packages scripts/agent/startup_validation.py`.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/startup_validation.py` | Unit: drive `check_services` with a tool-discovery FATAL and a warning-only discovery. | `uv run pytest tests/agent/test_startup_validation.py` | New tests pass; existing tests pass. |
| `scripts/agent/startup_validation.py` | Static: lint and type-check the touched file. | `uv run ruff check` / `uv run mypy --no-namespace-packages` | Clean. |

## Risks
- **Risk**: Placing the early return after the RAG step by mistake would not change behavior.
  → **Mitigation**: Place it immediately after the discovery block and before the RAG step;
  the regression test (RAG service not called) fails if placed incorrectly.
- **Risk**: Accidentally altering the readiness short-circuit or the RAG check's soft
  semantics. → **Mitigation**: Scope the edit to a single early return; preserve the readiness
  block and RAG block untouched; existing tests guard both.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Core logic: add `has_fatal` early return after tool discovery | Pending | — | — | |
| 2 | Tests: regression test for tool-discovery FATAL skip | Pending | — | — | |
| 3 | Docs & verification: ops doc update and validation | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261117-175055_startup001_rag-skip-tool-fatal.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261117-201048
- **Related target files**: `scripts/agent/startup_validation.py`, `tests/agent/test_startup_validation.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.
