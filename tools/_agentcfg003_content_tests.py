#!/usr/bin/env python3
"""_agentcfg003_content_tests.py — Authored content for the agentcfg003 test rows and companion blocks.

Private module for tools/generate_agentcfg003_procedures.py; cannot run standalone.
"""

from __future__ import annotations

from tools._agentcfg003_content_base import DEFAULTS

OWN_DOC = {
    "tests/shared/test_runtime_tool_registry.py",
    "tests/shared/test_tool_safety_tiers.py",
    "tests/mcp_servers/test_tool_schema_contract.py",
    "tests/agent/test_tool_policy_comprehensive.py",
    "tests/agent/test_tool_approval_risk.py",
    "tests/agent/test_agent_repl_tool_exec.py",
    "tests/agent/_config_test_defaults.py",
    "tests/agent/test_config_builders.py",
    "tests/agent/services/test_config_reload.py",
}

COMPANIONS: dict[str, dict[str, str]] = {}
TEST_CONTENT: dict[str, dict[str, object]] = {}


def companion(path: str, action: str, procedure: str, validation: str) -> None:
    COMPANIONS[path] = {
        "action": action,
        "procedure": procedure,
        "validation": validation,
    }


def add(path: str, **fields: object) -> None:
    entry = dict(DEFAULTS)
    entry.update(fields)
    TEST_CONTENT[path] = entry


# --- Companions (named by exactly one other row) ---

companion(
    "tests/shared/test_tool_metadata.py",
    "Create (new)",
    "Add contract tests for each closed value set and for the single version constant; assert the module "
    "imports nothing from `agent` (T-01).",
    "`uv run pytest tests/shared/test_tool_metadata.py -v`",
)

companion(
    "tests/shared/test_runtime_tool.py",
    "Change",
    "Replace the existing safe-default assertions (the `TestStrictBuilder` and `TestFixtureBuilderEquivalence` "
    "groups) with required-field assertions for the new fields, including that no default lowers risk.",
    "`uv run pytest tests/shared/test_runtime_tool.py -v`",
)

companion(
    "tests/shared/runtime_tool_factory.py",
    "Change",
    "Make `build_fixture_runtime_tool()` supply the new required fields, since the production builder no longer "
    "has defaults; keep the permissive behaviour confined to the fixture (T-02).",
    "`uv run pytest tests/shared/test_runtime_tool.py -v` and `PYTHONPATH=scripts uv run lint-imports`",
)

companion(
    "tests/shared/test_resource_scope.py",
    "Change",
    "Extend `TestValidateToolSchemaV2` to the new required field set and change `TestResolveResourceScopes` and "
    "`TestScopesConflict` fixtures to the key-to-kind mapping, including a `non_escalating` key that resolves a "
    "scope but never escalates (T-02, T-06).",
    "`uv run pytest tests/shared/test_resource_scope.py -v`",
)

companion(
    "tests/shared/test_tool_constants.py",
    "Change",
    "Rewrite the ownership assertions at lines 103, 117 and 127 as drift comparisons against declared "
    "metadata rather than ownership of `RETRYABLE_TOOLS` (T-08, T-09).",
    "`uv run pytest tests/shared/test_tool_constants.py -v`",
)

companion(
    "tests/agent/test_tool_policy.py",
    "Change",
    "Point the 71 references to the removed maps at declared metadata, and add the plan-mode derivation and "
    "key-kind cases (T-04, T-06).",
    "`uv run pytest tests/agent/test_tool_policy.py -v`",
)

companion(
    "tests/agent/test_tool_approval_preflight.py",
    "Change",
    "Replace the config-map and local-set fixtures in `TestCheckApprovalDryRun` with an entry that declares the "
    "capability flag (T-04, T-07).",
    "`uv run pytest tests/agent/test_tool_approval_preflight.py -v`",
)

companion(
    "tests/agent/test_tool_audit.py",
    "Change",
    "Move the operation-type and key-kind assertions in `TestAuditToolExec` to declared metadata, with a case "
    "for a `non_escalating` key not appearing in the audit scope (T-04, T-06).",
    "`uv run pytest tests/agent/test_tool_audit.py -v`",
)

companion(
    "tests/agent/test_tool_runner.py",
    "Change",
    "Replace the `RETRYABLE_TOOLS` membership assertions at lines 2534-2555 with the declared retry policy, and "
    "keep the reconciliation classification cases (T-04, T-08).",
    "`uv run pytest tests/agent/test_tool_runner.py -v`",
)

companion(
    "tests/agent/test_production_config_validator.py",
    "Change",
    "Remove the tier-map cases (`TestProductionConfigValidatorSafetyTiers`, "
    "`TestProductionConfigValidatorValidateUnknownToolSafetyTiers`) and add the fail-closed missing-field and "
    "unknown-key cases; keep the risk-floor group reading declared metadata (T-02, T-05).",
    "`uv run pytest tests/agent/test_production_config_validator.py -v`",
)

