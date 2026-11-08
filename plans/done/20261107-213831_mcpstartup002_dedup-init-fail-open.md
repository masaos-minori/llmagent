## Goal
Make a durable-dedup store initialization failure visible and safe instead of silently disabling write protection for non-retryable tools. When `load_dedup_config()` or `open_dedup_store()` fails, the process must either surface the failure at startup or fail closed for non-retryable tools (shell, delete, and other tools classified non-retryable), consistent with the existing lookup-failure path that already fails non-retryable tools closed. Eliminate the silent `dedup_state=""` write path that currently lets a non-retryable tool execute with no durable record and no marker in the result after one store failure.

## Priority
Medium

## Scope
- **In-Scope**:
  - `scripts/mcp_servers/dispatch.py` — `_dedup_context()` and the caller in `dispatch_tool()` so that a store-initialization failure does not produce a silent overlay-only write for non-retryable tools.
  - `tests/mcp_servers/test_mcp_dispatch.py` — assert the new behavior for the initialization-failure path and preserve the retryable-tool fail-open behavior.
- **Out-of-Scope**:
  - Changing which tools are classified retryable vs non-retryable.
  - Changing the idempotency-key reuse rejection logic.
  - Changing the durable dedup store schema, the overlay fallback data model, or `_purge_once`.
  - Adding a new configuration key or changing how `load_dedup_config()` resolves its values.
  - Any change to the `_duplicate_cache` in-memory layer.
- **Dependencies**: Sibling issues `issues/20261107-132004_mcpstartup001_python-m-double-execution.md`, `issues/20261107-132052_mcpstartup003_auth-guard-single-point.md`, and `issues/20261107-132117_mcpstartup004_run-http-diagnostics-cleanup.md` also edit `scripts/mcp_servers/server.py`; this issue does not touch that file, so there is no required order, but sequence against them if any later plan expands scope into `dispatch.py`. No `Depends on` entries.

## Background
Archived issue `issues/done/20261023-114103_mcpstart004_server-modules-load-config-before-isolation-and-package-init-imports-sibling-servers.md` and the durable-dedup design established that `mcp_servers.dispatch` opens its durable dedup store lazily on the first side-effecting call with an idempotency key. Current source verified against HEAD `47b837eb8`; `scripts/mcp_servers/dispatch.py` is unchanged since the review head `59dbae624`.

## Problem
`_dedup_context()` in `scripts/mcp_servers/dispatch.py` loads the dedup config and opens the store on first use. Its `except Exception` branch sets the module-global `_dedup_disabled = True`, logs one warning, and returns `(None, None)`. In `dispatch_tool()`, when the returned store is `None`, the entire dedup block is skipped and the tool executes with `dedup_state=""` — no durable record, no marker. For a **non-retryable** tool this means write protection is silently disabled for the rest of the process. The inline comment documents this as fail-open by design so a store failure does not stall tool calls. However, the *lookup*-failure path already treats non-retryable tools differently: a store lookup error raises `error_type="dedup_store_error"` and fails the call closed, while a retryable tool degrades to `dedup_state="store_error"`. The initialization-failure path has no such asymmetry; it degrades every tool, including non-retryable ones, to overlay-only.

## Reason for Change
Non-retryable tools (shell, delete, other write tools) rely on durable dedup as their only write-protection mechanism. A store that failed to initialize should not let them write with no record and no indication. The lookup-failure path already encodes the intended asymmetry; the initialization-failure path should match it. No incident is reported; this is a consistency and hardening change, so it is Medium rather than High.

## Implementation Intent
Preserve the documented fail-open intent for **retryable** tools (a store failure must not stall auto-replayable calls) while making the failure safe for **non-retryable** tools. Choose one of two mechanisms and record the choice in the Plan's Design: (a) mirror the lookup-failure asymmetry — on store-initialization failure, fail non-retryable tools closed with `error_type="dedup_store_error"` and degrade retryable tools to `dedup_state="store_error"`; or (b) surface the initialization failure at startup so the process refuses to serve with a broken dedup store. Decide the approach in the plan; do not change the retryable/non-retryable classification.

