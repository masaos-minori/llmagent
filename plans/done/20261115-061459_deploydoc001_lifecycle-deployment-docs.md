## Goal
Document the two genuine gaps in the Agent-managed MCP subprocess lifecycle documentation — the undefined failure cooldown and the undocumented invalid-transition handling — in the owning architecture document, resolving the issue's undecided invalid-transition decision against the behavior the code already implements.

## Priority
Medium

## Scope
- **In-Scope**:
  - Document the MCP subprocess failure cooldown (a fixed module-constant window that throttles automatic restart attempts after a failed start, during which `ensure_ready()` and `restart()` reject with a message naming the remaining time) in the "Lifecycle Implementation" section of `agent_02_runtime-architecture.md`.
  - Document the invalid-lifecycle-transition handling: an illegal transition raises `ValueError` from `assert_valid_transition`, `_set_state` logs a warning and still applies the new state (log-and-store), i.e. it does not reject the transition.
  - Add a concise PID/process-group ownership note: each subprocess runs in its own session and is tracked by process-group id; shutdown terminates the whole group.
- **Out-of-Scope**:
  - Changing lifecycle or deployment code (`scripts/agent/lifecycle_router.py`, `scripts/agent/lifecycle.py`, `scripts/agent/http_lifecycle.py`).
  - Documenting spawn, health probe, restart, and shutdown suppression: already present in `agent_02` (state machine L139-143, lifecycle delegation L175, shutdown suppression L177) and `agent_10_01` (startup, health poll, shutdown_all process-group termination); no edit required.
  - Aligning active database paths and recovery ownership across deployment and DB documents: covered by the completed plan `adrrev009` (Manual Recovery hardened in `agent_10_01`); no residual discrepancy found, so no edit required.
  - Adding a hand-maintained inventory of MCP binaries and service-unit definitions: `tools/generate_mcp_inventory.py` already generates the server inventory from live `config/agent.toml` (routing.md → "When to run which tool"); no doc currently hand-maintains such a table, so nothing to correct.
- **Dependencies**:
  - **Depends on**: `plans/done/20261110-233648_adrrev009_adr008-recovery-align.md` | phase all | this issue's "align database paths and recovery ownership" item was deferred to adrrev009 in the issue's Dependencies; adrrev009 landed and hardened the Manual Recovery procedure, so that item needs no further action. Sequencing-only note; not blocking.

## Background
Source: `memo-issue.md` (Issue C). The memo marked the evidence incomplete; this pass verified the lifecycle modules, the deployment scripts, and the current documentation against source.