companion(
    "tests/agent/test_config_dataclasses.py",
    "Change",
    "Remove the field-level assertions for the four removed maps from `TestApprovalConfigValidation` and keep "
    "the operational-exception fields asserted (T-05).",
    "`uv run pytest tests/agent/test_config_dataclasses.py -v`",
)

companion(
    "tests/agent/commands/test_agent_cmd_config.py",
    "Change",
    "Remove the four assertions on the removed maps in `TestPrintConfigValues` and `TestApplyConfigDict` (T-05).",
    "`uv run pytest tests/agent/commands/test_agent_cmd_config.py -v`",
)

companion(
    "tests/agent/shared/test_startup_validation_pipeline.py",
    "Change",
    "Update the pipeline stage names and the patched tier check at lines 310 and 322 to the drift-report shape "
    "(T-09).",
    "`uv run pytest tests/agent/shared/test_startup_validation_pipeline.py -v`",
)

# --- Test rows that keep their own document ---

add(
    "tests/shared/test_runtime_tool_registry.py",
    goal="Assert that a policy application does not derive a tier from configuration (REQ-002, REQ-004, REQ-013 "
    "/ T-02).",
    assumptions=[
        "The fixture helpers build `RuntimeTool` instances, so they must carry the new required fields."
    ],
    design=[
        "The assertions move from a configuration-derived tier to the tier the entry was declared with."
    ],
    procedure="Change `TestApplyPolicyReversibility` and the fixture helper `_registry_with()` to the reduced "
    "`apply_policy()` signature, and assert the lookup returns the declared tier.",
    method=[
        "Add a case where a declared tier differs from what the removed configuration map would have "
        "produced, so the test cannot pass by coincidence."
    ],
    details=[
        "Verified 2026-11-21: this file is named by rows 04 and 39, so it keeps its own document."
    ],
    validation=["`uv run pytest tests/shared/test_runtime_tool_registry.py -v`"],
    completion=[
        "A policy application cannot change a declared tier, and the fixture supplies the required fields."
    ],
)

add(
    "tests/shared/test_tool_safety_tiers.py",
    goal="Assert the tier checks report drift only, with no decision effect (REQ-007, REQ-013 / T-09).",
    design=[
        "The fixture that reads the real `config/agent.toml` tiers (`_real_tool_safety_tiers()`) becomes a "
        "comparison against declared metadata."
    ],
    procedure="Change `TestRealAgentTomlSafetyTiers` and `TestUnknownToolSafetyTiersEarlyReturn` to the removed "
    "configuration argument, and assert the result is a finding rather than a classification.",
    method=["Keep the early-return case as a no-finding case for an empty registry."],
    details=[
        "Verified 2026-11-21: 20 direct references to the removed map in this file."
    ],
    validation=["`uv run pytest tests/shared/test_tool_safety_tiers.py -v`"],
    completion=["No assertion in this file depends on a removed configuration map."],
    out_of_scope=[
        "The test file that exercises the shared tier check through fixtures only (follow-up test-audit "
        "work item)."
    ],
)

add(
    "tests/mcp_servers/test_tool_schema_contract.py",
    goal="Assert the extended per-tool field set for every producer module (REQ-003, REQ-013 / T-03).",
    assumptions=[
        "The producers in rows 08 to 21 and row 68 must land in the same release unit."
    ],
    design=[
        "The contract test stays the single check over all producers; the envelope-version assertion is added "
        "only as a check that the value is unchanged."
    ],
    procedure="Extend the field set `test_all_tools_pass_schema_v2_contract()` checks, and change "
    "`test_side_effect_parity_matches_canonical()` to compare the declared class with the reference "
    "sets as a cross-check.",
    method=[
        "Keep `_TOOL_LIST_MODULES` unchanged (13 producer modules) and keep the tool-name coverage test as "
        "the check that no producer entry is missing."
    ],
    details=[
        "Verified 2026-11-21: this file is named by rows 08 and 68, so it keeps its own document."
    ],
    validation=["`uv run pytest tests/mcp_servers/test_tool_schema_contract.py -v`"],
    completion=[
        "Every producer entry declares the extended set, and no field is supplied by a default."
    ],
)

add(
    "tests/agent/test_tool_policy_comprehensive.py",
    goal="Assert the inverted priority in `classify_operation_type()` (REQ-007, REQ-013 / T-04, T-09).",
    design=[
        "The priority test is the one that can fail if the declared value is read after the reference sets, "
        "so it needs a case where the two disagree."
    ],
    procedure="Change `TestClassifyOperationType` to read declared metadata as the authority and assert the "
    "reference sets only produce a disagreement report.",
    method=[
        "Keep `TestEscalateForPath` and `TestEscalateForGithubBranch`, with the fixtures carrying the "
        "declared key kinds."
    ],
    details=[
        "Verified 2026-11-21: this file is cited by `docs/10_adr/adr_01_index.md` for the tier rule."
    ],
    validation=["`uv run pytest tests/agent/test_tool_policy_comprehensive.py -v`"],
    completion=[
        "A disagreement between a declaration and the reference data changes no decision, and the "
        "declared value is what the classification returns."
    ],
)

