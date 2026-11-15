## Goal
Document the existing operational signal for durable dedup-store degradation so operators can recognize when dedup protection is degraded, without re-documenting the degradation behavior, the `record_pending` policy, or the protected-asset classification already frozen by `adrrev008` and `adrrev011`.

## Priority
Medium

## Scope
- **In-Scope**: Document the dedup-store degradation signal — the dispatcher `logger.warning()` calls emitted at store-init unavailability (`dispatch.py` L190), lookup failure (`dispatch.py` L334), and write failure (`dispatch.py` L215), together with the `dedup_state=store_error` result marker — as an operational detection method in the monitoring document.
- **Out-of-Scope**: Re-documenting the retry-class-dependent degradation behavior, the `record_pending`/post-open-write-failure policy, or the disposable-cache protected-asset claim (`adrrev008`). Adding a new structured metric or exporter (no metrics framework exists; OTel is trace-only and optional). Changing dedup/dispatch behavior. RAG audit emission and MCP authentication (`adrrev011`). Keyless side-effect rejection (sibling MCP route issue).
- **Dependencies**:
  - **Depends on**: `plans/done/20261110-230633_adrrev008_mcp-dedup-ownership.md` | phase all | `adrrev008` already documents the per-retry-class degradation behavior (`db_03_07` Replay Decision Table), the `record_pending` post-open-write-failure policy (ADR-004 L247-248), and the disposable-cache protected-asset/health-mechanism classification (ADR-008 Recovery Policy Matrix); this Plan cross-references those documents and does not re-document them. Closed plan (in `plans/done/`).

## Background
The issue asked to (1) document the retry-class-dependent degradation, (2) decide the `record_pending` failure policy, (3) add an operational signal for degradation, and (4) keep disabled-tool rejection distinct from executed-call audit. Adversarial verification against current source found that items (1), (2), and (4) are already implemented and documented by the completed plan `adrrev008` (`plans/done/20261110-230633_adrrev008_mcp-dedup-ownership.md`) and the frozen `adrrev011`:

- The `db_03_07` Replay Decision Table (L117-125) captures the per-retry-class behavior: `retryable` + store unavailable proceeds overlay-only with `store_error`; `non_retryable` + store unavailable fails closed (`dedup_store_error`).
- ADR-004 L247-248 registers both exceptions: the retryable fail-open (`store_error`) and the retryable post-open write-failure warning-only (the `record_pending` decision), each with rationale and a maintainer approval record.
- ADR-008 L134 and `db_03_07` L96-98, L144-145 classify `mcp_dedup.sqlite` as a disposable cache owned by the dispatcher, recovered by recreation, with non-retryable tools failing closed until an operator resolves the state.
- Audit separation is covered by `adrrev011` (RAG audit) and the `dedup_unreplayable`/`idempotency_key_reused` rejection paths documented in `db_03_07` L122-125 and `mcp_03_03` L51-62.

Only item (3) remains: the operational signal exists in code but is not documented.

## Problem
Operators cannot currently tell from documentation when dedup protection is degraded. The dispatcher logs a `WARNING` at each degradation point (store unavailable, lookup failed, write failed) and returns a `dedup_state=store_error` marker, but no document describes these as the operational signal for dedup degradation, so the documented degradation behavior in `db_03_07`/ADR-004 is not connected to a detectable operational signal.

## Reason for Change
The degradation behavior is documented but its operational signal is not. Connecting them closes the observability gap the issue tracks. This is Medium: the fail-closed path for non-retryable tools already exists, so this is documentation, not a safety fix.

## Implementation Intent
Confirm the three existing `logger.warning()` degradation signals and the `store_error` marker in `dispatch.py`, then record them as a detection method in the monitoring document, cross-referencing `db_03_07` (behavior), `mcp_03_03` (health mechanism), ADR-008 (protected-asset classification), and ADR-004 (failure-policy authority). No code change.

## Requirements
- `REQ-001`: The dedup-store degradation signal — the dispatcher `logger.warning()` calls for store-init unavailability (`dispatch.py` L190), lookup failure (`dispatch.py` L334), and write failure (`dispatch.py` L215), together with the `dedup_state=store_error` result marker — MUST be documented as an operational detection method so operators can recognize degraded dedup protection.

