## Goal
- Make one `ReplInputController` the sole owner of stdin (normal, multiline, tool-approval, Memory-delete and Memory-prune prompts), deliver each read result only to the request that started it, bind approvals and destructive confirmations to an immutable request, and make Ctrl-C act by state, so a stale `y`/`yes` can never approve a later operation.

## Priority
High

## Scope
- **In-Scope**: the controller and request model; reader delivery binding and discard semantics; removal of the direct `input()` in Memory delete/prune (handlers become async); render-only `CLIView`; approval request/operation binding with required-vs-optional preview metadata, HIGH fail-closed, an explicit MEDIUM fallback setting, masked static previews, one masker for dry-run output and errors, redact-before-truncate; approval audit fields (request id, preview source, fallback reason, outcome, no answer text); state-dependent Ctrl-C, SIGTERM/console-close graceful shutdown, Windows ctypes fallback fix, defined and tested optional double-Ctrl-C force exit; docs and tests for all of it.
- **Out-of-Scope**: session transitions (cliplc002); maintenance jobs and job cancellation wiring (cliplc003); shutdown deadline machine (cliplc004); command parsing and export (cliplc011); CLI docs consolidation (cliplc014); a real Windows console test (`不明`, only the control-event abstraction is tested).
- **Dependencies**: This Plan blocks the sessions-transition, maintenance-job, bounded-shutdown, and export-contract Plans (cliplc002, cliplc003, cliplc004, cliplc011). It touches files that the open Issues cliplc003 (`memory_data_ops.py`), cliplc012 (characterization tests of the delayed-input hand-off), cliplc014 (CLI docs), and mdqmcp007 (`tool_approval.py`, `tool_result_formatter.py`) also name, and files named by the unconsumed mcpdl003 procedures (`tool_approval.py`, `config_dataclasses.py`); the Issue's claim that no sibling touches these files is stale (see Assumptions). None of those is a prerequisite.

## Background
Source: consolidated CLI REPL and MCP lifecycle backlog, Issue 1. Current source (all checked in Step 2/3): `scripts/agent/stdin_reader.py` documents and implements delivery of a late line to "the newest pending request" (`_run` delivers to `self._waiter` read after the blocking `input()` returns, lines 104-109); `scripts/agent/commands/memory_data_ops.py:50` calls `input()` synchronously from sync handlers invoked by the async REPL; `scripts/agent/signal_handler.py:61-63` registers the same handler for SIGTERM and SIGINT; `CLIView.read_multiline` (`scripts/agent/cli_view.py:268-301`) returns accumulated text on timeout. `docs/23_agent/agent_07_05_cli-and-commands-repl-io.md:41` specifies the hand-off ("Hand-off After Timeout"). Archived siblings (cliview001, cliview002, repl001) were not read (archive directories are not read by this workflow); their effect is verified through current source and tests only.

## Problem
- A line arriving after its request timed out or was cancelled goes to the newest pending request, so a stale `y`/`yes` can answer a later approval or confirmation (`stdin_reader.py:104-109`; asserted by `tests/agent/test_stdin_reader.py::TestCancelledRequestDelivery`).
- `_confirm()` (`memory_data_ops.py:47-53`) is a second, blocking stdin reader that competes with the daemon reader and blocks the event loop.
- Ctrl-C always takes the shutdown path (`signal_handler.py:54-63`); a KeyboardInterrupt never reaches the input loop on Unix.
- Approval preview: raw `args` reach `build_preview` (`tool_approval.py:101`, and `mask_args` documents it is not applied to the approval preview, `tool_result_formatter.py:69-71`); dry-run text is truncated unmasked (`tool_approval.py:119,121`); a dry-run execution failure (`RuntimeError`/`OSError`) falls back to the static preview even for HIGH risk (`tool_approval.py:124-127,221-223`) while a dry-run error result fails closed (`:207-218`); the audit event carries no request id, preview source, or fallback reason (`shared/models.py:13-28`).
- The Windows ctypes fallback handler references `win32con.CTRL_CLOSE_EVENT` (`signal_handler.py:101`) but `win32con` is only imported in the branch whose `import win32api` just failed, so the callback raises `NameError` (Confirmed by repository evidence, Step 2).

## Reason for Change
Security and input-integrity risk on the approval boundary; later session, maintenance, shutdown, and command work must build on the corrected input model.

## Implementation Intent
Exactly one stdin read is active at a time; each completed read is delivered only to the waiter captured when it started; cancelled and timed-out results are discarded. Destructive confirmation and tool approval carry an immutable request id, risk level, and preview. Ctrl-C acts according to the active state. The view layer renders only. Blocking `input()` in a thread cannot be interrupted, so the design discards rather than cancels.

