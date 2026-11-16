## Goal

Build the session-start memory block in `PromptSetup.setup_prompt` through the shared builder, so recalled memory is neutralized and framed as data (`REQ-003`: session-start path; `REQ-005`: path test).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `memory_block` construction in `setup_prompt` in `scripts/agent/startup_prompt_setup.py` and the companion test file `tests/agent/test_startup_prompt_setup.py`.
- Out of scope: the snippet count cap and its warning, snippet order, PII redaction and truncation (they run in the memory service before this point), the failure handling, and the per-turn path (document `03`).

## Assumptions

- Execute after document `01` of this Plan: `snippet_filter.py` must already provide the builder.
- The builder returns the block starting at the header line, so `setup_prompt` keeps prepending its own two blank lines before appending to the system prompt (Plan corrected in Step 3a).
- Plan overlap judgment: no other Frozen Plan targets this file or its test file.
- Existing tests assert only `"--- USER MEMORY ---" in ctx.conv.system_prompt_content` (`tests/agent/test_startup_prompt_setup.py`, `tests/agent/test_startup.py`), which the unchanged header line keeps true.
- Test file `tests/agent/test_startup_prompt_setup.py` is a companion: it is a Plan row under `tests/`, only the `startup_prompt_setup.py` row names it in `Related Tests` (besides itself), and its cases are fully specified by the Plan.

## Design decisions

- Replace the inline string construction with `memory_block = "\n\n" + block` where `block` comes from the builder called with the capped snippets' texts; skip appending when the builder returns an empty string.
- Leave the cap, the warning, the exception handling, `memory_disabled` handling and the final `replace_history` call exactly as they are.

## Alternatives considered

N/A: the Plan fixes the approach (one shared builder on both paths).

## Implementation
### Target file
`scripts/agent/startup_prompt_setup.py`

### Procedure
1. Import the builder from `agent.memory.snippet_filter` with the module's other imports (sorted per ruff `I`).
2. In `setup_prompt`, after the cap, compute the block from `[snippet.text for snippet in memory_snippets]` through the builder and append `"\n\n" + block` to `initial_prompt` only when the block is non-empty.

### Method
- Keep `if memory_snippets:` and the cap as they are; the empty-block check covers a list of snippets that the builder drops (it does not drop any; keep the check for the builder's documented empty result).
- Do not change the `try`/`except` shape or the classification helper.

### Details
- `setup_prompt` is radon B (10); removing the inline join must not raise it.
- Check `lint-imports` for the new import: both modules are in `agent`, so no layer rule applies.

### Companion test files
- `tests/agent/test_startup_prompt_setup.py`
  - Procedure: add tests with the file's fake memory service pattern: (a) a snippet with embedded line breaks and a copy of the header yields a system prompt that contains the real header line once, the framing line once, and the hostile text on a single bullet line; (b) ordinary snippets keep their wording; (c) the cap behavior and failure handling tests stay unchanged and pass; keep the existing header assertions. Write (a) first and confirm it fails on the current code.
  - Validation: `uv run pytest tests/agent/test_startup_prompt_setup.py tests/agent/test_startup.py tests/agent/test_startup_memory_failures.py -q`.

## Compatibility considerations

- The session-start block gains one framing line and snippet text becomes one line; the header line, the cap, order, PII redaction, truncation and failure handling are unchanged.

## Security considerations

- Closes the session-start entry of a persistent prompt-injection channel (recalled text entering the system prompt unmarked). The residual risk is documented, not eliminated.

## Rollback considerations

- Revert the commit; the builder in document `01` is harmless if left unused.

## Validation plan

- `uv run pytest tests/agent/test_startup_prompt_setup.py tests/agent/test_startup.py tests/agent/test_startup_memory_failures.py -q`; the hostile-snippet test fails on the pre-change code.
- `uv run ruff format`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`.
- `uv run python tools/check_module_size.py`, `uv run python tools/generate_reference_table.py --check`; diff coverage per `rules/toolchain.md` section 7.

## Completion criteria

- The session-start prompt contains the block from the builder; cap, order, PII redaction, truncation and failure handling are unchanged and the existing header assertions pass (`REQ-003`, AC-3).
- The new test exists and fails on the pre-change code (`REQ-005`, AC-5).

## Out of Scope

- The per-turn path, the helper, documentation, and deployment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the hostile-snippet `setup_prompt` test and confirm it fails on the current code (companion `tests/agent/test_startup_prompt_setup.py`) | Pending | — | — | |
| 2 | Build the session-start block through the builder in `setup_prompt` | Pending | — | — | |
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
- **Requirement ID**: `REQ-003` (session-start path uses the builder), `REQ-005` (path test)
- **Source issue**: issues/20261115-214901_startrev001_memory-prompt-injection-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-221435_startrev001_memory-prompt-injection-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-095914
- **Related target files**: `scripts/agent/startup_prompt_setup.py`, `tests/agent/test_startup_prompt_setup.py`