## Implementation Target Files
**Freeze status**: Frozen (`20261115-055932`; `check_workitem_structure.py` and
`check_plan_target_overlaps.py` both report No findings).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` | Modify | Add a detection/troubleshooting row documenting the dedup-degradation WARNING signals and the `store_error` marker so operators can recognize degraded dedup protection (REQ-001). | REQ-001 | Monitoring doc has a `Status | Detection Method | Action` table (L25-29) and a Troubleshooting table (L38-48); neither lists a dedup-degradation row. | none (doc) | Verified |

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
| `scripts/mcp_servers/dispatch.py` | Read L180-216 and L304-344 to quote the exact init/lookup/write degradation branches and confirm the `store_error` marker is returned on them. | `docs/23_agent/agent_10_05...md` (REQ-001) |
| `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Read the Replay Decision Table (L117-125) and Adoption Path (L139-145) to cross-reference the documented degradation behavior the signal implements. | `docs/23_agent/agent_10_05...md` (REQ-001) |
| `docs/22_mcp/mcp_03_03_transport-and-health.md` | Read the durable-dedup states (L51-62) to align the `store_error` / `dedup_store_error` wording with the transport health model. | `docs/23_agent/agent_10_05...md` (REQ-001) |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` (ADR-004) | Read L247-248 for the registered `record_pending`/write-failure exceptions defining which degrade paths are expected. | `docs/23_agent/agent_10_05...md` (REQ-001) |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` (ADR-008) | Read the Recovery Policy Matrix (L82-135) for the disposable-cache classification the signal reports on. | `docs/23_agent/agent_10_05...md` (REQ-001) |

## Acceptance Criteria
- `REQ-001`: The monitoring document lists the dedup-degradation WARNING signals (init availability, lookup, write) and the `dedup_state=store_error` marker as a detection method, with a pointer to `db_03_07` for the behavior and ADR-008 for the classification. (Acceptance criterion)

## Tests
N/A: documentation-only; no Python target. Run the documentation checkers for `REQ-001`.

## Documentation Impact
Yes. `REQ-001` drives a single edit to the monitoring document (`agent_10_05`), named via `docs/00_index.md` "Document References by Task" under the agent/operations domain. No other document requires modification: the degradation behavior, `record_pending` policy, and protected-asset claim are already documented by `adrrev008`.

## Assumptions
- The existing `logger.warning()` signals are an adequate operational signal; adding a structured metric/exporter is out of scope because no metrics framework exists and OTel is trace-only and optional.
- The monitoring document (`agent_10_05`) is the correct home for the detection method; the behavior lives in `db_03_07` and the health mechanism in `mcp_03_03`.
- `adrrev008`'s classification (disposable cache, ADR-004 as failure-policy authority) remains current.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether to enhance the signal (e.g. a structured counter) rather than document the existing log warnings. | None yet — a judgment call; the issue's acceptance criterion permits "a recorded decision explains why not." | Record in the Plan that the existing log-warning signal suffices; do not build a metrics framework. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` | Modify | Low (operations doc read by operators) | N/A | N/A | not applicable (rsynced) |

## Design
Path A classification: ≤3 files, no public/runtime interface change, no DB schema change. The remaining scope after adversarial verification is a documentation-only edit; the degradation behavior, `record_pending` policy, and protected-asset claim are already frozen by `adrrev008`/`adrrev011`, so this Plan only connects the existing operational signal to the monitoring document. The one open choice (UNK-01) is where to document the signal and whether to add a new metric: the existing `logger.warning()` calls are sufficient, and no metrics framework exists to extend, so the Plan documents the existing log-warning signal rather than introducing a metric.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or
tests until another phase lands (for example a `NOT NULL` column added before its write path):
one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be
validated alone}`.

1. **Phase 1: Document the dedup-degradation operational signal**
   - [ ] Confirm the three `logger.warning()` degradation signals and the `store_error` marker in `scripts/mcp_servers/dispatch.py` L180-216, L304-344 (`REQ-001`).
   - [ ] Add a detection/troubleshooting row to `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` listing the init/lookup/write WARNING signals and the `dedup_state=store_error` marker, cross-referencing `db_03_07` (behavior) and ADR-008 (classification); describe the signal by level and trigger without quoting concrete log strings or config values (`REQ-001`).

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` | Documentation structure / consistency / content policy | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain agent`, `uv run python tools/check_docs_japanese.py` | Pass; English only; no implementation-detail content; no Japanese |

## Risks
- **Risk**: Editing `agent_10_05` while another active Plan references the same file. → **Mitigation**: run `check_plan_target_overlaps.py` after freeze; no active Frozen Plan targets this doc (verified at Step 3).
- **Risk**: Over-documenting behavior already in `db_03_07`/ADR-008, duplicating `adrrev008`. → **Mitigation**: reference those documents instead of restating the behavior; keep the edit scoped to the signal/detection method only.
- **Risk**: Recording concrete log message text or configuration values violates the Docs content policy. → **Mitigation**: describe the signal by level and trigger, not by quoting exact strings or config keys; follow `skills/DESIGN.md` Docs content policy.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Document the dedup-degradation operational signal | Completed | — | 20261115-203139 | REQ-001; single doc edit to `agent_10_05`; no code change. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|---------|
| `implementations/20261115-055932_01_docs_23_agent_agent_10_05_operations-and-observability-monitoring.md.md` | 1 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261111-163849_mcpsec002_dedup-degradation-security-docs.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-055932
- **Related target files**: `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem (undocumented operational signal); Required Changes (emit degradation signal); Acceptance Criteria (degradation event documented) | `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` | 1 | Dedup-degradation WARNING signals + `store_error` marker documented as a detection method | `check_docs_consistency.py --domain agent`, `check_docs_content_policy.py` | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261115-055932 -->