## Requirements
- `REQ-001`: `ReplInputController` is the sole stdin owner; every request has a unique `request_id`, `prompt_kind` (normal, multiline, tool-approval, memory-delete, memory-prune), creation time, operation id, and lifecycle state; at most one read is active; a destructive confirmation is refused while an older blocking read is unresolved.
- `REQ-002`: A completed read is bound to the waiter captured when it started; delivery to the newest waiter is removed; results of timed-out or cancelled requests are discarded; no direct `input()` call remains outside the single reader thread.
- `REQ-003`: Reads return the outcomes `completed`, `timed_out`, `cancelled`, `eof`, `shutdown`; partial multiline input is never auto-submitted (interactive: offer send, continue, discard; non-interactive: discard); `CLIView` keeps rendering only and holds no input-state policy.
- `REQ-004`: Memory delete and prune confirmation go through the controller as request-bound prompts; the handlers are async and no longer block the event loop.
- `REQ-005`: Tool approval is bound to request id and operation id; preview metadata states required versus optional; a failed required HIGH-risk preview fails closed (including dry-run execution failure); the MEDIUM static fallback is an explicit config setting.
- `REQ-006`: Static previews are built from masked arguments; dry-run output and error text pass the one shared secret masker; redaction happens before truncation; tokens, signed URLs, paths, and raw exceptions do not appear in approval prompts.
- `REQ-007`: The approval audit event records preview source, fallback reason, request id, and outcome, and never the answer text.
- `REQ-008`: Ctrl-C at a prompt discards the input, during a turn cancels the turn, and during a job requests job cancellation through a seam wired by the maintenance-job Plan; Ctrl-D and `/exit` shut down normally; SIGTERM and console close begin graceful shutdown; the Windows ctypes fallback is fixed; double-Ctrl-C force exit is defined, off by default, and tested.
- `REQ-009`: Documentation removes the delayed-input hand-off specification and documents the input outcomes, Ctrl-C semantics, the CLIView boundary, and approval fail-closed behavior.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/repl_input_controller.py | create: new module holding `ReplInputController`, request model, outcome enum, process-shared accessor | New file. A single owner of stdin does not exist; the reader, CLIView, and approval each hold their own entry point (checked in Step 3) | REQ-001, REQ-002, REQ-003; AC-1, AC-2, AC-3 | `get_stdin_reader` consumers: `cli_view.py:115`, `repl_input_loop.py:70`, `tool_approval.py:133` (`tools/scan_change_consumers.py`, checked in Step 3) | `tests/agent/test_repl_input_controller.py` | Verified |
| scripts/agent/stdin_reader.py | modify: bind delivery to the waiter captured at read start; discard late lines; keep one daemon thread | Remove newest-waiter delivery | REQ-002; AC-1 | `_run` re-reads `self._waiter` after `input()` returns (`stdin_reader.py:104-109`); docstring `:39-43` (checked in Step 2) | `tests/agent/test_stdin_reader.py` | Verified |
| scripts/agent/cli_view.py | modify: remove `read_multiline`, `Reader` protocol, `_INPUT_TIMEOUT_S`, the reader dependency | CLIView renders only | REQ-003; AC-3 | `cli_view.py:20,24,76-86,115,268-301` (checked in Step 2) | `tests/test_cli_view.py` | Verified |
| scripts/agent/repl_input_loop.py | modify: read lines and multiline continuation through the controller; map outcomes; Ctrl-C state reporting | Loop is the normal-prompt caller | REQ-001, REQ-003, REQ-008; AC-3, AC-5 | `repl_input_loop.py:70,137-200` (`_read_input` CC 11; `_repl_loop` CC 31, radon, checked in Step 5) | `tests/agent/test_repl.py` | Verified |
| scripts/agent/signal_handler.py | modify: state-dependent SIGINT, SIGTERM and console-close shutdown, ctypes fallback fix, optional force exit | SIGINT currently equals SIGTERM; ctypes handler references an unbound name | REQ-008; AC-5 | `signal_handler.py:54-63,101` (checked in Step 2) | `tests/agent/test_signal_handler.py` | Verified |
| scripts/agent/tool_approval.py | modify: request-bound approval, required/optional preview, HIGH fail-closed on any preview failure, masked static preview, mask before truncating dry-run text, audit provenance | Core of the approval boundary | REQ-005, REQ-006, REQ-007; AC-1, AC-4 | `tool_approval.py:91-136,205-227` (checked in Step 2) | `tests/agent/test_tool_approval_request_binding.py` | Verified |
| scripts/agent/tool_output.py | modify: render request id and preview provenance in the approval prompt through the one masker | Prompt rendering must not print unmasked text | REQ-005, REQ-006; AC-4 | `emit_approval_prompt` writes `preview` verbatim (`tool_output.py:34-40`, checked in Step 2) | `tests/agent/test_tool_approval_request_binding.py` | Verified |
| scripts/agent/tool_result_formatter.py | modify: correct the `mask_args` docstring that says masking is not applied to the approval preview; no behavior change expected | The documented gap becomes false | REQ-006; AC-4 | `tool_result_formatter.py:64-71` (checked in Step 2) | `tests/agent/test_tool_approval_request_binding.py` | Verified |
| scripts/agent/commands/memory_data_ops.py | modify: async delete/prune; replace `_confirm` with a controller request | Second stdin reader and event-loop block | REQ-001, REQ-004; AC-2 | `memory_data_ops.py:47-53,321-414` (checked in Step 2) | `tests/agent/commands/test_memory_data_ops.py` | Verified |
| scripts/agent/commands/cmd_memory.py | modify: `_cmd_memory` becomes async and awaits the async handlers | Handlers are called from a sync dispatch table | REQ-004; AC-2 | `cmd_memory.py:80-124`; the registry awaits coroutine handlers (`registry.py:139-154`, checked in Step 3) | `tests/agent/commands/test_cmd_memory.py` | Verified |
| scripts/agent/shared/models.py | modify: add request id, preview source, fallback reason to `ToolApprovalEvent` (defaulted) | Audit provenance | REQ-007; AC-4 | `shared/models.py:13-28` (checked in Step 3) | `tests/agent/test_tool_approval_request_binding.py` | Verified |
| scripts/agent/tool_audit.py | modify: `audit_approval` accepts and writes the new fields, never the answer text | Audit provenance | REQ-007; AC-4 | `tool_audit.py:111-148` (checked in Step 2) | `tests/agent/test_tool_approval_request_binding.py` | Verified |
| scripts/agent/config_dataclasses.py | modify: add the explicit MEDIUM preview-fallback field to `ApprovalConfig` | Explicit setting | REQ-005; AC-4 | `config_dataclasses.py:266-293`, precedent `gitops_push_blocked` (checked in Step 3) | `tests/agent/test_config_builders.py` | Verified |
| scripts/agent/config_section_builders.py | modify: build the new field with the default | Config build path | REQ-005; AC-4 | `config_section_builders.py:269,277` (checked in Step 3) | `tests/agent/test_config_builders.py` | Verified |
| scripts/agent/services/config_field_registry.py | modify: register the field and its reload class | Registry lists every approval field | REQ-005; AC-4 | `config_field_registry.py:87` (checked in Step 3) | `tests/agent/test_config_builders.py` | Verified |
| docs/23_agent/agent_07_02_cli-and-commands-cliview.md | modify: CLIView renders only; remove the `Reader` protocol claim | Responsibility boundary | REQ-009; AC-6 | Lines "Test Protocols" and "Presentation Layer Only" (checked in Step 2) | N/A: documentation | Verified |
| docs/23_agent/agent_07_05_cli-and-commands-repl-io.md | modify: remove the hand-off specification; document outcomes and Ctrl-C semantics | Stale hand-off specification | REQ-009; AC-6 | `agent_07_05...md:39,41,54` (checked in Step 2) | N/A: documentation | Verified |
| docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md | modify: document request binding and fail-closed preview behavior | Approval behavior changes | REQ-009; AC-6 | `agent_06_02...md:95,122` fail-closed list (checked in Step 3) | N/A: documentation | Verified |
| docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md | modify: document the new approval field | Config reference | REQ-009; AC-6 | `agent_08_04...md:107` (checked in Step 3) | N/A: documentation | Verified |
| docs/23_agent/agent_13_reference-api-generated.md | modify: regenerate the generated API table (`get_stdin_reader` rows, new symbols) | Generated-block fallout | REQ-009; AC-6 | `agent_13...md:139-140` (`tools/scan_change_consumers.py`, checked in Step 3) | N/A: generated, `generate_reference_table.py --check` | Verified |
| tests/agent/test_repl_input_controller.py | create: controller lifecycle, discard, outcomes, single reader | Tests first | REQ-001, REQ-002, REQ-003; AC-1, AC-2, AC-3 | New file; sibling `tests/agent/test_stdin_reader.py` exists (checked in Step 3) | itself | Verified |
| tests/agent/test_tool_approval_request_binding.py | create: stale-`y` crossover, consecutive approvals, preview and redaction, audit fields | Tests first; no `test_tool_approval.py` exists (five `test_tool_approval_*.py` siblings do) | REQ-005, REQ-006, REQ-007; AC-1, AC-4 | `ls tests/agent` (checked in Step 3) | itself | Verified |
| tests/agent/test_stdin_reader.py | modify: replace `test_line_after_cancel_goes_to_the_newest_request...` with the discard assertion | Inverts the hand-off test | REQ-002; AC-1 | `test_stdin_reader.py:87-118` (checked in Step 2) | itself | Verified |
| tests/test_cli_view.py | modify: replace `TestReadMultilineTimeout` | `read_multiline` leaves CLIView | REQ-003; AC-3 | `test_cli_view.py:151` (checked in Step 2) | itself | Verified |
| tests/agent/test_repl.py | modify: update prompt/Ctrl-C tests (`TestSignalDuringPromptEndsLoop`) and add timeout-then-approval, timeout-then-memory scenarios | Loop behavior changes | REQ-003, REQ-008; AC-3, AC-5 | `test_repl.py:849` (checked in Step 2) | itself | Verified |
| tests/agent/test_signal_handler.py | modify: state-dependent SIGINT, SIGTERM, control-event abstraction, ctypes fix, force exit | Signal semantics | REQ-008; AC-5 | `test_signal_handler.py:37-118` (checked in Step 2) | itself | Verified |
| tests/agent/commands/test_memory_data_ops.py | modify: replace `patch("builtins.input")` (lines 233, 391, 560) with the controller | `input()` is removed | REQ-004; AC-2 | grep (checked in Step 3) | itself | Verified |
| tests/agent/commands/test_cmd_memory.py | modify: await the async `_cmd_memory` | Handler becomes async | REQ-004; AC-2 | `rg "_cmd_memory\("` (checked in Step 3) | itself | Verified |
| tests/agent/commands/test_agent_cmd_memory.py | modify: await the async `_cmd_memory` | Handler becomes async | REQ-004; AC-2 | `rg "_cmd_memory\("` (checked in Step 3) | itself | Verified |
| tests/agent/test_config_builders.py | modify: default and override of the new approval field | Config field | REQ-005; AC-4 | `test_config_builders.py:278,322` (checked in Step 3) | itself | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/repl.py | Constructs `ReplInputLoop` and `SignalHandler`; the shared accessor keeps it unchanged | scripts/agent/signal_handler.py, REQ-008 |
| scripts/agent/secrets_masker.py | The one shared masker (`_mask_secrets`) used for dry-run text | scripts/agent/tool_approval.py, REQ-006 |
| scripts/agent/commands/registry.py | `_run_matched_command` awaits coroutine handlers | scripts/agent/commands/cmd_memory.py, REQ-004 |
| scripts/agent/tool_exceptions.py | `ApprovalPreviewError`, `ApprovalPreviewBlockingError` | scripts/agent/tool_approval.py, REQ-005 |
| scripts/agent/context.py | `shutdown_requested`, `is_processing` state | scripts/agent/repl_input_loop.py, REQ-008 |
| scripts/agent/tool_policy.py | `classify_risk`, `check_preflight` consumers in the approval path | scripts/agent/tool_approval.py, REQ-005 |
| .importlinter | Import contracts the new module must satisfy | scripts/agent/repl_input_controller.py, REQ-001 |