## Requirements
- `REQ-001`: A durable-dedup store initialization failure does not produce a silent overlay-only write for a non-retryable tool; the call is either failed closed with `error_type="dedup_store_error"` or the process fails to start, per the chosen mechanism.
- `REQ-002`: A retryable tool still degrades to overlay-only (`dedup_state="store_error"`) when the store is unavailable, preserving the documented fail-open intent for auto-replayable calls.
- `REQ-003`: The asymmetry between non-retryable (fail closed) and retryable (degrade) tools is identical to the existing store-lookup-error path, so the two failure modes cannot diverge again.
- `REQ-004`: `tests/mcp_servers/test_mcp_dispatch.py` asserts the initialization-failure behavior for both a retryable and a non-retryable tool, and the updated test fails on the current code.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/mcp_servers/dispatch.py` | Modify | `_dedup_context()` (`L182-193`) sets `_dedup_disabled=True` and returns `(None,None)` on init failure; the caller skips the dedup block for every tool including non-retryable ones (`dedup_state=""`). Reconcile the init-failure path with the lookup-failure asymmetry. | `REQ-001`/`REQ-002`/`REQ-003` | `_dedup_disabled` L171; `_dedup_context` `except Exception` L186; caller `store is None` skip L304-305; lookup error `dedup_store_error` L309-323 (checked in Step 2) | `tests/mcp_servers/test_mcp_dispatch.py` | `Verified` |
| `tests/mcp_servers/test_mcp_dispatch.py` | Modify | Assert the new initialization-failure behavior for retryable and non-retryable tools; confirm the test fails on current code. | `REQ-004` | existing dedup store-failure tests (checked in Step 2) | `tests/mcp_servers/test_mcp_dispatch.py` | `Verified` |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/mcp_servers/models.py` | Defines the retryable vs non-retryable classification consumed by `dispatch_tool()`; needed to route the init-failure path correctly. | `scripts/mcp_servers/dispatch.py` (`REQ-001`/`REQ-002`) |

## Acceptance Criteria
- `REQ-001`: With a store that fails to initialize, a non-retryable tool call is failed closed with `error_type="dedup_store_error"` (approach a) or the process fails to start (approach b); it never returns a successful overlay-only write with `dedup_state=""`.
- `REQ-002`: With a store that fails to initialize, a retryable tool call degrades to `dedup_state="store_error"` and proceeds overlay-only.
- `REQ-003`: The non-retryable/retryable split on init failure matches the store-lookup-error path exactly.
- `REQ-004`: The updated `test_mcp_dispatch.py` fails on current code and passes after the fix.

## Tests
- Parametrized test over a retryable and a non-retryable tool asserting the store-initialization-failure behavior (`REQ-001`/`REQ-002`).
- Extend `tests/mcp_servers/test_mcp_dispatch.py` so the new assertion fails on current code (`REQ-004`).

## Documentation Impact
Update the MCP dispatch/dedup documentation only if it states that a store initialization failure degrades all tools to overlay-only. State the boundary and failure behavior, not implementation details. Name the target doc via `docs/00_index.md` "Document References by Task" → mcp domain. Run the `docs/` checkers from `routing.md` for any edited doc.

