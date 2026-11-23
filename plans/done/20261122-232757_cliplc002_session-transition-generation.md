## Goal
- Make session transitions generation-safe: introduce a monotonically increasing session generation and one atomic `SessionTransitionService` for `/clear new` and `/session load`, bind title and background results to the session and generation that created them, take one immutable persistence snapshot for shutdown and pre-transition finalization, and make `/clear` and `/undo` semantics explicit, so a transition either commits completely or leaves the old session intact.

## Priority
High

## Scope
- **In-Scope**: session generation and `SessionTarget`; `SessionTransitionService` (idle check, snapshot, finalize old-session Memory and diagnostics, temporary build, atomic commit, rollback) used by `/clear new` and `/session load`; generation-safe title and background tasks with per-session `title_pending`; `BgTaskMonitor` registration by task type, instance id, session id, and generation, and log redaction; `SessionPersistenceSnapshot` for shutdown; `/clear` kept as a temporary in-memory reset (owner decision 2026-11-22) with explicit wording and docs; `/undo` reload failure made explicit; separate fetched, synthesized, dropped, and restored counts; separate title storage and display limits; docs and tests.
- **Out-of-Scope**: maintenance jobs (cliplc003); the bounded shutdown state machine (cliplc004); strict turn persistence (cliplc010); making `/clear` delete persisted messages or renaming the command; command parsing and export (cliplc011).
- **Dependencies**: The REPL input controller Plan (cliplc001) is complete, so its corrected input model is available. This Plan blocks the maintenance-job, bounded-shutdown, and strict-turn-persistence Plans (cliplc003, cliplc004, cliplc010). Open Issues cliplc003 and cliplc011 also name `cmd_session.py`, and cliplc004, cliplc009, and cliplc013 name `session_persister.py`; the overlaps are compatible and this Plan should land first.

## Background
Source: consolidated CLI REPL and MCP lifecycle backlog, Issue 2. Current source (checked in Step 2): `/clear` resets `ctx.conv.history` and statistics only and never touches persisted rows (`scripts/agent/services/conversation_service.py:24-44`); `/clear new` calls `ctx.session.start()` without finalizing the old session; `restore_session` mutates history, undo floor, session id, correlation, and stats one after another (`scripts/agent/services/session_restore.py:155-223`); `AgentSession.set_title` writes to `self.session_id`, whichever session is current (`scripts/agent/session.py:215-230`); the title task is created in `ConversationStateManager.append_user_message` (`scripts/agent/conversation_state_manager.py:105-113`) from `on_first_turn=self._cmds._generate_session_title` (`scripts/agent/startup_component_init.py:124`); session persistence runs only at exit and reads state per step (`scripts/agent/repl.py:94-97,158`, `scripts/agent/session_persister.py`). The Issue's `scripts/agent/session_title.py` does not exist: title code is in `scripts/agent/commands/session_title.py` and `scripts/agent/services/session_title.py`. There is no session generation anywhere in the code. Archived siblings (restoresummary001, undo001, bgmonitor001) were not read (archive directories are not read by this workflow).

## Problem
- A new session can start without the old one being finalized (Memory extraction and diagnostics only run at exit), and a load can fail halfway with history already replaced.
- A title or background result that completes after a transition is applied to the current session because nothing records which session created the task.
- Shutdown persistence reads session id, history, turn id, and statistics at different times.
- `/clear` wording hides that persisted messages return on reload; a failed memory reload after an `/undo` DB delete leaves history and DB diverged without any message.
- Logs and the audit line carry title text and raw exception text.

## Reason for Change
Data-integrity risk across session boundaries; maintenance jobs, shutdown, and turn persistence need stable session ownership.

## Implementation Intent
Each session id change bumps a generation; a transition service takes a snapshot, builds the new state off to the side, finalizes the old session, commits all fields together, and rolls back on failure. Session-specific tasks carry an immutable target and are rejected when the generation changed. Persistence works from an immutable snapshot.

## Requirements
- `REQ-001`: `AgentSession` holds a monotonically increasing generation that changes on every session id change, and exposes an immutable `SessionTarget` (session id and generation).
- `REQ-002`: `SessionTransitionService` handles `/clear new` and `/session load`: requires an idle turn, snapshots id, generation, history, undo floor, correlation, and statistics, finalizes old-session Memory and diagnostics before switching, builds the restored state in a temporary structure, commits all fields together, and rolls back on failure.
- `REQ-003`: Idle means no turn persistence boundary is active; a transition requested while one is active is refused with an explicit reason.
- `REQ-004`: Title generation captures the session target at task creation, saves to that explicit target, rejects a stale-generation result, and keeps `title_pending` per target session.
- `REQ-005`: `BgTaskMonitor` registers each task with type, instance id, session id, and generation and groups failures by type; title text and raw failure reasons are removed from logs and audit.
- `REQ-006`: An immutable `SessionPersistenceSnapshot` (session id, generation, defensive-copy history, turn id, statistics) is used by shutdown for both Memory and diagnostics and by pre-transition finalization; persistence is rejected when the generation changed.
- `REQ-007`: `/clear` stays a temporary reset of in-memory conversation history (owner decision), says so in its messages and docs, `/clear new` goes through the service, and long-term Memory tables and JSONL are unchanged.
- `REQ-008`: A failed memory reload after an `/undo` DB delete is reported explicitly with a recovery hint; DB and in-memory history cannot silently diverge.
- `REQ-009`: Session load reports fetched, synthesized, dropped, and restored counts separately; title storage and display limits are separate constants.
- `REQ-010`: Documentation covers generations, transition semantics, `/clear` and `/undo` persistence behavior, and uses "in-memory conversation history" instead of the ambiguous "memory".