## Acceptance Criteria
- `AC-1` (REQ-001, REQ-002, REQ-005): A delayed `y` or `yes` from a timed-out or cancelled request cannot approve any later operation; only one stdin reader exists per process; consecutive approval requests with no answer cause no answer crossover.
- `AC-2` (REQ-001, REQ-004): Memory delete/prune confirmation cannot race with an existing read (it is refused while an older blocking read is unresolved) and does not block the event loop; no direct `input()` remains in `scripts/`.
- `AC-3` (REQ-003): Timed-out multiline input is never silently submitted; CLIView contains no input-state policy.
- `AC-4` (REQ-005, REQ-006, REQ-007): A required HIGH-risk preview cannot silently fall back (any preview failure denies); MEDIUM fallback follows the setting; tokens, signed URLs, paths, and raw exceptions do not appear in approval prompts; redaction precedes truncation; the audit event carries request id, preview source, fallback reason, outcome and no answer text.
- `AC-5` (REQ-008): Ctrl-C behavior depends on prompt, turn, job, or shutdown state; SIGTERM and console close begin graceful shutdown; the ctypes fallback no longer raises `NameError`; force exit is off by default and tested when on.
- `AC-6` (REQ-009): The hand-off specification is gone; outcomes, Ctrl-C semantics, the CLIView boundary, and fail-closed approval are documented; checkers in `rules/tool-gates.md` pass.