- `Explicit in code`: the lifecycle is implemented across `scripts/agent/lifecycle_router.py` (`_ServerLifecycleRouter` coordinator: state tracking, failure cooldown, shutdown guard), `scripts/agent/lifecycle.py` (`LifecycleState` + `assert_valid_transition`), and `scripts/agent/http_lifecycle.py` (spawn, health-poll, restart, termination).
- `Explicit in code`: `deploy/` contains shell scripts (`deploy.sh`, `setup_services.sh`, `init_db.sh`, `start_agent.sh`, `build_binaries.sh`, `build_sqlite_vec.sh`, `load_env.sh`). There is no `deploy/systemd/`; service definitions use the OpenRC `conf.d/` layout (Gentoo `/etc/conf.d/<service>`), documented in `deployment_01` section 1.1 and 2.2a.
- `Explicit in code`: the failure cooldown is a module constant `_COOLDOWN_SECONDS` in `lifecycle_router.py`, and invalid transitions are handled by logging + applying the new state in `_set_state`.
- Related plan: `plans/done/20261110-233648_adrrev009_adr008-recovery-align.md` covers manual recovery for `workflow.sqlite` / `eventbus.sqlite` (the issue's DB-alignment item).

## Problem
The Agent-managed MCP subprocess lifecycle is documented unevenly. Spawn, health probe, restart, and shutdown suppression are described in `agent_02_runtime-architecture.md` and `agent_10_01_operations-and-observability-startup-and-health.md`, but two behaviors that operators actually encounter are not defined anywhere:

- The failure cooldown that throttles automatic restarts after a failed start is mentioned only by name ("cooldown rejections") in `agent_10_05_operations-and-observability-monitoring.md` L48, with no definition of its window, trigger, or the rejection message an operator sees (`MCP server <key> is restarting. Try again in Ns`).
- The handling of an invalid lifecycle-state transition is undocumented. The state machine itself is listed (`agent_02` L139-143), but whether an illegal transition is rejected or logged-and-applied is never stated, even though the code already decides it.

The issue also leaves Decision 1 (reject versus log-and-store for invalid transitions) open; the code already implements log-and-store, so recording it is an evidence correction, not a new decision.

## Reason for Change
Deployment and restart behavior drives operator actions. An operator who sees a cooldown rejection or an invalid-transition log entry has no document explaining what happened or why a restart is refused. The work is Medium because no confirmed wrong-action document was identified — the gap is missing definition, not incorrect guidance.

## Implementation Intent
Extend the existing "Lifecycle Implementation" section of `agent_02_runtime-architecture.md` (which already owns the `LifecycleState` enum, valid transitions, lifecycle delegation, and shutdown suppression) with two paragraphs: one for the failure cooldown and one for invalid-transition handling. Describe behavior, not implementation counts; reference the owning modules (`lifecycle_router.py`, `lifecycle.py`) without literal ports, configuration values, line numbers, or timer magnitudes. Record Decision 1 as the already-implemented log-and-store behavior.

## Requirements
- `REQ-001`: The "Lifecycle Implementation" section of `docs/23_agent/agent_02_runtime-architecture.md` MUST document (a) the failure cooldown that throttles automatic `ensure_ready()`/`restart()` attempts after a failed start, including that a rejection while it is active names the remaining time; (b) that an invalid lifecycle-state transition is logged and the new state still applied (log-and-store), not rejected; and (c) that each subprocess runs in its own session and is tracked by process-group id, with shutdown terminating the whole group.

## Implementation Target Files
**Freeze status**: Frozen (`20261115-061459`; `check_workitem_structure.py` reports No findings; `check_plan_target_overlaps.py` reports No findings).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|
| `docs/23_agent/agent_02_runtime-architecture.md` | Modify | Define the two undocumented lifecycle behaviors (failure cooldown, invalid-transition log-and-store) and add a PID/process-group ownership note in the "Lifecycle Implementation" section, which already owns the state machine and shutdown suppression. | REQ-001 | `lifecycle_router.py` defines `_COOLDOWN_SECONDS`, `_failed_starts`, `_in_cooldown()` (throttles `ensure_ready`/`restart`), and `StartSuppressedError`; `_set_state` catches `assert_valid_transition`'s `ValueError`, logs a warning, and still sets the new state (log-and-store). `agent_10_05` L48 mentions "cooldown rejections" without definition; no doc defines the cooldown window, the invalid-transition handling, or the session/pgid model. | none (doc) | Verified |

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
| `scripts/agent/lifecycle_router.py` | Source of the failure cooldown (`_COOLDOWN_SECONDS`, `_failed_starts`, `_in_cooldown`), the shutdown guard (`_shutting_down`, `StartSuppressedError`), and the invalid-transition handling (`_set_state` + `assert_valid_transition`). | `docs/23_agent/agent_02...` (REQ-001) |
| `scripts/agent/lifecycle.py` | `LifecycleState` enum and the legal-transition table backing `assert_valid_transition`. | `docs/23_agent/agent_02...` (REQ-001) |
| `scripts/agent/http_lifecycle.py` | Spawn, health-poll, restart, and process-group termination context that frames the cooldown/shutdown-suppression behavior. | `docs/23_agent/agent_02...` (REQ-001) |
| `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | Confirms spawn/health/shutdown are already documented at the operations level; read to avoid duplicating them. | `docs/23_agent/agent_02...` (REQ-001) |
| `docs/90_deployment/deployment_01_deployment.md` | Confirms the OpenRC `conf.d/` service-definition mechanism and that no systemd exists; read to close the issue's service-location unknown. | Context (no edit) |

## Acceptance Criteria
- The failure cooldown is defined once, in the owning document, including that it throttles automatic restarts and that a rejection while active names the remaining time. (REQ-001)
- The invalid-transition handling is recorded as log-and-store (logged, then the new state applied), matching `lifecycle_router.py::_set_state`. (REQ-001)
- No duplicate description of spawn, health probe, restart, or shutdown suppression is introduced. (REQ-001)
- `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_japanese.py`, and `check_docs_consistency.py --domain agent` pass. (REQ-001)

## Tests
Not required (documentation-only). Run `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`, and `uv run python tools/check_docs_consistency.py --domain agent`.

## Documentation Impact
Yes. `docs/23_agent/agent_02_runtime-architecture.md` changes under the agent domain (see `docs/00_index.md` "Document References by Task": runtime architecture and lifecycle under the agent domain). REQ-001 drives it. The edit extends an existing section, so it must not duplicate the spawn/health/restart/shutdown descriptions already present in `agent_02` and `agent_10_01`.

## Assumptions
- `agent_02_runtime-architecture.md`'s "Lifecycle Implementation" section is the correct owner for the cooldown and invalid-transition descriptions because it already documents the `LifecycleState` machine and shutdown suppression; the operations-level restatement belongs to `agent_10_01`, which is not edited here.
- Decision 1 (invalid transitions) is an evidence correction, not a governance-amending decision: the code already implements log-and-store, so documenting current behavior does not require a maintainer approval record (consistent with the precedent that documenting reconciliation is an evidence correction).
- The deployment doc's DB-path and recovery-ownership statements remain consistent with `scripts/db/config.py` and the adrrev009-hardened Manual Recovery; no residual discrepancy exists.
- The failure-cooldown magnitude is a module constant; the content policy forbids concrete timer magnitudes, so the plan describes the window behaviorally and references the module rather than stating its value.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether to state the cooldown's numeric magnitude (seconds) in the doc. | Content policy forbids concrete configuration/timer values; the rejection message surfaces the remaining time to the operator regardless. | Describe the window behaviorally ("a fixed cooldown window") and reference `lifecycle_router.py`; do not state the numeric magnitude. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/23_agent/agent_02_runtime-architecture.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path A: one documentation file, no interface/schema/deployment change. The only design
choice is document ownership: the failure cooldown and invalid-transition handling are
routing-layer behavior of `_ServerLifecycleRouter`/`lifecycle.py`, so they belong in the
runtime-architecture document that already owns the state machine and shutdown suppression
(`agent_02`), not in the operations runbook (`agent_10_01`), which would duplicate the
spawn/health/shutdown descriptions already there. Recording the invalid-transition decision
as log-and-store is an evidence correction (the code already behaves this way), so it needs
no maintainer approval record.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or
tests until another phase lands (for example a `NOT NULL` column added before its write path):
one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be
validated alone}`.

1. **Phase 1: Document the two lifecycle gaps in `docs/23_agent/agent_02_runtime-architecture.md`**
   - [ ] Add a paragraph to the "Lifecycle Implementation" section defining the failure cooldown: it throttles automatic `ensure_ready()`/`restart()` attempts after a failed start, and a rejection while it is active names the remaining time (REQ-001).
   - [ ] Add a paragraph recording the invalid-transition handling: an illegal transition raises `ValueError` from `assert_valid_transition`, `_set_state` logs a warning and still applies the new state (log-and-store), i.e. it is not rejected (REQ-001).
   - [ ] Add a concise PID/process-group ownership note: each subprocess runs in its own session and is tracked by process-group id; shutdown terminates the whole group (REQ-001).
2. **Phase 2: Verification**
   - [ ] Run the documentation and consistency checkers named in the Acceptance Criteria against `agent_02` and confirm they pass (REQ-001).

### Release units
N/A: no release unit.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/23_agent/agent_02...` | Structural/formatting rules | `uv run python tools/check_docs_quality.py` | Pass |
| `docs/23_agent/agent_02...` | File size, front matter, internal links | `uv run python tools/check_docs_structure.py` | Pass |
| `docs/23_agent/agent_02...` | Content policy (no implementation-detail content) | `uv run python tools/check_docs_content_policy.py` | Pass |
| `docs/23_agent/agent_02...` | English-only output language | `uv run python tools/check_docs_japanese.py` | Pass |
| `docs/23_agent/agent_02...` | Cross-domain claim consistency (cooldown/pgid vs code) | `uv run python tools/check_docs_consistency.py --domain agent` | Pass |

## Risks
- **Risk**: The content-policy checker (`check_docs_content_policy.py`) flags the cooldown description as an implementation-detail (a concrete timer magnitude or module-constant name) that should point to a canonical source instead. → **Mitigation**: describe the window behaviorally ("a fixed cooldown window"), never state its magnitude, and reference `lifecycle_router.py` by name only as the owner, per `skills/DESIGN.md` Docs content policy.
- **Risk**: The edit duplicates the spawn/health/restart/shutdown descriptions already in `agent_02` and `agent_10_01`. → **Mitigation**: scope the edit to the two undefined behaviors (cooldown, invalid-transition handling) plus a one-line pgid note; re-read the existing "Lifecycle Implementation" section before editing.
- **Risk**: High-churn doc risk — `agent_02` is edited by other plans. → **Mitigation**: re-read the file at implementation and re-run the doc checkers against `HEAD` before committing.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Document the failure cooldown and invalid-transition handling in `agent_02` | Completed | — | 20261115-203721 | Adds the cooldown definition, the log-and-store invalid-transition handling, and a PGID/shutdown note to the "Lifecycle Implementation" section (REQ-001). |
| 2 | Run documentation and consistency checkers | Completed | — | — | `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_japanese.py`, `check_docs_consistency.py --domain agent` (REQ-001). Docs-only cycle substitution per memo3: check_docs_quality, check_docs_structure, check_docs_content_policy, check_docs_japanese, check_docs_consistency --domain agent all Pass (20261115-203623). |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|---------|
| `implementations/20261115-061459_01_docs_23_agent_agent_02_runtime-architecture.md.md` | 1 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261111-163903_deploydoc001_lifecycle-deployment-docs.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-061459
- **Related target files**: `docs/23_agent/agent_02_runtime-architecture.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem (undefined cooldown + undocumented invalid-transition handling); Required Changes (document cooldown, record invalid-transition decision); Unresolved Questions (Decision 1) | `docs/23_agent/agent_02_runtime-architecture.md` | 1, 2 | Cooldown defined once; invalid-transition recorded as log-and-store; no duplicate spawn/health/restart/shutdown | `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent` | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261115-061459 -->