## Implementation Target Files
**Freeze status**: Frozen
Amended 2026-11-23 (fallout): added scripts/agent/commands/command_defs_list.py — REQ-002 fallout: SessionTransitionService.clear_new awaits old-session Memory finalization, so clear_conversation and _cmd_clear become async and registry.py rejects an async handler on a sync CommandDef
Amended 2026-11-23 (fallout): added tests/agent/test_session_correlation_refresh.py — REQ-002 fallout: the consumer scan missed this test; it calls clear_conversation synchronously and expects restore_session to mutate the context
Amended 2026-11-23 (fallout): added tests/agent/test_history_compression_consistency.py — REQ-002 fallout: test_compress_persist_restore_keeps_summary_drops_ephemeral assumes restore_session mutates the context

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/session.py | modify: add the session generation, a frozen `SessionTarget`, target-checked `set_title`, per-session title pending, and separate title storage and display limits | Session identity has no generation; `set_title` writes to whichever session is current | REQ-001, REQ-004, REQ-009; AC-2, AC-5 | `session.py:80,215-230` (`session_id` plain attribute, `set_title` uses `self.session_id`); `session.py:207-213` single `_title_pending` bool (checked in Step 2) | `tests/agent/test_agent_session.py` | Verified |
| scripts/agent/services/session_transition.py | create: new `SessionTransitionService` with snapshot, temporary build, atomic commit, rollback, and idle check for `/clear new` and `/session load` | New file. No transition service exists; `clear_conversation` and `restore_session` mutate state step by step | REQ-002, REQ-003; AC-1 | `conversation_service.py:24-44` and `session_restore.py:155-223` mutate history, id, correlation, stats sequentially (checked in Step 2) | `tests/agent/services/test_session_transition.py` | Verified |
| scripts/agent/session_persister.py | modify: add an immutable `SessionPersistenceSnapshot`, a capture method, snapshot parameters on both persist methods, and a generation check | Shutdown persistence reads session id, stats, and history at different times | REQ-006; AC-3 | `session_persister.py:59-80,187-217` (each method reads `ctx.session.session_id` and `ctx.conv.history` itself; checked in Step 2) | `tests/agent/test_session_persister.py` | Verified |
| scripts/agent/services/session_restore.py | modify: build the restored state without mutating the context and report fetched, synthesized, dropped, and restored counts | `restore_session` mutates history, undo floor, id, correlation, and stats in sequence with no rollback | REQ-002, REQ-009; AC-1, AC-5 | `session_restore.py:155-223` (`replace_history`, `undo_floor`, `session_id`, `refresh_session_correlation`, `reset_session_stats` in order; `n_messages` is the fetched count, comment at lines 219-222; checked in Step 2) | `tests/agent/test_session_restore.py` | Verified |
| scripts/agent/services/models.py | modify: extend `SessionRestoreResult` with separate fetched, synthesized, dropped, and restored counts | A single `n_messages` hides synthesized and dropped rows | REQ-009; AC-5 | `models.py:116-120` (`session_id`, `n_messages` only; checked in Step 3) | `tests/agent/test_session_restore.py` | Verified |
| scripts/agent/services/conversation_service.py | modify: route `/clear new` through the transition service and state in-memory history in the result messages | `/clear new` replaces the session without finalizing the old one and without rollback | REQ-002, REQ-007; AC-1, AC-4 | `conversation_service.py:24-44` (history cut, stats reset, `session.start()`, then `set_title`; checked in Step 2) | `tests/agent/services/test_conversation_service.py` | Verified |
| scripts/agent/services/undo_service.py | modify: make a failed memory reload after the DB delete an explicit error instead of silent divergence | `/undo` deletes from the DB first, then reloads on an ambiguous match; a failing `fetch_messages` leaves history diverged | REQ-008; AC-4 | `undo_service.py:88-110` (`fetch_messages` unguarded after `ctx.session.undo_last_turn()`; checked in Step 2) | `tests/agent/test_undo_db_memory_parity.py` | Verified |
| scripts/agent/bg_task_monitor.py | modify: register task type, instance id, session id, and generation; group failures by type; log exception class names, not raw reasons | Tasks are tracked only by function name; raw exception text is logged | REQ-005; AC-2 | `bg_task_monitor.py:73-95,126-150` (`task.get_name()` key; `%s` of `exc`; checked in Step 2) | `tests/agent/test_orchestrator_bg_failure_threshold.py` | Verified |
| scripts/agent/conversation_state_manager.py | modify: capture the session target when the first-turn title task is created and register the task with the monitor | The task is created without any session identity | REQ-004, REQ-005; AC-2 | `conversation_state_manager.py:105-113` (`asyncio.create_task(self._on_first_turn(line), name=...)`; creation point, checked in Step 2) | `tests/agent/test_orchestrator.py` | Verified |
| scripts/agent/services/session_title.py | modify: save the generated title to the captured target session, reject a stale generation, and keep the title text out of logs | `ctx.session.set_title(title)` writes to the current session; the title is logged with `%r` | REQ-004, REQ-005; AC-2 | `services/session_title.py:56-57` (checked in Step 2) | `tests/agent/services/test_session_title.py` | Verified |
| scripts/agent/commands/session_title.py | modify: use the captured target for pending state and the fallback title, and stop logging title text and raw failure reasons | The fallback title goes to the current session; the audit line carries the fallback text and exception | REQ-004, REQ-005; AC-2 | `commands/session_title.py:27-57` (`set_title_pending`, `set_title(fallback_title)`, audit `fallback=%r reason=%s`; checked in Step 2) | `tests/agent/commands/test_agent_cmd_session.py` | Verified |
| scripts/agent/commands/cmd_session.py | modify: load through the transition service, report the separate counts, and show title pending per session | `_load_session` calls `restore_session` directly and reports one count | REQ-002, REQ-009; AC-1, AC-5 | `cmd_session.py:250-269` (`restore_session` call and `n_messages` message); `:118` (`is_title_pending()`) (checked in Step 2) | N/A: covered by the own test row | Verified |
| scripts/agent/commands/cmd_context.py | modify: word `/clear` as in-memory conversation history and report an undo reload failure with a recovery hint | The `/clear` message says history cleared without saying persisted rows remain | REQ-007, REQ-008; AC-4 | `cmd_context.py:118-137` (checked in Step 2) | `tests/agent/commands/test_agent_cmd_context.py` | Verified |
| scripts/agent/repl.py | modify: capture one persistence snapshot at shutdown and pass it to both persist steps | Memory and diagnostics persistence read state at different times | REQ-006; AC-3 | `repl.py:94-97,158` (`_persist_session_state` calls the two methods in turn; checked in Step 2) | `tests/agent/test_repl.py` | Verified |
| docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md | modify: document `/clear` as an in-memory reset, `/clear new` and `/session load` transition semantics, counts, and `/undo` failure | Session category text predates generations and the transition service | REQ-010; AC-6 | `agent_07_07...md:34` (`/clear [new]` text; checked in Step 2) | N/A: documentation | Verified |
| docs/23_agent/agent_04_01_state-and-persistence-state-model.md | modify: document the session generation, the transition snapshot, and per-session title pending | State model has no generation concept | REQ-010; AC-6 | `agent_04_01...md` (session state model; checked in Step 3) | N/A: documentation | Verified |
| docs/23_agent/agent_04_02_state-and-persistence-history-compression.md | modify: update the reset table rows for `/clear` and session load | The lifetime table lists `/clear` resets without the persisted-row note | REQ-010; AC-6 | `agent_04_02...md:132-136` (checked in Step 2) | N/A: documentation | Verified |
| docs/23_agent/agent_14_reference-api-subpackages-generated.md | modify: regenerate the generated API table for the new transition service | Generated-block fallout of a new public module | REQ-010; AC-6 | `agent_14...md` lists `session_restore` and `conversation_service` (`rg -c`, checked in Step 3) | N/A: generated | Verified |
| docs/23_agent/agent_13_reference-api-generated.md | modify: regenerate the generated API table for `session.py` and `session_persister.py` symbols | Generated-block fallout of new public symbols | REQ-010; AC-6 | `generate_reference_table.py --check` after the code change (checked in Step 3) | N/A: generated | Verified |
| registry/manifests/agent_api.yaml | modify: regenerate the agent API contract manifest (generated by `tools/generate_reference_table.py --manifests`) | The manifest goes stale when public symbols change (observed after cliplc001) | REQ-010; AC-6 | `tools/generate_reference_table.py --check` reported this manifest stale after the previous change (checked in Step 3) | N/A: generated | Verified |
| tests/agent/services/test_session_transition.py | create: transition tests (load failure at every step, rollback, finalization, idle check, clear new) | New file; tests first | REQ-002, REQ-003, REQ-007; AC-1, AC-4 | New file; sibling `tests/agent/services/test_conversation_service.py` exists (checked in Step 3) | itself | Verified |
| tests/agent/test_agent_session.py | modify: generation increments, target-checked set_title, per-session pending, title limits | Tests follow the behavior change | REQ-001, REQ-004, REQ-009; AC-2, AC-5 | file exists (checked in Step 3) | itself | Verified |
| tests/agent/test_session_restore.py | modify: restore builds without mutating, separate counts, failure leaves the old session | Tests follow the behavior change | REQ-002, REQ-009; AC-1, AC-5 | file exists (checked in Step 3) | itself | Verified |
| tests/agent/test_session_persister.py | modify: snapshot immutability, one snapshot for both steps, stale generation rejected | Tests follow the behavior change | REQ-006; AC-3 | file exists (checked in Step 3) | itself | Verified |
| tests/agent/services/test_conversation_service.py | modify: `/clear new` finalizes the old session; long-term Memory unchanged | Tests follow the behavior change | REQ-007; AC-4 | file exists (checked in Step 3) | itself | Verified |
| tests/agent/test_undo_db_memory_parity.py | modify: reload failure after the DB delete is explicit | Tests follow the behavior change | REQ-008; AC-4 | `test_undo_db_memory_parity.py:245` `TestUndoReloadFallback` (checked in Step 2) | itself | Verified |
| tests/agent/test_orchestrator_bg_failure_threshold.py | modify: failures grouped by type; no raw reason logged | Tests follow the behavior change | REQ-005; AC-2 | file exists (checked in Step 3) | itself | Verified |
| tests/agent/test_orchestrator.py | modify: the title task is created with the captured session target | Tests follow the behavior change | REQ-004, REQ-005; AC-2 | file exists (checked in Step 3) | itself | Verified |
| tests/agent/services/test_session_title.py | modify: stale-generation title rejected; title not logged | Tests follow the behavior change | REQ-004, REQ-005; AC-2 | file exists (checked in Step 3) | itself | Verified |
| tests/agent/commands/test_agent_cmd_session.py | modify: load via the service, separate counts, fallback title to the captured target | Tests follow the behavior change | REQ-002, REQ-004, REQ-009; AC-1, AC-2, AC-5 | file exists (checked in Step 3) | itself | Verified |
| tests/agent/commands/test_agent_cmd_context.py | modify: `/clear` wording and undo reload failure message | Tests follow the behavior change | REQ-007, REQ-008; AC-4 | file exists (checked in Step 3) | itself | Verified |
| tests/agent/test_repl.py | modify: shutdown passes one snapshot to both persist steps | Tests follow the behavior change | REQ-006; AC-3 | file exists (checked in Step 3) | itself | Verified |
| `scripts/agent/commands/command_defs_list.py` | modify: declare `/clear` with `is_async=True` so its handler may await the transition service | REQ-002 fallout: SessionTransitionService.clear_new awaits old-session Memory finalization, so clear_conversation and _cmd_clear become async and registry.py rejects an async handler on a sync CommandDef | REQ-002 / N/A: none cites REQ-002 | `scripts/agent/commands/command_defs_list.py:144` (`CommandDef` for `/clear`); `scripts/agent/commands/registry.py:81-85` (is_async mismatch is rejected) | tests/agent/commands/test_agent_cmd_context.py | Verified |
| `tests/agent/test_session_correlation_refresh.py` | modify: await the now-async `clear_conversation` and follow the builder contract of `restore_session` | REQ-002 fallout: the consumer scan missed this test; it calls clear_conversation synchronously and expects restore_session to mutate the context | REQ-002 / N/A: none cites REQ-002 | `tests/agent/test_session_correlation_refresh.py:15,68` (sync `clear_conversation` call) and `TestFlowRefresh::test_restore_flow_refreshes_correlation` | itself | Verified |
| `tests/agent/test_history_compression_consistency.py` | modify: follow the builder contract of `restore_session` (apply the restored state through the transition service or the commit helper) | REQ-002 fallout: test_compress_persist_restore_keeps_summary_drops_ephemeral assumes restore_session mutates the context | REQ-002 / N/A: none cites REQ-002 | `tests/agent/test_history_compression_consistency.py::test_compress_persist_restore_keeps_summary_drops_ephemeral` (fails after restore_session became a builder) | itself | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/commands/mixin_base.py | `refresh_session_correlation` and `reset_session_stats` are reused by the transition | scripts/agent/services/session_transition.py, REQ-002 |
| scripts/agent/context.py | `ConversationState`, `ctx.turn.persistence_boundary`, `is_processing` | scripts/agent/services/session_transition.py, REQ-003 |
| scripts/agent/orchestrator.py | Constructs `BgTaskMonitor` and passes `on_first_turn` through unchanged | scripts/agent/conversation_state_manager.py, REQ-005 |
| scripts/agent/startup_component_init.py | Wires `on_first_turn` to `_generate_session_title` | scripts/agent/conversation_state_manager.py, REQ-004 |
| scripts/agent/session_message_repo.py | Message fetch and undo delete used by restore and undo | scripts/agent/services/undo_service.py, REQ-008 |
| scripts/agent/commands/registry.py | `/session` and `/clear` dispatch and the async handler rule | scripts/agent/commands/cmd_session.py, REQ-002 |

