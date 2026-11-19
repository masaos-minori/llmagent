## Goal

Give `_make_ctx` a real `ApprovalConfig` for `ctx.cfg.approval` so the two approval-applying tests keep passing once `approval` reloads through the validated path (REQ-006: valid approval values still apply; fixture-only change).

## Scope
**Release unit**: hot-reload-validation

- In scope: the `_make_ctx` fixture in this file; no test logic or assertion changes.

## Assumptions
- `dataclasses.replace` requires a real dataclass for a changed section — the same reason `_make_ctx` already sets `ctx.cfg.llm = LLMConfig()` with that comment (`test_agent_cmd_config.py:26-30`).
- Default `ApprovalConfig()` construction is valid (field `default_factory` defaults pass `__post_init__` tier/risk checks), so no per-test values are needed; `approval_resource_keys` / `approval_dry_run_tools` carry validators-free, type-safe values (`test_agent_cmd_config.py:324-338`).
- `TestPrintConfigValues._make_cfg_ctx` assignments to `ctx.cfg.approval.*` (`:199-202`) stay valid: `ApprovalConfig` is a mutable dataclass, and that class exercises the print path, not `apply_config_dict`.

## Design decisions
- Convert in `_make_ctx` (shared fixture) rather than in the two tests only, so any later reload test added to this file starts from a real section object.

## Alternatives considered
- Keep a `MagicMock` and patch `prepare_validated_section`: rejected — it would hide the candidate construction the Plan is testing.

## Implementation
### Target file
`tests/agent/commands/test_agent_cmd_config.py`

### Procedure
1. Add `ApprovalConfig` to the existing `from agent.config_dataclasses import LLMConfig` line (`:15`).
2. In `_make_ctx`, after the `ctx.cfg.llm = LLMConfig()` line, set `ctx.cfg.approval = ApprovalConfig()` and extend the fixture comment to name both replace call sites.
3. Run the whole file; if any other test in it relies on a mock-only approval attribute that `ApprovalConfig` lacks, convert that attribute to the real field value in the fixture (report it — do not add new approval semantics).

### Method
- No change to `_DUMMY_MCP`, the payloads of `test_approval_resource_keys_applied` / `test_approval_dry_run_tools_applied`, or their assertions: valid values must still apply through the validated path.

### Details
- N/A.

## Compatibility considerations
- Only this file's fixtures change behavior; production code and the other reload suites are covered by seq 03/06.

## Security considerations
- N/A: test fixture only; the applied-value contract it protects is the security-relevant one covered by seq 06's rejection tests.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
| Check | Command | Expected |
|---|---|---|
| Approval application through the validated path | `uv run pytest tests/agent/commands/test_agent_cmd_config.py -q` | All tests pass, incl. both approval-applying tests |
| Gates | `rules/toolchain.md` sequence | Pass |

## Completion criteria
- `ctx.cfg.approval` is a real `ApprovalConfig` in `_make_ctx`; both approval-applying tests pass after the seq 03 loop move; no assertion was weakened.

## Out of Scope
- Any production-code change; the rejection tests (seq 06 document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Convert the `_make_ctx` approval fixture to a real `ApprovalConfig` | Completed | 20261119-105232 | 20261119-105345 | After seq 03 lands Step 2 stale check clean; Step 3a: only the two approval-applying tests send approval fields (lines near the approval_resource_keys/approval_dry_run_tools payloads); file clean at baseline Changed: tests/agent/commands/test_agent_cmd_config.py (_make_ctx real ApprovalConfig; import extended). Before the change the 2 approval tests failed with TypeError (replace on a mock); after: 34 passed |
| 2 | Run the file and resolve any mock-only approval attribute reliance | Completed | 20261119-112102 | 20261119-112102 | test_agent_cmd_config.py 34 passed; no mock-only approval attribute reliance found |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261119-112102 | 20261119-112102 | End of unit: full suite 12907 passed, 7 skipped, 1 unrelated failure (test_check_repo_path_equivalence: Hypothesis property test on PurePosixPath, passes alone 9/9 and in the git MCP module under xdist 418/418); diff-cover 100%; ADR-cited tests 52 passed; validation gates pass; ruff/mypy/lint-imports/bandit clean |

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
- **Requirement ID**: REQ-006 (valid approval values keep applying; fixture conversion)
- **Source issue**: issues/20261117-123004_adrchk004_hot-reload-validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-094759_adrchk004_hot-reload-validation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-101805
- **Related target files**: `tests/agent/commands/test_agent_cmd_config.py`