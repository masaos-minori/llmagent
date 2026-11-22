## Goal

Change the accepted-key cases so the removed prompt keys are asserted to be rejected as unknown keys (REQ-004, test migration).

## Scope
**Release unit**: RU-1

## Assumptions
- Companion judgement: condition 2 is met (named by row 09 only), but condition 3 fails because the existing accepted-key case must be inverted into an unknown-key assertion, a test-design decision of its own; it keeps its own document.
- The existing real-config integration case (line 348 onwards) is not changed; it passes once row 01 removes the key from `config/agent.toml`.

## Design decisions
- N/A: one accepted-key fixture becomes an unknown-key case; no test-design decision.

## Alternatives considered
- Keeping a case that asserts the key is accepted with a warning: rejected, there is no warning path after REQ-004.

## Implementation
### Target file
`tests/agent/test_production_config_validator.py`
### Procedure
Convert the accepted-key cases into unknown-key rejection cases.
### Method
- Replace the `"system_prompt_tool": ""` fixture in the no-error case (lines 196-202) with a case asserting `Unknown config keys` reports both `system_prompt_tool` and `system_prompts`.
- Remove `assert "system_prompt_tool" in keys` (line 296) and add the negative assertion that neither prompt name is in the valid-key set.
### Details
- The valid-key set is derived from the dataclass fields (row 04) plus explicit additions (row 09); the test asserts the observable result, not the derivation path.

## Compatibility considerations
- N/A: internal test change only.

## Security considerations
- N/A: no trust boundary is involved.

## Rollback considerations
- N/A: revert the commit as part of RU-1.

## Validation plan
- `uv run pytest tests/agent/test_production_config_validator.py`
- `uv run pytest tests/agent/test_production_config_validator.py -m integration` (the real-file case after row 01).
- `uv run ruff check tests/agent/test_production_config_validator.py`

## Completion criteria
- Both prompt keys are reported as unknown keys by the validator in this file's cases, and the real-file integration case still passes (AC-2).

## Out of Scope
- The per-server `[dedup]` key coverage added by `mcpdl003`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261122-182327 | 20261122-182327 | RU-1 batch-run; accepted-key case inverted to unknown-key rejection for both prompt names; valid-key set assertion inverted to negative. Finding: 'valid_keys_only_no_errors' name no longer fits the inverted case; renamed to test_removed_prompt_keys_are_rejected_as_unknown |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261122-182327 | 20261122-183400 | 46 passed incl. integration real-file case (also validates row 09); full suite at batch end end-of-batch full-suite run: 13333 passed, 2 failed — b04 concurrent-writes flaky (3 reruns pass, unrelated to this batch), and an unlisted positional _build_tool_config call site in test_tool_result_formatter.py:77 fixed (finding recorded on row 14); diff-cover 100% (>=90) |

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
- **Requirement ID**: `REQ-004` (assert the removed keys are rejected as unknown keys)
- **Source issue**: `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-162618_agentcfg005_system-prompt-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-165517
- **Related target files**: `tests/agent/test_production_config_validator.py`