add(
    "tests/agent/test_tool_approval_risk.py",
    goal="Assert risk levels read from declared metadata (REQ-004, REQ-013 / T-04).",
    design=[
        "The risk-fallback cases in `TestClassifyRisk` move from the removed rule map to the declared tier's "
        "mapped risk."
    ],
    procedure="Change `_make_cfg()` so it no longer supplies the removed maps, and move `TestClassifyRisk` and "
    "`TestClassifyOperationType` to declared metadata.",
    method=[
        "Keep `TestBuildPreview` as the check that the preview shape is unchanged."
    ],
    details=[
        "Verified 2026-11-21: 14 direct references to the removed maps in this file."
    ],
    validation=["`uv run pytest tests/agent/test_tool_approval_risk.py -v`"],
    completion=["No test in this file supplies a removed configuration map."],
    out_of_scope=["The preview decision rules (preview work item)."],
)

add(
    "tests/agent/test_agent_repl_tool_exec.py",
    goal="Move the tier-behaviour contract assertions to declared metadata (REQ-004, REQ-013 / T-04).",
    design=[
        "The REPL path is the consumer that shows a tier result to the user, so the assertions stay as "
        "contract tests on the result, not on the source of the value."
    ],
    procedure="Change `TestClassifyRiskTierFallback` to the declared tier and remove the fixture values for the "
    "removed maps from `_make_cfg()`.",
    method=[
        "Keep `TestClassifyRiskDeleteDirectory`, `TestCheckAllowedRoot` and `TestCheckAllowedRepo` "
        "unchanged: those are operational exceptions the plan keeps."
    ],
    details=[
        "Verified 2026-11-21: 26 direct references to the removed maps in this file."
    ],
    validation=["`uv run pytest tests/agent/test_agent_repl_tool_exec.py -v`"],
    completion=["The REPL tier assertions pass from declared metadata only."],
)

add(
    "tests/agent/_config_test_defaults.py",
    goal="Remove the shared fixture mirrors of the removed maps (REQ-005, REQ-013 / T-05).",
    assumptions=[
        "The mirror relationship documented in this file's docstring is the reason the fixtures must be "
        "removed together with the shipped config."
    ],
    design=[
        "The fixture keeps the operational exception values the plan keeps, so the minimal-config helper still "
        "satisfies the validator's non-empty requirements."
    ],
    procedure="Delete `ALL_APPROVAL_RISK_RULES`, `ALL_TOOL_SAFETY_TIERS` and the removed-map entries, and update "
    "the docstring paragraph that describes the mirror.",
    method=[
        "Keep `PERMISSIVE_ALLOWED_ROOT`, `PERMISSIVE_SQLITE_VEC_SO` and the protected-path mirror."
    ],
    details=[
        "Verified 2026-11-21: 5 direct references; the file is used by the config contract test group."
    ],
    validation=[
        "`uv run pytest tests/agent/test_config_builders.py tests/agent/test_config_dataclasses.py -v`"
    ],
    completion=[
        "The fixture defines no value for a removed concept, and no test imports the removed names."
    ],
)

add(
    "tests/agent/test_config_builders.py",
    goal="Remove the builder and validator cases for the removed fields (REQ-005, REQ-009, REQ-013 / T-05).",
    design=[
        "The build path is asserted through `_MIN_CFG`; the removed keys become unknown-key cases rather than "
        "field cases."
    ],
    procedure="Remove `TestValidateDryRunTools` and the removed-map cases in `TestBuildApprovalConfig`, and add "
    "the case that a config containing a removed key is rejected as an unknown key.",
    method=[
        "Keep `TestBuildToolConfig`, `TestBuildLLMConfig` and the other groups unchanged."
    ],
    details=[
        "Verified 2026-11-21: 18 direct references; this file is named by rows 28, 31 and 32, so it keeps "
        "its own document."
    ],
    validation=["`uv run pytest tests/agent/test_config_builders.py -v`"],
    completion=[
        "The config-build tests assert the operational exceptions still load and the removed keys are "
        "rejected."
    ],
)

add(
    "tests/agent/services/test_config_reload.py",
    goal="Drop the hot-reload contract for the removed fields (REQ-005, REQ-011, REQ-013 / T-05).",
    design=[
        "Hot reload is asserted as accepting only the fields that remain; the policy-reapplication group keeps "
        "its behaviour without a tier map."
    ],
    procedure="Remove the removed-map cases from `TestApplyConfig` and `TestConfigReloadAtomicity`, update the "
    "field list asserted at lines 1167-1168, and change `TestRuntimeToolPolicyReapplication` to the "
    "reduced `apply_policy()` signature.",
    method=[
        "Keep the field-registry coverage test as the check that no removed field is registered."
    ],
    details=[
        "Verified 2026-11-21: 19 direct references; this file is named by rows 29 and 35, so it keeps its "
        "own document."
    ],
    validation=["`uv run pytest tests/agent/services/test_config_reload.py -v`"],
    completion=[
        "The hot-reload tests pass without supplying a removed map, and the field list they assert "
        "matches the registry."
    ],
)