## Acceptance Criteria
- `AC-1` (REQ-002): A failed `/session load` leaves the previous session unchanged at every transition step, and `/clear new` finalizes the old session before switching.
- `AC-2` (REQ-004, REQ-005): An old-generation title or background result cannot mutate the new session; no title text or raw failure reason appears in logs or audit.
- `AC-3` (REQ-006): Shutdown Memory and diagnostics persistence use one snapshot, and persistence is rejected when the generation changed.
- `AC-4` (REQ-007, REQ-008): `/clear` behavior matches its documentation (in-memory reset, persisted rows and long-term Memory unchanged); `/undo` cannot leave DB and in-memory history silently divergent.
- `AC-5` (REQ-001, REQ-009): The generation increases on every session id change; load reports four separate counts; title storage and display limits are separate.
- `AC-6` (REQ-010): Docs describe generations, transitions, `/clear`, `/undo`, and the checkers in `rules/tool-gates.md` pass.

## Tests
- Load failure injected at every transition step with the previous session verified unchanged; `/clear new` finalization order (REQ-002).
- Title completion during `/clear new` and during `/session load`; stale-generation rejection; per-session pending (REQ-004).
- Monitor registration, grouping by type, and redaction of title text and raw reasons (REQ-005).
- Shutdown racing a transition; one snapshot for both persist steps; generation mismatch rejected (REQ-006).
- `/clear` followed by reload; long-term Memory tables and JSONL unchanged (REQ-007).
- Undo reload failure after the DB delete (REQ-008); separate counts (REQ-009).
- ruff, mypy, and the full test suite.

