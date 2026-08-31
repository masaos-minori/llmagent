# Implementation Procedure: Real-Config Verification Test for Git Tools (REQ-002)

## Goal

Add a test that loads the actual `config/agent.toml` (not a synthetic cfg) and asserts `classify_risk()` resolves git_checkout/git_pull/git_push to HIGH through the actual risk-classification path.

## Scope

Add a new test alongside the existing `test_git_checkout_pull_push_resolve_to_high_risk` in `tests/agent/test_tool_policy_comprehensive.py`. The new test uses the project's public config loading API (`load_config()`) rather than parsing TOML manually or constructing a synthetic cfg.

## Assumptions

- `scripts.agent.config_builders.load_config()` returns a dict with keys matching the AgentConfig dataclass structure (approval.approval_risk_rules, approval.tool_safety_tiers).
- The existing `_cfg()` helper in the test file constructs an AgentConfig from a dict; the new test will use `load_config()` directly.
- classify_risk() accepts an AgentConfig instance as its first argument.

## Design decisions

- Add a separate test method (not extend the existing one) to keep concerns clear: the existing test verifies mapping function behavior with synthetic data; the new test verifies end-to-end behavior with the shipped config.
- Use `load_config()` from the project's public API rather than reading TOML manually. If the API changes, the test failure will be obvious and fixable.
- Assert each of the three git tools individually to provide clear per-tool failure messages.

## Alternatives considered

- Extend the existing `test_git_checkout_pull_push_resolve_to_high_risk` to also load the real config. Rejected: this conflates two distinct concerns (mapping function vs. end-to-end pipeline) and makes it harder to identify which specific assertion fails.
- Create a separate test file. Rejected: the existing test file already covers these tools; adding here keeps related tests together and avoids duplication.

## Implementation

### Target file

`tests/agent/test_tool_policy_comprehensive.py`

### Procedure

Add a new test method that loads the actual config/agent.toml and asserts classify_risk() resolves git_checkout/git_pull/git_push to HIGH.

### Method

```python
    def test_real_config_resolves_git_tools_to_high_risk(self) -> None:
        """REQ-002: The shipped config/agent.toml resolves git_checkout/git_pull/git_push
        to HIGH through the actual risk-classification pipeline."""
        from agent.config_builders import load_config
        from agent.tool_policy import RiskLevel

        raw = load_config()
        # Build an AgentConfig from the loaded dict so classify_risk can access
        # nested fields like cfg.approval.approval_risk_rules.
        cfg = AgentConfig(**raw)
        for name in ("git_checkout", "git_pull", "git_push"):
            assert classify_risk(cfg, name, {"repo_path": "/tmp/repo"}) == RiskLevel.HIGH
```

### Details

The test must:
1. Import `load_config` from `agent.config_builders`.
2. Call `load_config()` to get the raw config dict.
3. Construct an `AgentConfig` instance using the raw dict (via `**raw`).
4. Call `classify_risk(cfg, tool_name, {"repo_path": "/tmp/repo"})` for each of the three git tools.
5. Assert each result equals `RiskLevel.HIGH`.

If `classify_risk` expects string values instead of enum values, adjust the assertion accordingly:
```python
assert classify_risk(cfg, name, {"repo_path": "/tmp/repo"}) == "high"
```

## Compatibility considerations

- This test depends on `load_config()` returning a dict compatible with `AgentConfig(**raw)`. If the config schema changes, the test will fail at construction time, making the issue obvious.
- The test may fail if the shipped config has been modified since the Plan was written. Verify against current repo state before finalizing.

## Security considerations

- This is a verification enhancement: ensuring the shipped config actually produces the expected risk classification. Catches regressions where config content drifts from intended security posture.

## Rollback considerations

- If the test fails due to config changes, revert by removing the test. The underlying risk classification logic remains unchanged.

## Validation plan

- Run the new test: `uv run pytest tests/agent/test_tool_policy_comprehensive.py::TestClassifyRisk::test_real_config_resolves_git_tools_to_high_risk`
- Expected outcome: all three git tools resolve to HIGH.
- Regression run: `uv run pytest tests/agent/test_tool_policy_comprehensive.py` — all existing tests pass.

## Completion criteria

- New test method exists in TestClassifyRisk class.
- Test loads config via `load_config()` (not synthetic cfg).
- Test asserts classify_risk() returns HIGH for git_checkout/git_pull/git_push.
- Test passes against current config/agent.toml.

## Out of scope

- Modifying the existing `test_git_checkout_pull_push_resolve_to_high_risk` test.
- Adding integration-level test exercising check_approval()'s full-word-"yes" path (separate concern).
- Parsing TOML manually instead of using the public config loading API.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add test_real_config_resolves_git_tools_to_high_risk to tests/agent/test_tool_policy_comprehensive.py | Completed | 20260831-150523 | 20260831-150523 | Already implemented on disk (commit `e8f0086bf`, prior session), in `TestClassifyOperationType` rather than `TestClassifyRisk` as this document's Design decisions specified — a cosmetic placement difference, not a behavioral gap; the test's assertions and config-loading approach match this document's Method/Details. |
| 2 | Verify test passes against current config/agent.toml | Completed | 20260831-150523 | 20260831-150523 | `uv run pytest tests/agent/test_tool_policy_comprehensive.py::TestClassifyOperationType::test_real_config_resolves_git_tools_to_high_risk` — 1 passed. Full regression: `uv run pytest tests/agent/test_tool_policy_comprehensive.py` — all passed. |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260828-163234_mcp004_approval_risk_hierarchy_gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-150209_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-205709
- **Related target files**: tests/agent/test_tool_policy_comprehensive.py
