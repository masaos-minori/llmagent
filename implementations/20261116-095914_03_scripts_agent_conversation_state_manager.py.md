## Goal

Build the per-turn memory block in `ConversationStateManager.handle_memory_injection` through the shared builder, so both injection paths produce the same neutralized and framed block (`REQ-004`: per-turn path; `REQ-005`: path test).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `memory_block` construction in `handle_memory_injection` in `scripts/agent/conversation_state_manager.py` and the companion test file `tests/agent/test_memory_injection_recovery.py`.
- Out of scope: the message role, the `_memory_injected` marker, `source="memory_injection"`, the degraded-state and recovery handling, and the session-start path (document `02`).

## Assumptions

- Execute after document `01` of this Plan: the builder must exist.
- The per-turn message content starts at the header line today, which is exactly what the builder returns, so the message text stays header-first (Plan corrected in Step 3a).
- `ctx.conv.append_message` and `TRUSTED_SOURCES` in `scripts/agent/context.py` handle the `_memory_injected` marker; they are not changed (reference file).
- Plan overlap judgment: no other Frozen Plan targets this file or its test file.
- Test file `tests/agent/test_memory_injection_recovery.py` is a companion: it is a Plan row under `tests/`, only the `conversation_state_manager.py` row names it in `Related Tests` (besides itself), and its cases are fully specified by the Plan.

## Design decisions

- Replace the inline join with the builder call over `[snippet.text for snippet in memory_snippets]`; append the message only when the returned block is non-empty, with the same role, marker and source arguments as today.
- Leave the `try`/`except`/`else` flow and the degraded-state transitions untouched.

## Alternatives considered

N/A: the Plan fixes the approach (one shared builder on both paths).

## Implementation
### Target file
`scripts/agent/conversation_state_manager.py`

### Procedure
1. Import the builder from `agent.memory.snippet_filter` with the module's other imports (sorted per ruff `I`).
2. In `handle_memory_injection`, build the block through the builder, and keep the `append_message` call with `"role": "system"`, `"_memory_injected": True` and `source="memory_injection"` as they are, using the block as `content`.

### Method
- Keep `if memory_snippets:` and add the non-empty check on the block; nothing else in the method changes.

### Details
- `handle_memory_injection` is radon B (9); removing the inline join must not raise it.
- Confirm no other module parses the old block text (the header appears only in the two builders and the tests that assert it).

### Companion test files
- `tests/agent/test_memory_injection_recovery.py`
  - Procedure: add tests using the file's `_make_manager` and fake memory helpers: (a) with a hostile snippet (line breaks, a copy of the header) the appended message has role `system`, `_memory_injected` true, source `memory_injection`, content that starts at the header line, contains the framing line once, and holds the hostile text on a single bullet line; (b) ordinary snippets keep their wording; (c) the failure, recovery and flag transition tests stay unchanged and pass. Write (a) first and confirm it fails on the current code.
  - Validation: `uv run pytest tests/agent/test_memory_injection_recovery.py tests/agent/test_orchestrator.py -q`.

## Compatibility considerations

- The per-turn block gains one framing line and snippet text becomes one line; role, marker, source and degraded-state handling are unchanged, and the header line stays as is.

## Security considerations

- Closes the per-turn entry of the same channel: without it, hostile text would be injected unchecked one turn after a sanitized session start. The residual risk is documented.

## Rollback considerations

- Revert the commit; the builder in document `01` is harmless if left unused.

## Validation plan

- `uv run pytest tests/agent/test_memory_injection_recovery.py tests/agent/test_orchestrator.py tests/agent/test_startup.py -q`; the hostile-snippet test fails on the pre-change code.
- `uv run ruff format`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`.
- `uv run python tools/check_module_size.py`, `uv run python tools/generate_reference_table.py --check`; diff coverage per `rules/toolchain.md` section 7.

## Completion criteria

- The per-turn message is a `system` message built by the builder with `_memory_injected` and `source="memory_injection"` unchanged (`REQ-004`, AC-4).
- The new test exists and fails on the pre-change code (`REQ-005`, AC-5).

## Out of Scope

- The session-start path, the helper, documentation, and deployment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `handle_memory_injection` hostile-snippet test and confirm it fails on the current code (companion `tests/agent/test_memory_injection_recovery.py`) | Pending | — | — | |
| 2 | Build the per-turn block through the builder in `handle_memory_injection` | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (per-turn path uses the builder), `REQ-005` (path test)
- **Source issue**: issues/20261115-214901_startrev001_memory-prompt-injection-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-221435_startrev001_memory-prompt-injection-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-095914
- **Related target files**: `scripts/agent/conversation_state_manager.py`, `tests/agent/test_memory_injection_recovery.py`