## Documentation Impact
Yes (REQ-010). Target docs are those named by `docs/00_index.md` "Document References by Task" for the agent session and state domains, listed in `Implementation Target Files`; the generated API tables and the agent API manifest are regenerated, not hand-edited.

## Assumptions
- Owner decision (2026-11-22): `/clear` stays a temporary reset of in-memory conversation history; persisted rows remain and return on reload; the command is not renamed and no DB deletion is added. Therefore there is no pre-delete state for `/undo` to recover, and the requirement to keep one is satisfied by the rows staying in the DB.
- The title task creation point is located (Step 2): `ConversationStateManager.append_user_message` creating the task from `on_first_turn`.
- The session target reaches the title task through a context variable set before `asyncio.create_task` (a task copies its creation context), so the `on_first_turn` callable signature and its pass-through in `orchestrator.py` and `audit_event_emitter.py` stay unchanged (`not affected`).
- Commands run serially inside the REPL loop, so no other LLM turn can run during a transition; the idle check is a guard (no active persistence boundary), not a lock.
- Overlaps with open Issues are compatible and this Plan precedes them; the open Issue overlaps are cliplc003, cliplc011 (`cmd_session.py`) and cliplc004, cliplc009, cliplc013 (`session_persister.py`).
- No schema change: generation is runtime state, titles use the existing column (persisted schema check: not applicable).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether `ctx.turn.persistence_boundary` is always None while a slash command runs | Only the field definition (`context.py:256`) and the serial loop were read | Verify in the procedure phase and test; fall back to refusing when a turn is active by another flag | False |
| UNK-02 | Whether a failed old-session Memory finalization should abort `/clear new` and `/session load` or only warn | No owner decision; shutdown treats it as non-fatal | Design warns and continues (data of the old session is already persisted); owner confirms at review | False |
| UNK-03 | Whether `on_session_stop` can run safely twice for one session (once at transition, again at exit if the session is reloaded later) | Memory layer idempotence not checked | Check `memory.on_session_stop` during the procedure phase; guard by finalized-session marker if needed | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/session.py | Modify | High | 8 | N/A | requires service restart (agent code) |
| scripts/agent/services/session_transition.py | Create | High | N/A: new file | N/A | requires service restart (agent code) |
| scripts/agent/session_persister.py | Modify | Medium | 4 | N/A | requires service restart (agent code) |
| scripts/agent/services/session_restore.py | Modify | High | 4 | N/A | requires service restart (agent code) |
| scripts/agent/services/models.py | Modify | Low | 5 | N/A | requires service restart (agent code) |
| scripts/agent/services/conversation_service.py | Modify | Medium | 1 | N/A | requires service restart (agent code) |
| scripts/agent/services/undo_service.py | Modify | Medium | 2 | N/A | requires service restart (agent code) |
| scripts/agent/bg_task_monitor.py | Modify | Medium | 4 | N/A | requires service restart (agent code) |
| scripts/agent/conversation_state_manager.py | Modify | Medium | 6 | N/A | requires service restart (agent code) |
| scripts/agent/services/session_title.py | Modify | Medium | N/A: generated | N/A | requires service restart (agent code) |
| scripts/agent/commands/session_title.py | Modify | Medium | 0 | N/A | requires service restart (agent code) |
| scripts/agent/commands/cmd_session.py | Modify | Medium | 2 | N/A | requires service restart (agent code) |
| scripts/agent/commands/cmd_context.py | Modify | Low | 0 | N/A | requires service restart (agent code) |
| scripts/agent/repl.py | Modify | Medium | 4 | N/A | requires service restart (agent code) |
| docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md | Modify | Low | 2 | N/A | none (documentation) |
| docs/23_agent/agent_04_01_state-and-persistence-state-model.md | Modify | Low | 5 | N/A | none (documentation) |
| docs/23_agent/agent_04_02_state-and-persistence-history-compression.md | Modify | Low | 4 | N/A | none (documentation) |
| docs/23_agent/agent_14_reference-api-subpackages-generated.md | Modify | Low | N/A: generated | N/A | none (documentation) |
| docs/23_agent/agent_13_reference-api-generated.md | Modify | Low | N/A: generated | N/A | none (documentation) |
| registry/manifests/agent_api.yaml | Modify | Low | N/A: generated | N/A | none (documentation) |
| tests/agent/services/test_session_transition.py | Create | Low | N/A: new file | N/A | none (tests) |
| tests/agent/test_agent_session.py | Modify | Low | 5 | N/A | none (tests) |
| tests/agent/test_session_restore.py | Modify | Low | 8 | N/A | none (tests) |
| tests/agent/test_session_persister.py | Modify | Low | 5 | N/A | none (tests) |
| tests/agent/services/test_conversation_service.py | Modify | Low | 1 | N/A | none (tests) |
| tests/agent/test_undo_db_memory_parity.py | Modify | Low | 2 | N/A | none (tests) |
| tests/agent/test_orchestrator_bg_failure_threshold.py | Modify | Low | 2 | N/A | none (tests) |
| tests/agent/test_orchestrator.py | Modify | Low | 27 | N/A | none (tests) |
| tests/agent/services/test_session_title.py | Modify | Low | 0 | N/A | none (tests) |
| tests/agent/commands/test_agent_cmd_session.py | Modify | Low | 4 | N/A | none (tests) |
| tests/agent/commands/test_agent_cmd_context.py | Modify | Low | 2 | N/A | none (tests) |
| tests/agent/test_repl.py | Modify | Low | 8 | N/A | none (tests) |
| `scripts/agent/commands/command_defs_list.py` | Modify | Not assessed (amendment 2026-11-23) | N/A | N/A | Not assessed (amendment 2026-11-23) |
| `tests/agent/test_session_correlation_refresh.py` | Modify | Not assessed (amendment 2026-11-23) | N/A | N/A | Not assessed (amendment 2026-11-23) |
| `tests/agent/test_history_compression_consistency.py` | Modify | Not assessed (amendment 2026-11-23) | N/A | N/A | Not assessed (amendment 2026-11-23) |