## Tests
- Stale-`y` crossover and Memory-confirmation race tests are written first (REQ-001, REQ-002, REQ-004).
- Multiline timeout followed by tool approval and by Memory confirmation; consecutive approval requests with no answer crossover (REQ-002, REQ-003).
- Ctrl-C and SIGTERM for every prompt kind; control-event abstraction for Windows events including the ctypes path (REQ-008).
- Required versus optional preview failure by risk level; HIGH fails closed on dry-run error and on dry-run execution failure; MEDIUM follows the setting; preview redaction before truncation (REQ-005, REQ-006).
- Audit event fields, no answer text (REQ-007).
- ruff, mypy, full test suite.

## Documentation Impact
Yes (REQ-009). Target docs are those named by `docs/00_index.md` "Document References by Task" for the agent CLI, approval, and configuration domains, listed in `Implementation Target Files`; the generated API table is regenerated, not hand-edited.

## Assumptions
- The Issue's statement "no open sibling issue or plan touches these files" is stale (Step 2): the open Issues cliplc003, cliplc012, cliplc014, and mdqmcp007 and the unconsumed mcpdl003 procedures name overlapping files. The overlaps are compatible: different functions or fields (mcpdl003 changes `_issue_grant` and adds a grant-TTL config field; mdqmcp007 changes dry-run policy for mdq). They require rebasing line references, not a design change.
- Design for discard: a blocking `input()` in a daemon thread is not interruptible on any target platform, so the Plan never attempts to cancel it (Issue Constraints).
- The controller is a process-shared accessor (like `get_stdin_reader`), so `repl.py` construction does not change.
- The job state for Ctrl-C is a state value plus a cancel-callback registration seam; actual job cancellation belongs to the maintenance-job Plan (cliplc003), which the Issue marks Out of Scope.
- Interactive versus non-interactive input is decided by `sys.stdin.isatty()`.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Double-Ctrl-C force-exit policy (window, exit method, default) | Issue marks it `不明` | Design sets it off by default behind an injectable flag; owner confirms at review | False |
| UNK-02 | Default of the MEDIUM static-fallback setting | Issue marks it `不明` | Design default keeps today's behavior (fallback allowed); owner confirms at review | False |
| UNK-03 | Real Windows console behavior of control events | No Windows host; Issue says `不明` | Tested only through the control-event abstraction; stop and report if a path cannot be tested | False |
| UNK-04 | Exact shape of the job-cancel seam the maintenance-job Plan will consume | cliplc003 has no Plan yet | Define the seam here as a callback registration; cliplc003 adapts at its own Plan | False |
| UNK-05 | The line submitted after Ctrl-C at a prompt or after a multiline timeout is consumed by the abandoned blocking read, so the next prompt shows only after that line | Terminal line ownership of an uninterruptible `input()`; no way to clear the pending buffer was found | Procedures print a notice that the next line is discarded; owner confirms the behavior is acceptable at review | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/repl_input_controller.py | Create | Medium | N/A: new file | N/A | requires service restart (agent code) |
| scripts/agent/stdin_reader.py | Modify | Medium | 1 | N/A: 1 author | requires service restart (agent code) |
| scripts/agent/cli_view.py | Modify | Medium | 3 | N/A: 3 authors | requires service restart (agent code) |
| scripts/agent/repl_input_loop.py | Modify | High | 2 | N/A: 2 authors | requires service restart (agent code) |
| scripts/agent/signal_handler.py | Modify | Medium | 0 | N/A: 2 authors | requires service restart (agent code) |
| scripts/agent/tool_approval.py | Modify | High | 6 | N/A: 4 authors | requires service restart (agent code) |
| scripts/agent/tool_output.py | Modify | Low | 0 | N/A | requires service restart (agent code) |
| scripts/agent/tool_result_formatter.py | Modify | Low | 2 | N/A | requires service restart (agent code) |
| scripts/agent/commands/memory_data_ops.py | Modify | Medium | 2 | N/A: 3 authors | requires service restart (agent code) |
| scripts/agent/commands/cmd_memory.py | Modify | Medium | 0 | N/A | requires service restart (agent code) |
| scripts/agent/shared/models.py | Modify | Low | 3 | N/A | requires service restart (agent code) |
| scripts/agent/tool_audit.py | Modify | Medium | 9 | N/A | requires service restart (agent code) |
| scripts/agent/config_dataclasses.py | Modify | Medium | 13 | N/A | requires service restart (agent code) |
| scripts/agent/config_section_builders.py | Modify | Medium | 9 | N/A | requires service restart (agent code) |
| scripts/agent/services/config_field_registry.py | Modify | Low | 7 | N/A | requires service restart (agent code) |
| docs/23_agent/agent_07_02_cli-and-commands-cliview.md | Modify | Low | 0 | N/A | none (documentation) |
| docs/23_agent/agent_07_05_cli-and-commands-repl-io.md | Modify | Low | 1 | N/A | none (documentation) |
| docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md | Modify | Low | 5 | N/A | none (documentation) |
| docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md | Modify | Low | 7 | N/A | none (documentation) |
| docs/23_agent/agent_13_reference-api-generated.md | Modify | Low | N/A: generated | N/A | none (documentation) |
| tests/agent/test_repl_input_controller.py | Create | Low | N/A: new file | N/A | none (tests) |
| tests/agent/test_tool_approval_request_binding.py | Create | Low | N/A: new file | N/A | none (tests) |
| tests/agent/test_stdin_reader.py | Modify | Low | 1 | N/A | none (tests) |
| tests/test_cli_view.py | Modify | Low | 3 | N/A | none (tests) |
| tests/agent/test_repl.py | Modify | Low | 7 | N/A | none (tests) |
| tests/agent/test_signal_handler.py | Modify | Low | 0 | N/A | none (tests) |
| tests/agent/commands/test_memory_data_ops.py | Modify | Low | 2 | N/A | none (tests) |
| tests/agent/commands/test_cmd_memory.py | Modify | Low | 1 | N/A | none (tests) |
| tests/agent/commands/test_agent_cmd_memory.py | Modify | Low | 0 | N/A | none (tests) |
| tests/agent/test_config_builders.py | Modify | Low | 9 | N/A | none (tests) |

