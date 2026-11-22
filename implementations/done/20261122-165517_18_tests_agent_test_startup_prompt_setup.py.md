## Goal

Replace the config-field prompt fixture with the typed single-source fixture (REQ-006, test migration).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Companion judgement: condition 2 is met (named by row 11 only), but condition 3 fails because the helper must decide how the typed source is supplied to the fixture; it keeps its own document.
- `_make_prompt_setup()` keeps its signature shape; the prompt value it supplies comes from the typed model, not from `ctx.cfg.tool`.

## Design decisions
- N/A: fixture source change; no test-design decision.

## Alternatives considered
- Mocking `ctx.cfg.tool` with an empty prompt dict: rejected, the startup path no longer reads the config layer.

## Implementation
### Target file
`tests/agent/test_startup_prompt_setup.py`
### Procedure
Point the helper's prompt fixture at the typed source.
### Method
- Remove the `system_prompt_tool="Initial prompt"` parameter (line 27) and the `ctx.cfg.tool.system_prompts` assignment (line 37).
- Provide the prompt content through the typed model from row 03 (a fixture source directory or an injected reader result), so `setup_prompt()` resolves it the same way production does.
- Keep the memory-injection assertions unchanged.
### Details
- The assertion that `ctx.conv.system_prompt_content` equals the resolved prompt is the contract this test keeps; only the input source changes.

## Compatibility considerations
- N/A: internal test change only.

## Security considerations
- N/A: no trust boundary is involved.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_startup_prompt_setup.py`
- `uv run ruff check tests/agent/test_startup_prompt_setup.py`, `uv run mypy scripts/`
- `uv run python tools/check_mock_patch_targets.py` if a patch target is added for the reader.

## Completion criteria
- The test proves the initial prompt is resolved through the typed model for the `default` name and for an explicit name, with memory injection unchanged (AC-4).

## Out of Scope
- Reader contract cases (row 12).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261122-182459 | 20261122-182459 | batch-run; helper prompt fixture replaced with autouse typed-source fixture (LLMAGENT_REGISTRY_DIR); config-field read removed; explicit-name case added per completion criteria; memory assertions unchanged |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261122-182459 | 20261122-183400 | 27 passed; ruff clean; check_mock_patch_targets no findings; mypy/full suite at batch end end-of-batch full-suite run: 13333 passed, 2 failed — b04 concurrent-writes flaky (3 reruns pass, unrelated to this batch), and an unlisted positional _build_tool_config call site in test_tool_result_formatter.py:77 fixed (finding recorded on row 14); diff-cover 100% (>=90) |

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
- **Requirement ID**: `REQ-006` (startup resolves the prompt through the typed model)
- **Source issue**: `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-162618_agentcfg005_system-prompt-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-165517
- **Related target files**: `tests/agent/test_startup_prompt_setup.py`