## Goal

Add the effective-configuration snapshot of the real `config/agent.toml` and the explicit-over-default precedence test (REQ-008, snapshot contract).

## Scope
**Release unit**: RU-1

## Assumptions
- Companion judgement: condition 2 is met (named by row 01 only), but condition 3 fails because this row carries its own test-design decisions (snapshot as a recorded contract, real-file read not mocked, `integration` marker); it keeps its own document.
- The asserted inventory is the post-change one: 18 explicit values equal their code defaults, 12 differ, and 2 registered fields are absent (`tool.disabled_tools`, `approval.gitops_push_blocked`). The pre-change measurement (14 differing) is the baseline only, not the contract, because the two prompt fields are gone after rows 01 and 04 land.
- If `plans/20261121-172154_mcpdl003_dedup-config-isolation.md` lands in `config/agent.toml` first, the differing count becomes 13; that plan's row is judged compatible, not a conflict, so the snapshot must be written against the state at its own execution time and the count recorded in this test's comment.
- Marked `integration` following the existing real-config test pattern (`tests/agent/test_production_config_validator.py` line 348). Caveat from the Plan: the marker is defined as tests that start real subprocesses, and the full-suite and `diff-cover` runs deselect `integration`, so this test runs in CI only; coverage of the changed lines must come from row 12 and row 18, not from this file.
- The snapshot pins effective values through the builders, not the file text, so it records what the configuration resolves to rather than how it is written.

## Design decisions
- The test asserts the inventory as a recorded contract: an explicit value that equals its code default must remain in the file (REQ-005), so the test fails if such a value is dropped, which is the behaviour this plan is protecting.
- Precedence is asserted with a controlled override: an explicit value differing from the code default must survive through `build_agent_config`, proving explicit-over-default.
- Real-file read is not mocked: mocking would make the snapshot assert nothing about the deployed standard file.

## Alternatives considered
- Storing the snapshot as a fixture file that duplicates the TOML: rejected, that creates a second source of truth for the same values.
- Asserting only the differing values: rejected, the equal-to-default group is exactly what REQ-005 protects.

## Implementation
### Target file
`tests/agent/test_config_effective_snapshot.py` (new)
### Procedure
Create the snapshot test and the precedence test.
### Method
- Load the real `config/agent.toml` through `shared.config_loader.ConfigLoader` with `strict=True`, build the effective configuration, and compare each explicit value with the dataclass default.
- Assert the recorded inventory counts and the per-field classification for the differing group; keep the two absent fields as a recorded assertion, not an error.
- Precedence case: one field with an explicit value that differs from its code default, resolved through the builders, must equal the explicit value.
- Mark `@pytest.mark.integration`.
### Details
- The file lives under `tests/agent/` mirroring the `scripts/agent/` module that produces the effective values (`config_builders.py`).
- Run with `-m integration` in the targeted pass; the CI job runs the full suite including `integration`.

## Compatibility considerations
- This is the deployment contract for `agentcfg006`, which reads the same file; the counts recorded here are what a later reduction plan must not silently change.

## Security considerations
- N/A: no trust boundary beyond reading the standard config file.

## Rollback considerations
- N/A: revert the commit; the inventory assertion must be reverted together with row 01, otherwise the counts no longer match.

## Validation plan
- `uv run pytest tests/agent/test_config_effective_snapshot.py tests/agent/test_production_config_validator.py -m integration`
- `uv run ruff check tests/agent/test_config_effective_snapshot.py`, `uv run mypy scripts/`
- Full suite `-n logical` and `diff-cover` ≥ 90% (CI run includes this test).

## Completion criteria
- The snapshot matches the recorded post-change inventory, the precedence case proves an explicit value wins over the code default, and the real file passes both validators with zero errors (AC-5).

## Out of Scope
- Adding the two absent fields to `config/agent.toml` (Plan UNK-05, reported to `agentcfg006`).
- Snapshotting `registry/manifests/prompt_source.toml` contents (row 12 covers the reader contract).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | counts must be re-measured at execution time |
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
- **Requirement ID**: `REQ-008` (pin the effective configuration of the real file and prove explicit-over-default)
- **Source issue**: `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-162618_agentcfg005_system-prompt-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-165517
- **Related target files**: `tests/agent/test_config_effective_snapshot.py`