## Design
- **Controller** (`scripts/agent/repl_input_controller.py`): `ReplInputController` owns the single `StdinReader`. `submit(kind, prompt, operation_id, timeout)` creates an immutable `InputRequest` (`request_id`, `prompt_kind`, `created_at`, `operation_id`) and returns an `InputResult` with outcome `completed | timed_out | cancelled | eof | shutdown`. Lifecycle: `pending -> reading -> completed | timed_out | cancelled | discarded`. A new request is refused (`RuntimeError`-derived, explicit) while an older blocking read is unresolved; a destructive confirmation request additionally never reuses an in-flight read. State `PROMPT | TURN | JOB | SHUTDOWN` is held here and read by `SignalHandler`.
- **Reader**: delivery target is the waiter object captured in `_run` before `input()` is called, not `self._waiter` after it returns. A line whose captured waiter is done (timed out or cancelled) is dropped and the one blocking read is considered resolved, so the next request starts a fresh read. At most one read is outstanding (existing invariant retained).
- **Multiline**: continuation reads move from `CLIView.read_multiline` to the controller. On `timed_out` the partial text is not submitted; interactive (`isatty`) offers send / continue / discard, non-interactive discards.
- **Memory prompts**: `memory_delete` and `memory_prune` become `async`, `_cmd_memory` awaits them, and `_confirm` becomes a controller request whose `operation_id` is the memory id (delete) or a prune operation id; `y`/`yes` only for that request.
- **Approval**: `check_approval` creates one request per call (`request_id`, `operation_id` = `call_id`), the preview carries `required` (HIGH) or `optional` (MEDIUM) metadata and a source (`static | dry_run`). HIGH: any `ApprovalPreviewError` (blocking or not) denies with `denied_preview_failed`. MEDIUM: falls back to the static preview only when the new `ApprovalConfig` field allows it (default allows, UNK-02). Static previews use `mask_args(args, masked_fields)` output; dry-run text and error text pass the shared masker before `[:300]`/`[:200]` truncation; `emit_approval_prompt` renders only masked text with the request id. Audit gets request id, preview source, fallback reason; the answer text is never passed to `audit_approval`.
- **Signals**: `SignalHandler` registers SIGINT separately from SIGTERM. SIGINT: `PROMPT` discard the current line (controller `cancel_current`), `TURN` cancel the running turn, `JOB` invoke the registered job-cancel callback (seam only, UNK-04), `SHUTDOWN` force exit only when `force_exit_on_second_sigint` is set (default off, UNK-01). SIGTERM and `CTRL_CLOSE_EVENT` begin graceful shutdown. The Windows path is split into a pure `_dispatch_control_event(ctrl_type)` function so tests exercise it without a console; the ctypes callback uses the numeric event constants instead of `win32con`.
- **Alternatives**: (a) cancel the blocking read: rejected, `input()` is not interruptible; (b) keep the hand-off and add a request tag: rejected, it keeps delivery of stale text to a live waiter; (c) leave `build_preview` unmasked and mask in `tool_output`: rejected, truncation inside `build_preview` would precede redaction.
- **Consumer scan** (`tools/scan_change_consumers.py --seed get_stdin_reader`, Step 3): consumers are `cli_view.py`, `repl_input_loop.py`, `tool_approval.py`, `tests/agent/test_stdin_reader.py`, and the generated reference table; all are target rows. `test_prompt_source.py` is `not affected: its Reader is the prompt-source contract`. `read_multiline` consumers: `repl_input_loop.py`, `tests/test_cli_view.py`, `tests/agent/test_repl.py` (all target rows).
- **Predictable fallout check** (Step 3): module size gate 24576 B: `memory_data_ops.py` 15762 B, `repl_input_loop.py` 13722 B, `cli_view.py` 11004 B, `tool_approval.py` 10769 B are below it; the controller is a new module, so no split row is needed. Pinned counts: no test found asserting a count over the changed lists (`not affected`). Tool inventory: no `tools/` change (`not affected`). Generated blocks: `agent_13_reference-api-generated.md` is a row.
- **Import contract**: `agent.repl_input_controller` imports only `agent.stdin_reader` and stdlib; run `lint-imports` (Validation plan).
- **Persisted schema check**: not applicable (no DDL, schema version, or migration).