## Design
- **Generation**: `AgentSession` keeps `generation` (int, starts at 0) and bumps it inside `start` and in the transition commit; `capture_target()` returns `SessionTarget` (frozen: `session_id`, `generation`). `set_title(title, *, target=None)` writes only when the target matches the current id and generation, else returns False without a write; `title_pending` becomes per session id.
- **Title task identity**: `ConversationStateManager` sets a context variable to the captured target right before `asyncio.create_task`; `SessionTitleGen` and `SessionTitleService` read it. Alternative rejected: a new `on_first_turn(line, target)` signature (touches `orchestrator.py`, `audit_event_emitter.py`, and tests for no behavior gain).
- **Transition service**: `SessionTransitionService.load(ctx, session_id)` and `.clear_new(ctx)`: refuse when a turn boundary is active; `SessionTransitionSnapshot` of id, generation, history copy, undo floor, correlation id, statistics; finalize old session through `SessionPersister` with a `SessionPersistenceSnapshot`; build the new state (restore result or empty history) without touching the context; commit by assigning all fields together; on any failure restore the snapshot (including the session id and generation) and re-raise. `restore_session` becomes a builder returning the restored state plus counts.
- **Persistence snapshot**: frozen dataclass with a tuple copy of history; `persist_session_memories` and `persist_session_diagnostics` take an optional snapshot and reject one whose generation differs from the live generation; `repl.py` captures one snapshot and passes it to both.
- **BgTaskMonitor**: `register(task, task_type, session_id, generation)`; failures group by `task_type`; logs use the exception class name. The existing name-based keys stay valid for tasks registered without a type.
- **Undo**: if `fetch_messages` fails after the DB delete, raise `UndoReloadError` (defined in `undo_service.py`) carrying the deleted row count; `/undo` prints the error and tells the operator to run `/session load <id>`.
- **Counts and limits**: `SessionRestoreResult` gains `fetched`, `synthesized`, `dropped`, `restored`; `SESSION_TITLE_STORAGE_MAX_CHARS` and `SESSION_TITLE_DISPLAY_MAX_CHARS` replace the shared constant.
- **Consumer scan** (`tools/scan_change_consumers.py`, Step 3): `restore_session` (`cmd_session.py`), `SessionRestoreResult`, `clear_conversation` (`cmd_context.py`), `set_title` (`cmd_session.py`, both title modules, `conversation_service.py`), `is_title_pending` and `set_title_pending` (`cmd_session.py`, `commands/session_title.py`), `undo_last_turn`, `persist_session_memories` (`repl.py`), `on_first_turn` (`orchestrator.py`, `audit_event_emitter.py`, `startup_component_init.py`: `not affected: signature unchanged`). All other consumers are target rows.
- **Predictable fallout check** (Step 3): module size gate 24576 B: `session.py` 12216 B, `cmd_session.py` 11131 B, `session_persister.py` 9231 B, `session_restore.py` 9051 B are below it; the new service is its own module, so no split row. Pinned counts: none found. Tool inventory: no `tools/` change. Generated blocks: the two generated docs and the agent API manifest are rows. `repl.py` and the orchestrator tests mock the persister, so a new `capture_snapshot` call may need test doubles (Risks).
- **Complexity baseline** (radon): `persist_session_diagnostics` D (21), `_session_list` C (14), `_cmd_session` C (14); changes avoid adding branches to these and extract helpers.
- **Persisted schema check**: not applicable (no DDL, schema version, or migration).

## Implementation steps
Each checklist item cites `Implementation Target Files` rows. Tests are the first item of each phase.

1. **Phase 1: Session generation and target**
   - [ ] Write generation, target, per-session pending, and title limit tests (REQ-001, REQ-009; tests/agent/test_agent_session.py)
   - [ ] Add generation, `SessionTarget`, target-checked `set_title`, per-session pending, separate title limits (REQ-001, REQ-004, REQ-009; scripts/agent/session.py)
2. **Phase 2: Persistence snapshot**
   - [ ] Write snapshot and one-snapshot shutdown tests (REQ-006; tests/agent/test_session_persister.py, tests/agent/test_repl.py)
   - [ ] Add `SessionPersistenceSnapshot`, snapshot parameters, and the generation check (REQ-006; scripts/agent/session_persister.py)
   - [ ] Capture one snapshot at shutdown (REQ-006; scripts/agent/repl.py)
3. **Phase 3: Transition service and restore**
   - [ ] Write transition, rollback, and finalization tests first (REQ-002, REQ-003, REQ-007; tests/agent/services/test_session_transition.py, tests/agent/services/test_conversation_service.py, tests/agent/test_session_restore.py, tests/agent/commands/test_agent_cmd_session.py)
   - [ ] Extend the restore result with four counts (REQ-009; scripts/agent/services/models.py)
   - [ ] Turn `restore_session` into a state builder (REQ-002, REQ-009; scripts/agent/services/session_restore.py)
   - [ ] Create the transition service (REQ-002, REQ-003; scripts/agent/services/session_transition.py)
   - [ ] Route `/clear new` and `/session load` through it (REQ-002, REQ-007, REQ-009; scripts/agent/services/conversation_service.py, scripts/agent/commands/cmd_session.py, scripts/agent/commands/cmd_context.py)
   - [ ] modify: declare `/clear` with `is_async=True` so its handler may await the transition service (REQ-002; `scripts/agent/commands/command_defs_list.py`) — amendment 2026-11-23
   - [ ] modify: await the now-async `clear_conversation` and follow the builder contract of `restore_session` (REQ-002; `tests/agent/test_session_correlation_refresh.py`) — amendment 2026-11-23
   - [ ] modify: follow the builder contract of `restore_session` (apply the restored state through the transition service or the commit helper) (REQ-002; `tests/agent/test_history_compression_consistency.py`) — amendment 2026-11-23
4. **Phase 4: Title and background tasks**
   - [ ] Write stale-generation, redaction, and monitor tests (REQ-004, REQ-005; tests/agent/services/test_session_title.py, tests/agent/test_orchestrator_bg_failure_threshold.py, tests/agent/test_orchestrator.py)
   - [ ] Register and capture at task creation, then monitor registration (REQ-004, REQ-005; scripts/agent/conversation_state_manager.py, scripts/agent/bg_task_monitor.py)
   - [ ] Generation-safe title saving and redacted logs (REQ-004, REQ-005; scripts/agent/services/session_title.py, scripts/agent/commands/session_title.py)
