## Goal

Replace the shutdown wording in the operations runbook with the bounded machine: the step list, the timeout bound, and the startup-rollback claims become the sequence, the configurable deadline, and the per-step outcomes the Plan installs (REQ-012: every step reported; AC-1).

## Scope
**Release unit**: R7-reporting-and-docs (Phase 7)

- In scope: the shutdown-step list, the startup-interrupt section, and the Known Limitations bullet in this document.
- Out of scope: the coordinator implementation (row 5), the termination surface (rows 11-15), and the generated reference tables (rows 53-55).

## Assumptions

- The shutdown-step list is the numbered block at `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md:81-85` (persist, WAL checkpoint, WAL backup, `shutdown_all()`, `http.aclose()`), with the persist-first rationale at `:87`.
- The startup-interrupt section is `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md:91-93`, which states that a shutdown requested during startup rolls the started servers back through `shutdown_all()` and exits with status 0.
- The Known Limitations bullet at `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md:162` states that the checkpoint and backup share one timeout bound that is "fixed in `ResourceShutdownCoordinator.close_resources()` and not configurable", and `:163` states how a rollback failure and unconfirmed servers are shown.
- The document has no "30 seconds" claim; the 30 s termination claim lives in `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` (row 50).

## Step 3b verification against the current source (20261125-122600)

- All anchors hold: the step list is `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md:81-85`, the startup-interrupt section `:91-93`, and the two Known Limitations bullets `:162-163`. The step names match `scripts/agent/shutdown_budget.py:30-37` exactly, and the outcome vocabulary matches `ShutdownOutcome` (`:62-73`).
- Procedure step 6 is corrected against the code: the rollback's failure and unconfirmed server keys are reported only through the console fatal lines in `StartupOrchestrator._rollback_servers()` (`scripts/agent/startup.py:147-165`), not as a coordinator step record. `ShutdownCoordinator.shutdown_all()` removes each process entry before terminating it (`scripts/agent/http_lifecycle_shutdown_coordinator.py:209-210`), so the coordinator's `terminate_lifecycles` step sees no server left after a rollback and records `completed`; an unconfirmed server keeps its pgid and stderr-log tracking for manual cleanup. The document states this relationship instead of promising a rollback step record.
- The deadline is a top-level key in `config/agent.toml:39` (`shutdown_deadline_seconds = 45.0`), not a section key; the rewritten bullet names the file, not a section.

## Design decisions

- State the sequence by step name and outcome, not by line of code: the runbook's job is what an operator can observe, and the step names are what the report prints.
- Keep the persist-first rationale at `:87` and restate it as a budgeted step that uses one snapshot (row 9), rather than deleting it: the reason persist must precede closing is unchanged.
- Replace the "not configurable" limitation with the configured deadline (`shutdown_deadline_seconds` (new)) and state what an abandoned step means, because the limitation the bullet records is the one this Plan removes.
- Keep the console warning wording for unconfirmed servers (Plan Unknowns UNK-04) and add the step record as the durable answer, so the document does not promise that the warning disappears.
- Compatibility impact: documentation only; no code or config is changed by this row.

## Alternatives considered

- Leave the Known Limitations bullet and add a note that the bound is now configurable — rejected: a limitation that no longer holds is a false claim in a runbook an operator follows during an incident.

## Implementation
### Target file
`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure
1. Replace the numbered step list at `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md:81-85` with the bounded sequence: `enter_shutdown` (new) arms the deadline and closes the write gate, then `settle_writers` (new), `persist_snapshot` (new), `checkpoint` (new), `backup` (new), `terminate_lifecycles` (new), `close_hooks` (new), and the report step.
2. State that each step records one outcome (`completed`, `timed_out`, `failed`, `not_started` (new), `outcome_unknown`) and that a step with no time left is recorded `not_started` (new) rather than skipped.
3. Update the `shutdown_all()` item: the servers whose exit was not confirmed are reported as an unconfirmed outcome on the `terminate_lifecycles` (new) record, and the console warning line stays.
4. Update the startup-interrupt section at `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md:91-93` to say the rollback `shutdown_all()` call is given the remaining deadline (row 16), keeping the exit-status-0 behavior unchanged.
5. Rewrite the Known Limitations bullet at `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md:162`: the bound is `shutdown_deadline_seconds` (new), one deadline shared by every step, and an abandoned step is recorded with its outcome instead of only logged.
6. Update `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md:163` so the rollback failure and the unconfirmed server keys are described as both a warning line and a step record.

### Method

- Rewrite the sentences in place; no new section is added, and the Keywords and Related Documents sections are untouched.

### Details

- The step names are written exactly as the report prints them, so an operator reading the console and an operator reading this document use the same words.

## Compatibility considerations

- Runs after rows 5, 6, 7, 11, 12, 13, 15 and 16: the document describes behavior those rows install, so writing it first would state a sequence the code does not perform.
- `docs/00_index.md` maps shutdown and lifecycle claims to this file, so the replacement wording here is the canonical statement for the sequence.

## Security considerations

- The rewritten wording names server keys and outcome categories only; no absolute path or exception text is added (REQ-013).

## Rollback considerations

- Revert this row's commit with the Phase 7 commit; the document is the only file it changes.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | Docs | `uv run python tools/check_docs_quality.py` | No finding |
| `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | Docs | `uv run python tools/check_docs_structure.py docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | No finding |
| `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | Docs | `uv run python tools/check_docs_content_policy.py` | No warning for the rewritten claims |
| `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | Consistency | `uv run python tools/check_docs_consistency.py --domain agent` | Documented shutdown claims match `scripts/` |

## Completion criteria

- No sentence in this document states a fixed non-configurable shutdown timeout, a checkpoint-before-settle order, or a shutdown step whose outcome is never reported.

## Out of Scope

- The coordinator and termination implementations, the configuration keys (row 48), and the generated reference tables (rows 53-55).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the shutdown-step list, startup-rollback, and Known Limitations wording | Completed | 20261125-130118 | 20261125-130118 | Phase 7 Runbook rewritten as the bounded step sequence; Step 3b note added |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Completed | 20261125-130118 | 20261125-130118 | quality/structure/policy clean; consistency shows only the pre-existing /db warning |

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
- **Requirement ID**: REQ-012 (every step reported)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`