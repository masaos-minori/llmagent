## Goal

Document the two genuine gaps in the Agent-managed MCP subprocess lifecycle documentation in the owning architecture document: define the failure cooldown and the invalid-lifecycle-transition handling, and add a concise PID/process-group ownership note.

## Scope
**Release unit**: N/A: no release unit

- Covers `REQ-001`: three additions to the "Lifecycle Implementation" section of `docs/23_agent/agent_02_runtime-architecture.md` — (a) failure cooldown definition, (b) invalid-transition log-and-store handling, (c) process-group ownership note.

## Assumptions
- `agent_02`'s "Lifecycle Implementation" section is the correct owner: it already documents the `LifecycleState` enum, valid transitions, lifecycle delegation, and shutdown suppression (verified: section header at L173, delegation and suppression paragraphs present).
- Recording the invalid-transition decision (log-and-store) is an evidence correction: the code already implements it (verified: `scripts/agent/lifecycle_router.py` `_set_state` L156-178 catches `assert_valid_transition`'s `ValueError`, logs a warning, and still sets the new state). No maintainer approval record needed.
- Cooldown facts verified in `scripts/agent/lifecycle_router.py`: `_COOLDOWN_SECONDS` module constant (L30); a failed start records a timestamp in `_failed_starts` (L192); `_in_cooldown` throttles `ensure_ready` and `restart` (L230, L306); a rejection while active names the remaining seconds (L233); a successful start clears the failure record (L189).
- Process-group facts verified in `scripts/agent/http_lifecycle.py`: each subprocess is spawned with `start_new_session=True` and terminated via `os.killpg` (L55, L89); pgids are tracked per server in `_http_pgids` (L81).
- The cooldown is currently referenced but never defined in `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` ("cooldown rejections" in the Troubleshooting table); that file is not edited here.

## Design decisions
- Describe the cooldown window behaviorally ("a fixed cooldown window") and reference `agent/lifecycle_router.py` as the owner; do not state the numeric magnitude, ports, config values, or line numbers, per `skills/DESIGN.md` Docs content policy and UNK-01.
- Record Decision 1 as log-and-store exactly as implemented (evidence correction), not as a new governance decision.
- Extend the existing section with short paragraphs; do not restate spawn, health probe, restart, or shutdown suppression already present in `agent_02` and `agent_10_01`.

## Alternatives considered
- Placing the descriptions in the operations runbook `agent_10_01`: rejected — it already owns the operations-level startup/health/shutdown descriptions and would duplicate them; the cooldown and transition semantics are routing-layer behavior owned by the runtime-architecture document.

## Implementation
### Target file
- `docs/23_agent/agent_02_runtime-architecture.md`

### Procedure
1. Re-read the "Lifecycle Implementation" section (from the section header around L173) to confirm current content and avoid duplicating the existing state-machine, delegation, and shutdown-suppression text.
2. Add a failure-cooldown paragraph: after a failed start, a fixed cooldown window throttles automatic `ensure_ready` and `restart` attempts for that server; a rejection while the window is active names the remaining time; a successful start clears the cooldown state. Name `agent/lifecycle_router.py` as the owner without stating the window's magnitude.
3. Add an invalid-transition paragraph: an illegal transition raises `ValueError` from `assert_valid_transition` (legal table in `agent/lifecycle.py`), and the router's state setter logs a warning and still applies the new state (log-and-store); the transition is not rejected.
4. Add a concise PID/process-group note: each managed subprocess runs in its own session and is tracked by process-group id, and shutdown terminates the whole group (see the termination behavior already described for `shutdown_all` in `agent_10_01`).

### Method
- Prose paragraph additions to the existing section; no new tables; no code snippets; English only; no literal ports, config values, timer magnitudes, or line numbers.

### Details
- Do not quote the concrete rejection message text; state only that the rejection names the remaining time.
- Keep the shutdown-suppression sentence untouched; the cooldown paragraph is distinct from shutdown suppression (cooldown throttles automatic restarts after a failed start; suppression is post-shutdown).

## Compatibility considerations
- Documentation-only; no runtime interface change. `agent_10_05`'s existing "cooldown rejections" mention becomes resolvable via this definition; no edit to that file in this procedure.

## Security considerations
- N/A: documentation-only; closes an operator blind spot around restart throttling and invalid-transition log entries.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`, `uv run python tools/check_docs_consistency.py --domain agent` — all pass; content policy accepts the behavioral cooldown description (no numeric magnitude).

## Completion criteria
- The "Lifecycle Implementation" section defines the failure cooldown (throttling + remaining-time rejection), records invalid transitions as log-and-store, and carries a one-line process-group ownership note; no spawn/health/restart/shutdown duplication introduced; all five documentation checkers pass.

## Out of Scope
- Editing `scripts/agent/lifecycle_router.py`, `scripts/agent/lifecycle.py`, `scripts/agent/http_lifecycle.py`, `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md`, or `docs/90_deployment/deployment_01_deployment.md` (reference files). Stating the cooldown's numeric magnitude. Documenting spawn, health probe, restart, shutdown suppression, DB-path/recovery alignment (completed by adrrev009), or a hand-maintained MCP binary inventory (generated by `tools/generate_mcp_inventory.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add cooldown, invalid-transition, and process-group paragraphs to the "Lifecycle Implementation" section | Completed | 20261115-203330 | 20261115-203440 | REQ-001 Adversarial verification complete: stale_detector Pass; structure check Pass; plan_dependency_order ready (no gate); agent_02 'Lifecycle Implementation' section and LifecycleState enum confirmed; verified delegation to _ServerLifecycleRouter, _set_state log-and-store on invalid transition, cooldown gate on ensure_ready (ServerCooldownError) and restart, failed-start recording and clearing on success, http_lifecycle _http_pgids with start_new_session/os.killpg; agent_10_05 Troubleshooting cooldown row confirmed. Step 3b not needed: no procedure correction. Changed: docs/23_agent/agent_02_runtime-architecture.md - 3 paragraphs added to 'Lifecycle Implementation': cooldown rejection behavior (no numeric magnitude), advisory transition guard (log-and-store), process-group ownership note. |
| 2 | Run the five documentation and consistency checkers | Completed | 20261115-203540 | 20261115-203623 | Acceptance criteria: check_docs_quality, check_docs_structure, check_docs_content_policy, check_docs_japanese, check_docs_consistency --domain agent all Pass. Docs-only cycle substitution per memo3: full-suite tests not run. |

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
- **Requirement ID**: `REQ-001` (cooldown + invalid-transition + process-group note documented in `agent_02`)
- **Source issue**: `issues/20261111-163903_deploydoc001_lifecycle-deployment-docs.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-061459_deploydoc001_lifecycle-deployment-docs.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-061459
- **Related target files**: `docs/23_agent/agent_02_runtime-architecture.md`