5. **Phase 5: Undo**
   - [ ] Write the undo reload failure and `/clear` wording tests (REQ-007, REQ-008; tests/agent/test_undo_db_memory_parity.py, tests/agent/commands/test_agent_cmd_context.py)
   - [ ] Make the reload failure explicit (REQ-008; scripts/agent/services/undo_service.py)
6. **Phase 6: Documentation**
   - [ ] Update docs and regenerate the API tables and manifest (REQ-010; docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md, docs/23_agent/agent_04_01_state-and-persistence-state-model.md, docs/23_agent/agent_04_02_state-and-persistence-history-compression.md, docs/23_agent/agent_14_reference-api-subpackages-generated.md, docs/23_agent/agent_13_reference-api-generated.md, registry/manifests/agent_api.yaml)
7. **Phase 7: Deployment & Verification**
   - [ ] Run the validation sequence in `rules/toolchain.md` and the checkers in `rules/tool-gates.md`; then hand off to `skills/deploy/SKILL.md` (REQ-001 through REQ-010). Prerequisite: the change is committed and pushed first; deploying is the user's decision (approval gate).

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/session.py, tests/agent/test_agent_session.py | Unit | `uv run pytest tests/agent/test_agent_session.py -q` | Generation, target, pending, limits pass |
| scripts/agent/services/session_transition.py, session_restore.py, conversation_service.py | Unit + integration | `uv run pytest tests/agent/services tests/agent/test_session_restore.py tests/agent/commands/test_agent_cmd_session.py -q` | Failure at every step restores the old session |
| scripts/agent/session_persister.py, repl.py | Unit | `uv run pytest tests/agent/test_session_persister.py tests/agent/test_repl.py -q` | One snapshot, stale generation rejected |
| scripts/agent/bg_task_monitor.py, conversation_state_manager.py, title modules | Unit | `uv run pytest tests/agent -k "title or orchestrator or bg" -q` | Stale results rejected, no raw reasons logged |
| scripts/agent/services/undo_service.py | Unit | `uv run pytest tests/agent/test_undo_db_memory_parity.py -q` | Reload failure explicit |
| scripts/ | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports`, `uv run radon cc <changed> -s` | Clean; baseline findings only (vulture exit 3 and bandit baseline in unrelated files, Step 5); no complexity increase |
| Whole suite | Full | `uv run python tools/run_validation_gates.py --full`; `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | All pass; changed-line coverage at least 90% (diff-cover 10.3.0) |
| docs/ and registry/ | Checkers | `rules/tool-gates.md` "When to run which tool"; `uv run python tools/generate_reference_table.py --check` | No drift |