## Assumptions
- The retryable/non-retryable classification in `models.py` is stable and is the correct axis for the asymmetry.
- Failing non-retryable tools closed on init failure does not break the launcher or watchdog startup expectations for the non-production path.
- Approach (a) is preferred unless the owner requires process-startup failure; the plan records the trade-off.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | whether the owner wants process-startup failure (approach b) or per-call fail-closed (approach a) | not stated in the issue | record the chosen approach in the implementation procedure; confirm with owner | `False` |
| `UNK-02` | whether any caller depends on `_dedup_disabled` staying `False` after a recoverable config error | not tested in this review | enumerate consumers of `_dedup_disabled` during implementation | `False` |
| `UNK-03` | whether the overlay-only fallback for retryable tools is asserted elsewhere beyond `test_mcp_dispatch.py` | not enumerated | search tests for `dedup_state="store_error"` and overlay fallback | `False` |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/mcp_servers/dispatch.py` | Modify | every side-effecting tool call with an idempotency key across all ten servers | 2 | N/A | not applicable (rsynced) |
| `tests/mcp_servers/test_mcp_dispatch.py` | Modify | that test file only | N/A | N/A | not applicable (rsynced) |

## Design
**Open decision — failure mechanism (drives `REQ-001`/`REQ-002`):**
- **Approach (a) mirror the lookup-failure asymmetry.** On store-initialization failure in `_dedup_context()`, distinguish non-retryable from retryable tools at the call site: non-retryable tools return `DispatchResult(is_error=True, error_type="dedup_store_error")` (fail closed); retryable tools set `dedup_state="store_error"` and proceed overlay-only. This keeps the fail-open intent for auto-replayable calls while closing the write-protection gap. Lowest blast radius; matches the existing path exactly.
- **Approach (b) fail fast at startup.** Surface the initialization failure so the process refuses to serve. Higher blast radius: non-retryable *and* retryable tools lose dedup entirely, and startup validation must be added. Only choose this if the owner wants a broken dedup store to be a hard startup error.
- Record the chosen approach and its blast-radius trade-off in the implementation procedure. Approach (a) is recommended: it preserves the documented fail-open intent for retries and closes the gap with minimal change.

**Baseline (Step 5):** radon rates `dispatch.py` helper functions A(1); `bandit -ll` reports no high/medium findings; `lint-imports` 6 kept / 0 broken; `dispatch.py` churn 2 changes in 30 days; `DispatchResult` is imported by all ten server modules plus `server.py` and `formatters.py` — a broad public runtime contract, so the change must preserve its shape.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step. Declare a release unit (see `### Release units` below) when a phase breaks existing callers or tests until another phase lands (for example a `NOT NULL` column added before its write path): one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be validated alone}`.

1. **Phase 1: Choose the failure mechanism and document it.** Decide approach (a) vs (b) (Requirements `REQ-001`/`REQ-002`); record the blast-radius trade-off in the implementation procedure. No file change yet.
2. **Phase 2: Apply the chosen fix in `scripts/mcp_servers/dispatch.py`.** Route the store-initialization failure through the non-retryable/retryable distinction matching the lookup-failure path (`REQ-001`/`REQ-002`/`REQ-003`). Keep `_dedup_disabled` semantics for retryable tools intact.
3. **Phase 3: Repair the tests.** Extend `tests/mcp_servers/test_mcp_dispatch.py` to assert the initialization-failure behavior for both tool classes; confirm the new assertion fails on current code (`REQ-004`).
4. **Phase 4: Deployment & verification.** Run the validation commands below; confirm the updated regression test fails pre-fix and passes post-fix.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/dispatch.py` | Unit | `uv run pytest tests/mcp_servers` | new and existing tests pass; updated test fails pre-fix |
| `scripts/mcp_servers/dispatch.py` | Static | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` | clean |
| Reference table | Static | `uv run python tools/generate_reference_table.py --check` | no drift |

## Risks
- **Risk:** failing non-retryable tools closed on init change could stall tool calls the fail-open design intended to keep flowing. → **Mitigation:** only non-retryable tools are affected; retryable tools still degrade overlay-only, preserving the original intent.
- **Risk:** broad public runtime contract (`DispatchResult` used by all ten servers) means a signature change would cascade. → **Mitigation:** do not change `DispatchResult`; only populate its existing fields.
- **Risk:** high churn file risk is low (2/30d) but the file is central. → **Mitigation:** re-verify target sections at Step 8 freeze against current content.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Choose the failure mechanism (a fail-closed asymmetry / b startup failure) | Pending | — | — | Open design decision in Design section |
| 2 | Apply the chosen fix in `dispatch.py` | In Progress | — | — | `_dedup_context` + caller; procedure generated |
| 3 | Repair the dedup store-failure tests | Pending | — | — | `test_mcp_dispatch.py` (companion of step 2) |
| 4 | Deployment & verification | Pending | — | — | run validation commands; test fails pre-fix |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261108-082130_01_scripts_mcp_servers_dispatch.py.md | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261107-132027_mcpstartup002_dedup-init-fail-open.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261107-213831
- **Related target files**: `scripts/mcp_servers/dispatch.py`, `tests/mcp_servers/test_mcp_dispatch.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-082130 -->