## Implementation steps
Each checklist item cites `Implementation Target Files` rows. Tests are the first item of each phase.

1. **Phase 1: Input ownership and delivery binding**
   - [ ] Write the stale-`y` crossover and controller lifecycle tests (REQ-001, REQ-002; tests/agent/test_repl_input_controller.py, tests/agent/test_stdin_reader.py)
   - [ ] Bind delivery to the captured waiter and discard late lines (REQ-002; scripts/agent/stdin_reader.py)
   - [ ] Add `ReplInputController`, request model, outcomes, shared accessor (REQ-001, REQ-003; scripts/agent/repl_input_controller.py)
2. **Phase 2: Normal and multiline prompts**
   - [ ] Update tests: multiline timeout, partial text never submitted, CLIView render-only (REQ-003; tests/test_cli_view.py, tests/agent/test_repl.py)
   - [ ] Move multiline continuation into the controller; remove `read_multiline`, `Reader`, timeout constant from CLIView (REQ-003; scripts/agent/cli_view.py)
   - [ ] Read through the controller and map outcomes in the loop (REQ-001, REQ-003; scripts/agent/repl_input_loop.py)
3. **Phase 3: Memory confirmation**
   - [ ] Update tests: controller-based confirmation, race refusal, awaited `_cmd_memory` (REQ-004; tests/agent/commands/test_memory_data_ops.py, tests/agent/commands/test_cmd_memory.py, tests/agent/commands/test_agent_cmd_memory.py)
   - [ ] Make `memory_delete`/`memory_prune` async with request-bound confirmation; await them (REQ-004; scripts/agent/commands/memory_data_ops.py, scripts/agent/commands/cmd_memory.py)
4. **Phase 4: Approval binding, preview, audit, config**
   - [ ] Write approval tests: crossover, HIGH fail-closed, MEDIUM setting, redaction before truncation, audit fields (REQ-005, REQ-006, REQ-007; tests/agent/test_tool_approval_request_binding.py, tests/agent/test_config_builders.py)
   - [ ] Add the MEDIUM fallback field, builder, registry entry (REQ-005; scripts/agent/config_dataclasses.py, scripts/agent/config_section_builders.py, scripts/agent/services/config_field_registry.py)
   - [ ] Bind approval to request/operation id, required/optional preview, masked previews (REQ-005, REQ-006; scripts/agent/tool_approval.py, scripts/agent/tool_output.py, scripts/agent/tool_result_formatter.py)
   - [ ] Add audit provenance fields (REQ-007; scripts/agent/shared/models.py, scripts/agent/tool_audit.py)
5. **Phase 5: Signals**
   - [ ] Write tests: Ctrl-C per state, SIGTERM, control-event abstraction, ctypes fix, force exit (REQ-008; tests/agent/test_signal_handler.py, tests/agent/test_repl.py)
   - [ ] Split SIGINT from SIGTERM, state-dependent behavior, fix ctypes fallback, optional force exit (REQ-008; scripts/agent/signal_handler.py, scripts/agent/repl_input_loop.py)
6. **Phase 6: Documentation**
   - [ ] Update docs and regenerate the API table (REQ-009; docs/23_agent/agent_07_02_cli-and-commands-cliview.md, docs/23_agent/agent_07_05_cli-and-commands-repl-io.md, docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md, docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md, docs/23_agent/agent_13_reference-api-generated.md)
7. **Phase 7: Deployment & Verification**
   - [ ] Run the validation sequence in `rules/toolchain.md` and the checkers in `rules/tool-gates.md`; then hand off to `skills/deploy/SKILL.md` (REQ-001 through REQ-009). Prerequisite: the change is committed and pushed first; deploying is the user's decision (approval gate).

### Release units
**Unit**: input-controller-cutover | **Phases**: 1, 2 | **Reason**: removing `CLIView.read_multiline` and the reader hand-off breaks `repl_input_loop.py`, the CLIView tests, and the `test_repl.py` tests until the loop reads through the controller.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/repl_input_controller.py, scripts/agent/stdin_reader.py | Unit | `uv run pytest tests/agent/test_repl_input_controller.py tests/agent/test_stdin_reader.py -q` | Discard, single reader, outcomes pass |
| scripts/agent/cli_view.py, scripts/agent/repl_input_loop.py | Unit + integration | `uv run pytest tests/test_cli_view.py tests/agent/test_repl.py -q` | Timeout-then-approval and timeout-then-memory scenarios pass |
| scripts/agent/commands/memory_data_ops.py, scripts/agent/commands/cmd_memory.py | Unit | `uv run pytest tests/agent/commands -q` | Async confirmation, no `input()` |
| scripts/agent/tool_approval.py, scripts/agent/tool_output.py, scripts/agent/tool_audit.py | Unit | `uv run pytest tests/agent -k "tool_approval" -q` | Fail-closed, redaction, audit fields |
| scripts/agent/signal_handler.py | Unit | `uv run pytest tests/agent/test_signal_handler.py -q` | State-dependent Ctrl-C, ctypes fix |
| scripts/ | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/ -c pyproject.toml`, `lint-imports` | Clean; baseline pre-existing findings only (vulture exit 3 in unrelated files; bandit exit 1 baseline, Step 5) |
| Whole suite | Full | `uv run python tools/run_validation_gates.py --full`; `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | All pass; changed-line coverage at least 90% (diff-cover 10.3.0 available, current number recorded at implementation) |
| docs/ | Checkers | `rules/tool-gates.md` "When to run which tool"; `uv run python tools/generate_reference_table.py --check` | No drift |