## Risks
- **Risk**: A transition failing after the old session was finalized leaves the old session finalized but still active → **Mitigation**: finalization is idempotent persistence of already-saved data, rollback restores every field, and UNK-03 checks double finalization.
- **Risk**: `capture_snapshot` breaks tests that mock the persister or context (`test_repl.py`, orchestrator tests) → **Mitigation**: snapshot parameters are optional, and those test files are target rows.
- **Risk**: The context-variable target is invisible at the call site → **Mitigation**: one documented helper sets and reads it; the Design records the rejected signature change.
- **Risk**: Overlap with open Issues on `cmd_session.py` and `session_persister.py` → **Mitigation**: changes are to different functions; this Plan precedes them; run `tools/check_plan_target_overlaps.py` after freeze.
- **Risk**: `persist_session_diagnostics` is already complexity D (21) → **Mitigation**: take the snapshot as input and extract helpers instead of adding branches.
- **Risk**: Blocking old-session Memory finalization slows `/clear new` and `/session load` → **Mitigation**: bounded by the existing memory client timeouts; failure only warns (UNK-02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Session generation and target | Completed | — | 20261123-123550 |  |
| 2 | Persistence snapshot | Completed | — | 20261123-123550 |  |
| 3 | Transition service and restore | Completed | — | 20261123-123522 |  |
| 4 | Title and background tasks | Completed | — | 20261123-123550 |  |
| 5 | Undo | Completed | — | 20261123-123550 |  |
| 6 | Documentation | Completed | — | 20261123-123550 |  |
| 7 | Deployment and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261123-094714_01_scripts_agent_session.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261123-094714_02_scripts_agent_services_session_transition.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261123-094714_03_scripts_agent_session_persister.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261123-094714_04_scripts_agent_services_session_restore.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261123-094714_05_scripts_agent_services_models.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261123-094714_06_scripts_agent_services_conversation_service.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261123-094714_07_scripts_agent_services_undo_service.py.md | 5 | Procedure | Pending | — | — |
| implementations/20261123-094714_08_scripts_agent_bg_task_monitor.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261123-094714_09_scripts_agent_conversation_state_manager.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261123-094714_10_scripts_agent_services_session_title.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261123-094714_11_scripts_agent_commands_session_title.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261123-094714_12_scripts_agent_commands_cmd_session.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261123-094714_13_scripts_agent_commands_cmd_context.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261123-094714_14_scripts_agent_repl.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261123-094714_15_docs_23_agent_agent_07_07_cli-and-commands-slash-commands-session-mcp.md.md | 6 | Procedure | Pending | — | — |
| implementations/20261123-094714_16_docs_23_agent_agent_04_01_state-and-persistence-state-model.md.md | 6 | Procedure | Pending | — | — |
| implementations/20261123-094714_17_docs_23_agent_agent_04_02_state-and-persistence-history-compression.md.md | 6 | Procedure | Pending | — | — |
| implementations/20261123-094714_18_docs_23_agent_agent_14_reference-api-subpackages-generated.md.md | 6 | Procedure | Pending | — | — |
| implementations/20261123-094714_19_docs_23_agent_agent_13_reference-api-generated.md.md | 6 | Procedure | Pending | — | — |
| implementations/20261123-094714_20_registry_manifests_agent_api.yaml.md | 6 | Procedure | Pending | — | — |
| implementations/20261123-094714_23_tests_agent_test_session_restore.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261123-094714_33_scripts_agent_commands_command_defs_list.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261123-094714_34_tests_agent_test_session_correlation_refresh.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261123-094714_35_tests_agent_test_history_compression_consistency.py.md | 3 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261119-145300_cliplc002_session-transition-generation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261122-232757
- **Related target files**: scripts/agent/session.py, scripts/agent/services/session_transition.py, scripts/agent/session_persister.py, scripts/agent/services/session_restore.py, scripts/agent/services/models.py, scripts/agent/services/conversation_service.py, scripts/agent/services/undo_service.py, scripts/agent/bg_task_monitor.py, scripts/agent/conversation_state_manager.py, scripts/agent/services/session_title.py, scripts/agent/commands/session_title.py, scripts/agent/commands/cmd_session.py, scripts/agent/commands/cmd_context.py, scripts/agent/repl.py, docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md, docs/23_agent/agent_04_01_state-and-persistence-state-model.md, docs/23_agent/agent_04_02_state-and-persistence-history-compression.md, docs/23_agent/agent_14_reference-api-subpackages-generated.md, docs/23_agent/agent_13_reference-api-generated.md, registry/manifests/agent_api.yaml, tests/agent/services/test_session_transition.py, tests/agent/test_agent_session.py, tests/agent/test_session_restore.py, tests/agent/test_session_persister.py, tests/agent/services/test_conversation_service.py, tests/agent/test_undo_db_memory_parity.py, tests/agent/test_orchestrator_bg_failure_threshold.py, tests/agent/test_orchestrator.py, tests/agent/services/test_session_title.py, tests/agent/commands/test_agent_cmd_session.py, tests/agent/commands/test_agent_cmd_context.py, tests/agent/test_repl.py, scripts/agent/commands/command_defs_list.py, tests/agent/test_session_correlation_refresh.py, tests/agent/test_history_compression_consistency.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes / evidence in Implementation Target Files | scripts/agent/session.py | Phase 1 | AC-2 | `tests/agent/test_agent_session.py` | Confirmed by repository evidence |
| REQ-004 | Issue Required Changes / evidence in Implementation Target Files | scripts/agent/session.py | Phase 1 | AC-2 | `tests/agent/test_agent_session.py` | Confirmed by repository evidence |
| REQ-009 | Issue Required Changes / evidence in Implementation Target Files | scripts/agent/session.py | Phase 1 | AC-2 | `tests/agent/test_agent_session.py` | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes / evidence in Implementation Target Files | scripts/agent/services/session_transition.py | Phase 3 | AC-1 | `tests/agent/services/test_session_transition.py` | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes / evidence in Implementation Target Files | scripts/agent/services/session_transition.py | Phase 3 | AC-1 | `tests/agent/services/test_session_transition.py` | Confirmed by repository evidence |
| REQ-006 | Issue Required Changes / evidence in Implementation Target Files | scripts/agent/session_persister.py | Phase 2 | AC-3 | `tests/agent/test_session_persister.py` | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes / evidence in Implementation Target Files | scripts/agent/services/session_restore.py | Phase 3 | AC-1 | `tests/agent/test_session_restore.py` | Confirmed by repository evidence |
| REQ-009 | Issue Required Changes / evidence in Implementation Target Files | scripts/agent/services/session_restore.py | Phase 3 | AC-1 | `tests/agent/test_session_restore.py` | Confirmed by repository evidence |
| REQ-009 | Issue Required Changes / evidence in Implementation Target Files | scripts/agent/services/models.py | Phase 3 | AC-5 | `tests/agent/test_session_restore.py` | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes / evidence in Implementation Target Files | scripts/agent/services/conversation_service.py | Phase 3 | AC-1 | `tests/agent/services/test_conversation_service.py` | Confirmed by repository evidence |
| REQ-007 | Issue Required Changes / evidence in Implementation Target Files | scripts/agent/services/conversation_service.py | Phase 3 | AC-1 | `tests/agent/services/test_conversation_service.py` | Confirmed by repository evidence |
| REQ-008 | Issue Required Changes / evidence in Implementation Target Files | scripts/agent/services/undo_service.py | Phase 5 | AC-4 | `tests/agent/test_undo_db_memory_parity.py` | Confirmed by repository evidence |
| REQ-005 | Issue Required Changes / evidence in Implementation Target Files | scripts/agent/bg_task_monitor.py | Phase 4 | AC-2 | `tests/agent/test_orchestrator_bg_failure_threshold.py` | Confirmed by repository evidence |
| REQ-004 | Issue Required Changes / evidence in Implementation Target Files | scripts/agent/conversation_state_manager.py | Phase 4 | AC-2 | `tests/agent/test_orchestrator.py` | Confirmed by repository evidence |
| REQ-005 | Issue Required Changes / evidence in Implementation Target Files | scripts/agent/conversation_state_manager.py | Phase 4 | AC-2 | `tests/agent/test_orchestrator.py` | Confirmed by repository evidence |
| REQ-004 | Issue Required Changes / evidence in Implementation Target Files | scripts/agent/services/session_title.py | Phase 4 | AC-2 | `tests/agent/services/test_session_title.py` | Confirmed by repository evidence |
| REQ-005 | Issue Required Changes / evidence in Implementation Target Files | scripts/agent/services/session_title.py | Phase 4 | AC-2 | `tests/agent/services/test_session_title.py` | Confirmed by repository evidence |
| REQ-004 | Issue Required Changes / evidence in Implementation Target Files | scripts/agent/commands/session_title.py | Phase 4 | AC-2 | `tests/agent/commands/test_agent_cmd_session.py` | Confirmed by repository evidence |
| REQ-005 | Issue Required Changes / evidence in Implementation Target Files | scripts/agent/commands/session_title.py | Phase 4 | AC-2 | `tests/agent/commands/test_agent_cmd_session.py` | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes / evidence in Implementation Target Files | scripts/agent/commands/cmd_session.py | Phase 3 | AC-1 | covered by the test rows | Confirmed by repository evidence |
| REQ-009 | Issue Required Changes / evidence in Implementation Target Files | scripts/agent/commands/cmd_session.py | Phase 3 | AC-1 | covered by the test rows | Confirmed by repository evidence |
| REQ-007 | Issue Required Changes / evidence in Implementation Target Files | scripts/agent/commands/cmd_context.py | Phase 5 | AC-4 | `tests/agent/commands/test_agent_cmd_context.py` | Confirmed by repository evidence |
| REQ-008 | Issue Required Changes / evidence in Implementation Target Files | scripts/agent/commands/cmd_context.py | Phase 5 | AC-4 | `tests/agent/commands/test_agent_cmd_context.py` | Confirmed by repository evidence |
| REQ-006 | Issue Required Changes / evidence in Implementation Target Files | scripts/agent/repl.py | Phase 2 | AC-3 | `tests/agent/test_repl.py` | Confirmed by repository evidence |
| REQ-010 | Issue Required Changes / evidence in Implementation Target Files | docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md | Phase 6 | AC-6 | covered by the test rows | Confirmed by repository evidence |
| REQ-010 | Issue Required Changes / evidence in Implementation Target Files | docs/23_agent/agent_04_01_state-and-persistence-state-model.md | Phase 6 | AC-6 | covered by the test rows | Confirmed by repository evidence |
| REQ-010 | Issue Required Changes / evidence in Implementation Target Files | docs/23_agent/agent_04_02_state-and-persistence-history-compression.md | Phase 6 | AC-6 | covered by the test rows | Confirmed by repository evidence |
| REQ-010 | Issue Required Changes / evidence in Implementation Target Files | docs/23_agent/agent_14_reference-api-subpackages-generated.md | Phase 6 | AC-6 | covered by the test rows | Confirmed by repository evidence |
| REQ-010 | Issue Required Changes / evidence in Implementation Target Files | docs/23_agent/agent_13_reference-api-generated.md | Phase 6 | AC-6 | covered by the test rows | Confirmed by repository evidence |
| REQ-010 | Issue Required Changes / evidence in Implementation Target Files | registry/manifests/agent_api.yaml | Phase 6 | AC-6 | covered by the test rows | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes / evidence in Implementation Target Files | tests/agent/services/test_session_transition.py | Phase 3 | AC-1 | `tests/agent/services/test_session_transition.py` | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes / evidence in Implementation Target Files | tests/agent/services/test_session_transition.py | Phase 3 | AC-1 | `tests/agent/services/test_session_transition.py` | Confirmed by repository evidence |
| REQ-007 | Issue Required Changes / evidence in Implementation Target Files | tests/agent/services/test_session_transition.py | Phase 3 | AC-1 | `tests/agent/services/test_session_transition.py` | Confirmed by repository evidence |
| REQ-001 | Issue Required Changes / evidence in Implementation Target Files | tests/agent/test_agent_session.py | Phase 1 | AC-2 | `tests/agent/test_agent_session.py` | Confirmed by repository evidence |
| REQ-004 | Issue Required Changes / evidence in Implementation Target Files | tests/agent/test_agent_session.py | Phase 1 | AC-2 | `tests/agent/test_agent_session.py` | Confirmed by repository evidence |
| REQ-009 | Issue Required Changes / evidence in Implementation Target Files | tests/agent/test_agent_session.py | Phase 1 | AC-2 | `tests/agent/test_agent_session.py` | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes / evidence in Implementation Target Files | tests/agent/test_session_restore.py | Phase 3 | AC-1 | `tests/agent/test_session_restore.py` | Confirmed by repository evidence |
| REQ-009 | Issue Required Changes / evidence in Implementation Target Files | tests/agent/test_session_restore.py | Phase 3 | AC-1 | `tests/agent/test_session_restore.py` | Confirmed by repository evidence |
| REQ-006 | Issue Required Changes / evidence in Implementation Target Files | tests/agent/test_session_persister.py | Phase 2 | AC-3 | `tests/agent/test_session_persister.py` | Confirmed by repository evidence |
| REQ-007 | Issue Required Changes / evidence in Implementation Target Files | tests/agent/services/test_conversation_service.py | Phase 3 | AC-4 | `tests/agent/services/test_conversation_service.py` | Confirmed by repository evidence |
| REQ-008 | Issue Required Changes / evidence in Implementation Target Files | tests/agent/test_undo_db_memory_parity.py | Phase 5 | AC-4 | `tests/agent/test_undo_db_memory_parity.py` | Confirmed by repository evidence |
| REQ-005 | Issue Required Changes / evidence in Implementation Target Files | tests/agent/test_orchestrator_bg_failure_threshold.py | Phase 4 | AC-2 | `tests/agent/test_orchestrator_bg_failure_threshold.py` | Confirmed by repository evidence |
| REQ-004 | Issue Required Changes / evidence in Implementation Target Files | tests/agent/test_orchestrator.py | Phase 4 | AC-2 | `tests/agent/test_orchestrator.py` | Confirmed by repository evidence |
| REQ-005 | Issue Required Changes / evidence in Implementation Target Files | tests/agent/test_orchestrator.py | Phase 4 | AC-2 | `tests/agent/test_orchestrator.py` | Confirmed by repository evidence |
| REQ-004 | Issue Required Changes / evidence in Implementation Target Files | tests/agent/services/test_session_title.py | Phase 4 | AC-2 | `tests/agent/services/test_session_title.py` | Confirmed by repository evidence |
| REQ-005 | Issue Required Changes / evidence in Implementation Target Files | tests/agent/services/test_session_title.py | Phase 4 | AC-2 | `tests/agent/services/test_session_title.py` | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes / evidence in Implementation Target Files | tests/agent/commands/test_agent_cmd_session.py | Phase 3 | AC-1 | `tests/agent/commands/test_agent_cmd_session.py` | Confirmed by repository evidence |
| REQ-004 | Issue Required Changes / evidence in Implementation Target Files | tests/agent/commands/test_agent_cmd_session.py | Phase 3 | AC-1 | `tests/agent/commands/test_agent_cmd_session.py` | Confirmed by repository evidence |
| REQ-009 | Issue Required Changes / evidence in Implementation Target Files | tests/agent/commands/test_agent_cmd_session.py | Phase 3 | AC-1 | `tests/agent/commands/test_agent_cmd_session.py` | Confirmed by repository evidence |
| REQ-007 | Issue Required Changes / evidence in Implementation Target Files | tests/agent/commands/test_agent_cmd_context.py | Phase 5 | AC-4 | `tests/agent/commands/test_agent_cmd_context.py` | Confirmed by repository evidence |
| REQ-008 | Issue Required Changes / evidence in Implementation Target Files | tests/agent/commands/test_agent_cmd_context.py | Phase 5 | AC-4 | `tests/agent/commands/test_agent_cmd_context.py` | Confirmed by repository evidence |
| REQ-006 | Issue Required Changes / evidence in Implementation Target Files | tests/agent/test_repl.py | Phase 2 | AC-3 | `tests/agent/test_repl.py` | Confirmed by repository evidence |
| REQ-002 | Amendment 2026-11-23: REQ-002 fallout: SessionTransitionService.clear_new awaits old-session Memory finalization, so clear_conversation and _cmd_clear become async and registry.py rejects an async handler on a sync CommandDef | scripts/agent/commands/command_defs_list.py | Phase 3 | N/A: none cites REQ-002 | tests/agent/commands/test_agent_cmd_context.py | Confirmed by repository evidence |
| REQ-002 | Amendment 2026-11-23: REQ-002 fallout: the consumer scan missed this test; it calls clear_conversation synchronously and expects restore_session to mutate the context | tests/agent/test_session_correlation_refresh.py | Phase 3 | N/A: none cites REQ-002 | itself | Confirmed by repository evidence |
| REQ-002 | Amendment 2026-11-23: REQ-002 fallout: test_compress_persist_restore_keeps_summary_drops_ephemeral assumes restore_session mutates the context | tests/agent/test_history_compression_consistency.py | Phase 3 | N/A: none cites REQ-002 | itself | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261123-094714 -->
