# Work Plan: Complete Rollback Tracking for All MCP Server Types

## Goal

Track all started MCP servers regardless of transport type and ensure rollback cleans up all tracked servers during startup failure.

## Scope

**In-Scope:**
- Add tracking list for all started MCP servers in `StartupOrchestrator`
- Populate this list whenever any MCP server is started (both HTTP subprocess and stdio modes)
- Modify rollback handler to iterate over all tracked servers and shut down each one using appropriate lifecycle method

**Out-of-Scope:**
- Adding stdio-mode server support (this is about tracking what's already being started)
- Modifying the shutdown_all() method itself — only adding cleanup calls for stdio servers
- Changing the rollback trigger conditions

## Assumptions

1. The current `_spawned_subprocesses` list tracks only HTTP subprocess servers
2. stdio-mode servers are started elsewhere during the startup sequence and don't currently participate in rollback
3. There exists a way to identify and shut down stdio-mode servers during rollback

## Unknowns

| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | How are stdio-mode MCP servers started during the startup sequence? | Code search for stdio server startup | Search for stdio server instantiation | True |
| UNK-02 | Does stdio-mode server have a shutdown method available? | API inspection | Check stdio server lifecycle methods | True |
| UNK-03 | Where exactly do stdio servers get started during `_check_services()` or other startup steps? | Code flow analysis | Trace startup sequence for stdio references | True |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - `scripts/agent/startup.py` — add tracking list, modify rollback handler
  - `scripts/agent/lifecycle_protocol.py` — may need protocol extension for stdio shutdown
- **Blast Radius:** Rollback behavior changes; only affects failed startup scenarios
- **Risk Metrics:** High churn — startup.py has been modified frequently during development
- **Deploy Impact:** No deploy.sh changes required

## Implementation Steps

1. **Phase 1: Preparation (BLOCKED by unknowns)**
   - [ ] Search codebase for stdio-mode MCP server startup logic
   - [ ] Identify stdio server shutdown mechanism
   - [ ] Determine where stdio servers are created during startup sequence

2. **Phase 2: Core Logic Implementation**
   - [ ] Add `self._all_started_servers: list[tuple[str, McpServerConfig]] = []` to `__init__()`
   - [ ] Populate this list in `_start_servers()` alongside `_spawned_subprocesses`
   - [ ] If stdio servers exist, populate this list wherever they are started
   - [ ] Modify rollback handler to iterate over `self._all_started_servers`:
     ```python
     for key, cfg in self._all_started_servers:
         if cfg.transport == TransportType.HTTP:
             # Already handled by shutdown_all()
             pass
         else:
             # Call stdio-specific shutdown
             ...
     ```
   - [ ] Clear the tracking list after successful completion or rollback

3. **Phase 3: Deployment & Verification**
   - [ ] Run `ruff check scripts/agent/startup.py` to verify lint passes
   - [ ] Run `pytest tests/ -k startup --no-header -q` to verify existing tests pass
   - [ ] Verify no new mypy errors introduced

## Validation Plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/startup.py` | Integration test verifying stdio MCP servers are cleaned up during startup rollback | Manual verification once unknowns resolved | Correct rollback behavior |
| `scripts/agent/startup.py` | Integration test verifying HTTP subprocess servers are cleaned up during startup rollback | `pytest tests/test_startup*.py -v` | Tests pass |
| `scripts/agent/startup.py` | Unit test verifying tracking list is cleared after successful startup | `pytest tests/test_startup*.py -v -k tracking` | Tests pass |

## Risks & Mitigations

- **Risk:** stdio-mode server shutdown mechanism unknown → **Mitigation:** Defer this fix until stdio server lifecycle is understood; document as TODO
- **Risk:** Tracking list grows unbounded if servers aren't cleared → **Mitigation:** Ensure clearing happens in both success and failure paths
- **Risk:** Rollback order matters (HTTP vs stdio) → **Mitigation:** Document expected rollback order; implement in reverse order of start

## Traceability

- Workflow phase: requirement-to-plan
- Source issue: N/A
- Source requirement: requires/20260730-204440_require.md
- Source plan: N/A
- Source implementation procedure: N/A
- Generated at: 20260730-211610
- Related target files: scripts/agent/startup.py, scripts/agent/lifecycle_protocol.py
