## Goal

Create the single stdin owner: a request model, the five read outcomes, the interrupt state used by Ctrl-C handling, and a process-shared accessor, so every prompt (normal, multiline, tool approval, Memory delete, Memory prune) goes through one object (REQ-001, REQ-002, REQ-003).

## Scope
**Release unit**: input-controller-cutover

In scope: the new module only. Callers (loop, approval, Memory, signal handler, CLIView) are separate rows of the Plan.

## Assumptions

- Design for discard: a thread blocked in `input()` cannot be interrupted, so a timed-out or cancelled request is abandoned and its eventual line dropped (Plan Assumptions).
- Needs confirmation (non-blocking, UNK-05 in the Plan): after Ctrl-C or a multiline timeout the terminal line still belongs to the abandoned read, so the next line the operator submits is consumed and dropped before the next prompt reads; the notice text must say so.
- The reader's orphaned-read property is declared by the stdin_reader procedure; this module only calls it.

## Design decisions

- `PromptKind`(new) = normal, multiline, tool_approval, memory_delete, memory_prune; `InputOutcome`(new) = completed, timed_out, cancelled, eof, shutdown; `InputState`(new) = prompt, turn, job, shutdown; `InterruptAction`(new) = discard_input, cancel_turn, cancel_job, shutdown_in_progress.
- `InputRequest`(new) is a frozen dataclass: `request_id` (uuid4 hex), `prompt_kind`(new), `created_at`, `operation_id`(new), `prompt`, `timeout_s`(new), `destructive`; `InputResult`(new) carries the request, the outcome, and the text. Lifecycle (pending, reading, completed, timed_out, cancelled, discarded) lives in controller-private records, so the request stays immutable.
- `ReplInputController`(new) keeps at most one active request; a second `submit` while one is active raises `InputBusyError`(new). A destructive request also raises it while the reader reports an orphaned read.

## Alternatives considered

Rejected: tagging reads with a request id inside the reader only (it keeps one global waiter slot and no owner for state or interrupts); rejected: cancelling the blocked read (not possible with `input()`).

## Implementation
### Target file
`scripts/agent/repl_input_controller.py` (new)

### Procedure
1. Create the module with the enums, `InputRequest`(new), `InputResult`(new), `InputBusyError`(new), and `ReplInputController`(new).
2. Implement `ReplInputController.submit`(new): create a read task on the shared reader, wait on it with the request timeout, and map the result: text to completed, `TimeoutError` to timed_out (cancel the task), `EOFError` to eof, an explicit cancel to cancelled, a `shutdown` call to shutdown.
3. Implement `ReplInputController.collect_multiline`(new): continuation reads with the 30 s timeout that CLIView holds today; never return partial text as a submitted line. Interactive (`sys.stdin.isatty()`): offer send, continue, discard through a normal-kind request; non-interactive: discard. Output goes through a `notify` callable argument, so the module holds no view.
4. Implement the state API: `ReplInputController.set_state`(new), `ReplInputController.begin_turn`(new) / `ReplInputController.end_turn`(new) taking a cancel callback, `ReplInputController.begin_job`(new) / `ReplInputController.end_job`(new) (seam for the maintenance-job Plan), `ReplInputController.cancel_current`(new), `ReplInputController.shutdown`(new), and `ReplInputController.handle_interrupt`(new) returning an `InterruptAction`(new).
5. Add `get_input_controller`(new) and `reset_input_controller`(new), following the existing accessor pattern of the reader module; import only the reader module and the standard library.

### Method
Follow the shape of the existing reader module (module-level lazy singleton, small frozen types). The interrupt method performs the action for the current state: prompt cancels the current request, turn calls the registered turn-cancel callback, job calls the registered job-cancel callback, shutdown only reports that shutdown is in progress (the signal handler owns the force-exit policy).

### Details
- Mark every request that ends as timed_out or cancelled `discarded` once its read thread returns, so late lines are never delivered (REQ-002).
- Timeout default: none for normal and approval prompts; the multiline timeout constant moves here from CLIView as `MULTILINE_TIMEOUT_S`(new).
- Keep the module below the 24576 B size gate (`rules/tool-gates.md`); split the multiline helper into its own function, not a new file.

### Companion test files
- `tests/agent/test_repl_input_controller.py` (new)
  - Procedure: Write first: lifecycle and outcome tests for each outcome, stale-line discard, destructive refusal while a read is orphaned, single active request, multiline timeout never submitting partial text (interactive and non-interactive), state and interrupt actions per state.
  - Validation: `uv run pytest tests/agent/test_repl_input_controller.py -q`

## Compatibility considerations

New module; existing callers keep working until their own procedures switch them. `get_stdin_reader` stays importable (reader rows).

## Security considerations

The controller never logs or stores answer text beyond the returned `InputResult`(new); request ids are random and not derived from input.

## Rollback considerations

N/A: revert the commit; nothing else imports the module until the caller procedures land (release unit `input-controller-cutover`).

## Validation plan

- `uv run pytest tests/agent/test_repl_input_controller.py -q`
- `uv run ruff format scripts/agent/repl_input_controller.py && uv run ruff check scripts/agent/repl_input_controller.py && uv run mypy scripts/agent/repl_input_controller.py`
- `lint-imports` (import contract in `.importlinter`)

## Completion criteria

- Each outcome is reachable and tested; a late line never reaches a later request; a destructive request is refused while a read is orphaned.
- Module passes ruff, mypy, the import contract, and the module size gate.

## Out of Scope

Callers' wiring (CLIView, loop, approval, Memory, signals), docs, and any job cancellation behavior (maintenance-job Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261122-212457 | 20261122-213733 | Changed: scripts/agent/repl_input_controller.py (and companions) |
| 2 | Add or update tests per Validation plan (companion test files included) | Completed | 20261122-212457 | 20261122-213733 | targeted tests pass (647 in the affected directories) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261122-212457 | 20261122-213733 | ruff, mypy, lint-imports, bandit clean; full suite 13377 passed; diff-cover 91% |

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
- **Requirement ID**: `REQ-001` (sole stdin owner and request model), `REQ-002` (delivery bound to the starting request), `REQ-003` (read outcomes, multiline policy)
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-210208_cliplc001_repl-input-controller.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-210644
- **Related target files**: `scripts/agent/repl_input_controller.py`, `tests/agent/test_repl_input_controller.py`
