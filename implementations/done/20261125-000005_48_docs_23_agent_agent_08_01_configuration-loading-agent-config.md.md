## Goal

Add the four shutdown keys to the per-key configuration reference so the deadline, the settle window, the termination confirm window, and the force-exit opt-in are documented with their code defaults and reload class (REQ-002: one configurable global deadline; REQ-011: configurable second-signal behavior).

## Scope
**Release unit**: R7-reporting-and-docs (Phase 7)

- In scope: a new per-key subsection in this document, the restart-required list, and the table row tally.
- Out of scope: the dataclass fields (row 17), the builder (row 18), and the entries in `config/agent.toml` (row 19).

## Assumptions

- The reference is a set of per-domain tables under `## Per-Key Reference (config/agent.toml)` (`docs/23_agent/agent_08_01_configuration-loading-agent-config.md:67`), each with the columns `Key name`, `Reading component`, `Value type`, `Unit`, `Code default`, `Reload class` (for example `docs/23_agent/agent_08_01_configuration-loading-agent-config.md:105-125`).
- The default-value policy at `docs/23_agent/agent_08_01_configuration-loading-agent-config.md:94-101` requires the value written in `config/agent.toml` to equal the code default, which is what row 19 declares.
- The `ROWS: 77` tally line at `docs/23_agent/agent_08_01_configuration-loading-agent-config.md:214` counts the reference tables' data rows, so adding four rows changes it to 81.
- `### Settings Requiring Restart` (`docs/23_agent/agent_08_01_configuration-loading-agent-config.md:41-46`) lists keys named individually, so the four new keys belong there as `[RESTART]`.

## Step 3b verification against the current source (20261125-122600)

- Anchors hold: the per-key reference starts at `docs/23_agent/agent_08_01_configuration-loading-agent-config.md:67`, the restart list at `:41-46`, the `### MCP server definitions` table at `:203-213`, and the tally line was `ROWS: 77` at `:214` (now 81).
- Procedure step 3 exposed a Plan gap: `shutdown_termination_confirm_seconds` had no runtime consumer — `HttpServerLifecycleManager` built `ProcessTerminator()` with no arguments (`scripts/agent/http_lifecycle.py:84`) and the confirm window was the module default `_DEFAULT_KILL_CONFIRM_TIMEOUT_SEC = 2.0` (`scripts/agent/http_lifecycle_process_terminator.py:37`). User decision 2026-11-25: wire the key. `scripts/agent/factory.py:133-138` now injects `ProcessTerminator(kill_confirm_timeout_sec=ctx.cfg.shutdown_termination_confirm_seconds)` through the new optional keyword-only `process_terminator` on `_ServerLifecycleRouter` (`scripts/agent/lifecycle_router.py:160-169`) and `_SubprocessLifecycleManager` (`:57-72`), which `HttpServerLifecycleManager` already accepted. Pinned by `TestTerminatorConfirmWindowWiring` in `tests/agent/test_agent_factory.py`.
- The reading components in the new table name those consumers: `ShutdownBudget` is built in `scripts/agent/repl.py:89-91`, `shutdown_settle_seconds` is read by `ResourceShutdownCoordinator` (`scripts/agent/resource_shutdown_coordinator.py:265`), and `shutdown_force_exit_on_second_sigint` is read at `SignalHandler` construction (`scripts/agent/signal_handler.py:102`).

## Design decisions

- Add one `### Shutdown and termination` subsection rather than spreading the four keys across existing tables: they are sequence-wide settings read by different components, and a shared subsection states that they belong together.
- State the code default, not the deployed value, per the policy at `docs/23_agent/agent_08_01_configuration-loading-agent-config.md:99-101`.
- Mark all four `[RESTART]`: they are read into `AgentConfig` at startup and no reload path re-arms a live budget, which is also the assumption the cliplc005 Plan builds on.
- Compatibility impact: documentation only.

## Alternatives considered

- Append the four keys to the `### Database and retention` table because two of them bound database steps — rejected: the deadline also bounds process termination, and a database-scoped table would imply a narrower scope than the keys have.

## Implementation
### Target file
`docs/23_agent/agent_08_01_configuration-loading-agent-config.md`

### Procedure
1. Add a `### Shutdown and termination` subsection after `### MCP server definitions` (`docs/23_agent/agent_08_01_configuration-loading-agent-config.md:203-213`) with the same six columns.
2. Add the four rows: `shutdown_deadline_seconds` (new) `float` seconds `45.0`; `shutdown_settle_seconds` (new) `float` seconds `10.0`; `shutdown_termination_confirm_seconds` (new) `float` seconds `2.0`; `shutdown_force_exit_on_second_sigint` (new) `bool` n/a `False`. All `[RESTART]`.
3. Name the reading component for each row as the component that consumes it: `ShutdownBudget` (new), `ResourceShutdownCoordinator`, `ShutdownCoordinator` in `scripts/agent/http_lifecycle_shutdown_coordinator.py` and `terminate_with_timeout()`, and `SignalHandler`.
4. Add the four keys to `### Settings Requiring Restart` (`docs/23_agent/agent_08_01_configuration-loading-agent-config.md:41-46`).
5. Update the tally line at `docs/23_agent/agent_08_01_configuration-loading-agent-config.md:214` from 77 to 81.

### Method

- One new table in the existing per-key style; no prose section is rewritten.

### Details

- The unit column uses `seconds` for the three windows and `n/a` for the boolean, matching how other booleans are tabulated in this document.

## Compatibility considerations

- Overlap: this file is also a target row of the frozen cliplc005 Plan (`plans/20261124-110935_cliplc005_staged-reload-transaction.md`), which documents the reload transaction on the same reference. `tools/plan_dependency_order.py` places this Plan first; re-run `tools/check_plan_target_overlaps.py` after each lands so the tally line is not double-counted.
- Runs after rows 17, 18 and 19: a documented key that the dataclass does not define would be rejected by production validation and by the consistency checker.

## Security considerations

- N/A: no secret or path is documented.

## Rollback considerations

- Revert this row's commit with rows 17, 18 and 19: the keys, the file entries, and their documentation are one unit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` | Docs | `uv run python tools/check_docs_quality.py` | No finding |
| `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` | Docs | `uv run python tools/check_docs_structure.py docs/23_agent/agent_08_01_configuration-loading-agent-config.md` | No finding |
| `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` | Docs | `uv run python tools/check_docs_content_policy.py` | No warning for the new rows |
| `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` | Consistency | `uv run python tools/check_docs_consistency.py --domain agent` | The four documented keys match `config/agent.toml` and `scripts/` |

## Completion criteria

- All four keys appear in the reference with the code defaults the dataclass declares, are listed as restart-required, and the consistency checker reports no key mismatch.

## Out of Scope

- The dataclass fields, the builder, the config file entries, and the shutdown sequence behavior (rows 45, 46).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the shutdown-key subsection, restart entries, and tally update | Completed | 20261125-130118 | 20261125-130118 | Phase 7 Shutdown and termination table added, restart list extended, ROWS 77 to 81; confirm key wired into ProcessTerminator via factory per user decision |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Completed | 20261125-130118 | 20261125-130118 | quality/structure/policy clean; targeted tests 140 passed |

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
- **Requirement ID**: REQ-002 (one configurable global deadline), REQ-011 (second-signal behavior)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `docs/23_agent/agent_08_01_configuration-loading-agent-config.md`