## Risks
- **Risk**: A blocking read left behind by a timed-out request holds stdin, so the next request waits → **Mitigation**: the controller reports `timed_out`/`discarded` for the old request, starts the next read only when the single outstanding read resolves, and refuses destructive confirmation meanwhile (REQ-001).
- **Risk**: Making `_cmd_memory` async breaks sync callers and tests → **Mitigation**: the registry already awaits coroutine handlers; the three test files are target rows.
- **Risk**: Overlap with open Issues (cliplc003, cliplc012, cliplc014, mdqmcp007) and unconsumed mcpdl003 procedures on `tool_approval.py`, `config_dataclasses.py`, `memory_data_ops.py` → **Mitigation**: changes are to different functions and fields; rebase line references and run `tools/check_plan_target_overlaps.py` after freeze; sequence this Plan before cliplc003 and cliplc012.
- **Risk**: `repl_input_loop._repl_loop` is already CC 31 (radon E) and gains state reporting → **Mitigation**: put new logic in the controller and keep loop changes to call-site mapping.
- **Risk**: HIGH fail-closed on any preview failure may deny operations during an MCP outage → **Mitigation**: intentional per the Issue; the denial message states the reason and the audit event records `fallback_reason`.
- **Risk**: Importing the private `_mask_secrets` couples the approval path to a private name → **Mitigation**: follow the existing precedent in `tool_result_formatter.py`; no new masker is created.
- **Risk**: Force exit can lose unsaved state → **Mitigation**: off by default (UNK-01), injectable, covered by a test.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Input ownership and delivery binding | In Progress | — | — |  |
| 2 | Normal and multiline prompts | In Progress | — | — |  |
| 3 | Memory confirmation | In Progress | — | — |  |
| 4 | Approval binding, preview, audit, config | In Progress | — | — |  |
| 5 | Signals | In Progress | — | — |  |
| 6 | Documentation | In Progress | — | — |  |
| 7 | Deployment and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261122-210644_01_scripts_agent_repl_input_controller.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261122-210644_02_scripts_agent_stdin_reader.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261122-210644_03_scripts_agent_cli_view.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261122-210644_04_scripts_agent_repl_input_loop.py.md | 2, 5 | Procedure | Pending | — | — |
| implementations/20261122-210644_05_scripts_agent_signal_handler.py.md | 5 | Procedure | Pending | — | — |
| implementations/20261122-210644_06_scripts_agent_tool_approval.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261122-210644_07_scripts_agent_tool_output.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261122-210644_08_scripts_agent_tool_result_formatter.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261122-210644_09_scripts_agent_commands_memory_data_ops.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261122-210644_10_scripts_agent_commands_cmd_memory.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261122-210644_11_scripts_agent_shared_models.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261122-210644_12_scripts_agent_tool_audit.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261122-210644_13_scripts_agent_config_dataclasses.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261122-210644_14_scripts_agent_config_section_builders.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261122-210644_15_scripts_agent_services_config_field_registry.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261122-210644_16_docs_23_agent_agent_07_02_cli-and-commands-cliview.md.md | 6 | Procedure | Pending | — | — |
| implementations/20261122-210644_17_docs_23_agent_agent_07_05_cli-and-commands-repl-io.md.md | 6 | Procedure | Pending | — | — |
| implementations/20261122-210644_18_docs_23_agent_agent_06_02_tool-execution-and-approval-approval.md.md | 6 | Procedure | Pending | — | — |
| implementations/20261122-210644_19_docs_23_agent_agent_08_04_configuration-mcp-approval-obs.md.md | 6 | Procedure | Pending | — | — |
| implementations/20261122-210644_20_docs_23_agent_agent_13_reference-api-generated.md.md | 6 | Procedure | Pending | — | — |
| implementations/20261122-210644_22_tests_agent_test_tool_approval_request_binding.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261122-210644_29_tests_agent_commands_test_agent_cmd_memory.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261122-210644_30_tests_agent_test_config_builders.py.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261122-210208
- **Related target files**: scripts/agent/repl_input_controller.py, scripts/agent/stdin_reader.py, scripts/agent/cli_view.py, scripts/agent/repl_input_loop.py, scripts/agent/signal_handler.py, scripts/agent/tool_approval.py, scripts/agent/tool_output.py, scripts/agent/tool_result_formatter.py, scripts/agent/commands/memory_data_ops.py, scripts/agent/commands/cmd_memory.py, scripts/agent/shared/models.py, scripts/agent/tool_audit.py, scripts/agent/config_dataclasses.py, scripts/agent/config_section_builders.py, scripts/agent/services/config_field_registry.py, docs/23_agent/agent_07_02_cli-and-commands-cliview.md, docs/23_agent/agent_07_05_cli-and-commands-repl-io.md, docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md, docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md, docs/23_agent/agent_13_reference-api-generated.md, tests/agent/test_repl_input_controller.py, tests/agent/test_tool_approval_request_binding.py, tests/agent/test_stdin_reader.py, tests/test_cli_view.py, tests/agent/test_repl.py, tests/agent/test_signal_handler.py, tests/agent/commands/test_memory_data_ops.py, tests/agent/commands/test_cmd_memory.py, tests/agent/commands/test_agent_cmd_memory.py, tests/agent/test_config_builders.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 1 | scripts/agent/repl_input_controller.py | Phase 1 | AC-1, AC-2 | tests/agent/test_repl_input_controller.py | Explicit in issue |
| REQ-001 | Required Changes bullet 1 | scripts/agent/repl_input_loop.py | Phase 2 | AC-2 | tests/agent/test_repl.py | Explicit in issue |
| REQ-001 | Required Changes bullet 1 | scripts/agent/commands/memory_data_ops.py | Phase 3 | AC-2 | tests/agent/commands/test_memory_data_ops.py | Explicit in issue |
| REQ-002 | `stdin_reader.py:104-109` | scripts/agent/stdin_reader.py | Phase 1 | AC-1 | tests/agent/test_stdin_reader.py | Confirmed by repository evidence |
| REQ-002 | Required Changes bullet 2 | scripts/agent/repl_input_controller.py | Phase 1 | AC-1 | tests/agent/test_repl_input_controller.py | Explicit in issue |
| REQ-003 | Required Changes bullet 3 | scripts/agent/cli_view.py | Phase 2 | AC-3 | tests/test_cli_view.py | Explicit in issue |
| REQ-003 | Required Changes bullet 3 | scripts/agent/repl_input_loop.py | Phase 2 | AC-3 | tests/agent/test_repl.py | Explicit in issue |
| REQ-003 | Required Changes bullet 3 | scripts/agent/repl_input_controller.py | Phase 1 | AC-3 | tests/agent/test_repl_input_controller.py | Explicit in issue |
| REQ-004 | `memory_data_ops.py:47-53` | scripts/agent/commands/memory_data_ops.py | Phase 3 | AC-2 | tests/agent/commands/test_memory_data_ops.py | Confirmed by repository evidence |
| REQ-004 | `cmd_memory.py:80-124` | scripts/agent/commands/cmd_memory.py | Phase 3 | AC-2 | tests/agent/commands/test_cmd_memory.py | Derived from confirmed evidence |
| REQ-004 | `cmd_memory.py:80-124` | tests/agent/commands/test_agent_cmd_memory.py | Phase 3 | AC-2 | tests/agent/commands/test_agent_cmd_memory.py | Derived from confirmed evidence |
| REQ-005 | Required Changes bullet 4 | scripts/agent/tool_approval.py | Phase 4 | AC-1, AC-4 | tests/agent/test_tool_approval_request_binding.py | Confirmed by repository evidence |
| REQ-005 | Required Changes bullet 4 | scripts/agent/config_dataclasses.py | Phase 4 | AC-4 | tests/agent/test_config_builders.py | Explicit in issue |
| REQ-005 | Required Changes bullet 4 | scripts/agent/config_section_builders.py | Phase 4 | AC-4 | tests/agent/test_config_builders.py | Derived from confirmed evidence |
| REQ-005 | Required Changes bullet 4 | scripts/agent/services/config_field_registry.py | Phase 4 | AC-4 | tests/agent/test_config_builders.py | Derived from confirmed evidence |
| REQ-006 | `tool_result_formatter.py:69-71` | scripts/agent/tool_output.py | Phase 4 | AC-4 | tests/agent/test_tool_approval_request_binding.py | Confirmed by repository evidence |
| REQ-006 | `tool_result_formatter.py:69-71` | scripts/agent/tool_result_formatter.py | Phase 4 | AC-4 | tests/agent/test_tool_approval_request_binding.py | Confirmed by repository evidence |
| REQ-007 | `shared/models.py:13-28` | scripts/agent/shared/models.py | Phase 4 | AC-4 | tests/agent/test_tool_approval_request_binding.py | Confirmed by repository evidence |
| REQ-007 | `tool_audit.py:111-148` | scripts/agent/tool_audit.py | Phase 4 | AC-4 | tests/agent/test_tool_approval_request_binding.py | Confirmed by repository evidence |
| REQ-008 | `signal_handler.py:54-63,101` | scripts/agent/signal_handler.py | Phase 5 | AC-5 | tests/agent/test_signal_handler.py | Confirmed by repository evidence |
| REQ-008 | Required Changes bullet 5 | scripts/agent/repl_input_loop.py | Phase 5 | AC-5 | tests/agent/test_repl.py | Explicit in issue |
| REQ-009 | Documentation Impact | docs/23_agent/agent_07_05_cli-and-commands-repl-io.md | Phase 6 | AC-6 | `rules/tool-gates.md` checkers | Confirmed by repository evidence |
| REQ-009 | Documentation Impact | docs/23_agent/agent_07_02_cli-and-commands-cliview.md | Phase 6 | AC-6 | `rules/tool-gates.md` checkers | Confirmed by repository evidence |
| REQ-009 | Documentation Impact | docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md | Phase 6 | AC-6 | `rules/tool-gates.md` checkers | Derived from confirmed evidence |
| REQ-009 | Documentation Impact | docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md | Phase 6 | AC-6 | `rules/tool-gates.md` checkers | Derived from confirmed evidence |
| REQ-009 | Documentation Impact | docs/23_agent/agent_13_reference-api-generated.md | Phase 6 | AC-6 | `generate_reference_table.py --check` | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261122-210644 -->