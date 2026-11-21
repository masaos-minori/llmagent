#!/usr/bin/env python3
"""_agentcfg003_content_agent.py — Authored content for the agentcfg003 agent-layer rows.

Private module for tools/generate_agentcfg003_procedures.py; cannot run standalone.
"""

from __future__ import annotations

from tools._agentcfg003_content_base import add

add(
    "scripts/agent/tool_policy.py",
    goal="Read declared metadata for tier, risk and key kinds, and invert the priority in "
    "`classify_operation_type()` so declared metadata is read first (REQ-004, REQ-006, REQ-007, REQ-008; "
    "AC-04, AC-06, AC-07).",
    design=[
        "Declared metadata is the decision input; the static sets are used only for drift comparison, which is "
        "the priority inversion the issue asks for.",
        "The tier-to-risk mapping stays, but its input becomes the declared tier instead of a configuration map.",
        "Plan-mode blocking is derived from the declared tier; `plan_blocked_tools` remains only as the "
        "documented exception denylist, and its current entries stay redundant by design (DT-03 Option A).",
    ],
    procedure="Replace the configuration-map reads with declared-field reads, and reorder the classification "
    "lookup so the declared value is consulted before the reference sets.",
    method=[
        "`classify_operation_type()` reads the declared `side_effect_class` first; the reference sets become a "
        "comparison that reports disagreement.",
        "`classify_risk()` loses the `approval_risk_rules` lookup and resolves from the declared tier's mapped "
        "risk, then the existing special-case and escalation rules.",
        "`is_plan_mode_blocked()` checks the documented denylist first, then the declared tier.",
        "`_escalate_for_path()` and `_escalate_for_github_branch()` resolve keys by the declared kind rather "
        "than by tool name, and `_configured_path_keys()` / `_iter_path_arg_values()` read the declared mapping "
        "filtered by kind.",
    ],
    details=[
        "Verified 2026-11-21: the current lookup order is `approval_risk_rules`, then `tool_safety_tiers`, then "
        "the constants default, then `medium`; the plan-mode rule reads `tool_safety_tiers` and the audit and "
        "policy key reads use `approval_resource_keys`.",
        "`repository_gateway.py` calls these functions through their existing signatures, so the public entry "
        "points are unchanged.",
    ],
    compat=[
        "This is the largest consumer surface in the plan; the caller signatures stay, so no caller change is "
        "needed beyond the removed configuration fields."
    ],
    security=[
        "Fail-closed behaviour for a tool absent from the registry is preserved (risk stays `high`)."
    ],
    completion=[
        "No decision path in this module reads a configuration map or a static tool-name set; only the "
        "drift comparison reads the reference data.",
        "A tool whose declared kind is `path` or `branch` escalates through the declared kind, and a "
        "`non_escalating` key does not.",
    ],
    validation=[
        "`uv run pytest tests/agent/test_tool_policy.py tests/agent/test_tool_policy_comprehensive.py -v`"
    ],
)

add(
    "scripts/agent/tool_approval.py",
    goal="Read the declared capability flag and remove `_KNOWN_DRY_RUN_CAPABLE_TOOLS` (REQ-004, REQ-009; "
    "AC-04, AC-08).",
    assumptions=[
        "The decision rules about what the preview shows stay with the preview work item; this row only "
        "changes where the capability value comes from."
    ],
    design=[
        "The preflight asks the declared flag for the entry it already resolves; the local tool-name set has "
        "no remaining reader once the configuration map is removed."
    ],
    procedure="Replace the local set and the `approval_dry_run_tools` read with the declared capability flag on "
    "the registry entry.",
    method=[
        "Remove `_KNOWN_DRY_RUN_CAPABLE_TOOLS` and the configuration-map lookup; keep the preflight order "
        "and the prompt behaviour unchanged."
    ],
    details=[
        "Verified 2026-11-21: `_KNOWN_DRY_RUN_CAPABLE_TOOLS` is a module-level set and "
        "`approval_dry_run_tools` is read in the same module; both readers disappear with this change."
    ],
    completion=[
        "`_KNOWN_DRY_RUN_CAPABLE_TOOLS` is gone, and the preflight's capability decision comes only from "
        "the declared flag."
    ],
)

add(
    "scripts/agent/tool_audit.py",
    goal="Resolve the operation type and the resource keys written to audit records from declared metadata "
    "(REQ-004, REQ-008; AC-04, AC-07).",
    design=[
        "The audit record keeps its key shape; only the source of the key names changes, from the "
        "`path_keys`/`branch_keys` configuration map to the declared key kinds."
    ],
    procedure="Change `_extract_resource_scope()` to group declared keys by kind, and remove the configuration-map "
    "union.",
    method=[
        "Keys typed `path` are read as path values, keys typed `branch` as branch values; `non_escalating` "
        "keys are not written to the audit scope.",
        "Keep the behaviour for a list value (non-empty elements joined with `;`) and the existing fallback "
        "for an unknown tool name, which now has no configuration source to fall back to.",
    ],
    details=[
        "Verified 2026-11-21: the current code unions `approval_resource_keys` `path_keys` with the "
        "declared `resource_scope_keys`, which is the double source REQ-011 removes."
    ],
    completion=[
        "The audit scope for a call is derived from the declared mapping only, and the recorded values "
        "are unchanged for the tools that exist today."
    ],
    compat=[
        "The ADR that cites this module's behaviour is updated by row 67; the audit record shape is not "
        "changed here."
    ],
)

add(
    "scripts/agent/tool_runner.py",
    goal="Read the retry class from the declared `retry_policy` instead of from `RETRYABLE_TOOLS` (REQ-004, "
    "REQ-007; AC-04, AC-09).",
    design=[
        "The declared value is the authority; the reference set remains for the drift comparison owned by "
        "row 05."
    ],
    procedure="Change `_classify_retry_class()` to read the entry's declared `retry_policy` and pass the "
    "classification to `scripts/shared/mcp_dedup.py`.",
    method=[
        "Remove the membership test against `RETRYABLE_TOOLS`; map the declared value to the existing "
        "classification the dedup path expects.",
        "Keep the existing retry limits and the existing reconciliation handling unchanged.",
    ],
    details=[
        "Verified 2026-11-21: the current function names `RETRYABLE_TOOLS` as the single source of truth "
        "and credits ADR-008; the ownership statement moves with the ADR row."
    ],
    completion=[
        "The classification applied to a call comes from the declared policy, and no membership test "
        "against a static set remains in this module."
    ],
)

add(
    "scripts/agent/production_config_validator.py",
    goal="Remove the tier-map validation and move the fail-closed check to declared metadata (REQ-004, REQ-011; "
    "AC-04, AC-05).",
    design=[
        "The removed keys become unknown keys and are rejected through the normal unknown-key path; no "
        "compatibility reader is added (REQ-011).",
        "The risk floor for the git tools stays, but its input becomes the declared tier/risk rather than a "
        "configuration map.",
    ],
    procedure="Remove `_check_missing_tool_safety_tiers()` and `_check_unknown_tool_safety_tiers()`, drop the "
    "removed keys from `_get_valid_production_keys()`, and express the fail-closed case as a missing "
    "declared field.",
    method=[
        "Keep the `_check_approval_risk_floor()` outcome for the named git tools, reading it from declared "
        "metadata.",
        "The registry-facing `validate_against_registry()` keeps its reporting shape.",
    ],
    details=[
        "Verified 2026-11-21: `_check_unknown_tool_safety_tiers()` is called from `validate()`; both tier "
        "checks read the removed map."
    ],
    completion=[
        "A configuration that still contains a removed map is rejected as an unknown key with the key "
        "named, and no tier-map check remains."
    ],
    security=[
        "A stale deployed `config/agent.toml` fails at startup with a named key; that is the intended "
        "behaviour, not a fallback kept for removed configuration."
    ],
)

add(
    "scripts/agent/startup_validation.py",
    goal="Update the startup failure text and the tier-check path to follow the removed maps (REQ-002, REQ-007; "
    "AC-02, AC-10).",
    design=[
        "The tier check becomes a drift report; the startup consequence it currently states as fatal is the "
        "wording owned by ADR-002 and is not restated here.",
        "A missing required field is reported through the fail-closed registration path, not through a "
        "tier-map check.",
    ],
    procedure="Remove the pipeline stage that reads the configuration tier map and reword the message that refers "
    "to it; keep the drift report as a non-decision finding.",
    method=[
        "Remove the `check_routing_safety_tiers` call and the stage name recorded in the result; the report "
        "content comes from the changed drift path (row 37).",
        "Keep the broad-catch shape so an exception in a report path does not change startup behaviour.",
    ],
    details=[
        "Verified 2026-11-21: the current message text names the tier map, and the check is invoked inside a "
        "broad catch."
    ],
    completion=[
        "No startup stage reads a removed configuration map; a disagreement is reported as a finding."
    ],
)

add(
    "scripts/agent/services/config_validators.py",
    goal="Remove `validate_tool_safety_tiers()` and its value check (REQ-005, REQ-011; AC-05).",
    design=[
        "The closed value set in the vocabulary module replaces the string check here; keeping both would be "
        "a second source for the same concept."
    ],
    procedure="Delete the function and its use as a field validator in the field registry (row 29).",
    method=["No replacement validator is added for the removed field."],
    details=[
        "Verified 2026-11-21: the function validates the tier strings of the removed map and is referenced "
        "from `scripts/agent/services/config_field_registry.py`."
    ],
    completion=[
        "The module no longer defines a validator for a removed configuration field, and the field "
        "registry no longer references it."
    ],
)

add(
    "scripts/agent/services/config_field_registry.py",
    goal="Remove the four removed configuration fields from the hot-reload field registry (REQ-005, REQ-011; "
    "AC-05).",
    design=[
        "No entry is kept as a compatibility reader: a removed key is unknown and rejected."
    ],
    procedure="Delete the registry entries for `tool_safety_tiers`, `approval_risk_rules`, "
    "`approval_dry_run_tools` and `approval_resource_keys`, and the import of the removed validator.",
    method=["Keep every other entry and the validation call shape unchanged."],
    details=[
        "Verified 2026-11-21: the entries carry the section name and the validator reference, so the import "
        "of `validate_tool_safety_tiers` and `validate_approval_risk_rules` must be checked against the "
        "remaining fields."
    ],
    completion=[
        "The registry no longer lists a removed field, and a configuration containing one is reported as "
        "an unknown key."
    ],
    compat=[
        "Hot reload accepts only the fields that remain; this is the intended change to the field set."
    ],
)

add(
    "scripts/agent/config_dataclasses.py",
    goal="Remove the four map fields from the approval configuration dataclass (REQ-005, REQ-006, REQ-008; "
    "AC-05, AC-06).",
    design=[
        "The dataclass keeps the operational exceptions only: protected paths, high-risk branches, allowed "
        "repos, and the raise-only exceptions.",
        "`plan_blocked_tools` stays as the documented exception denylist; it is not derived from a declared "
        "field and is not removed.",
    ],
    procedure="Delete the four field definitions and the default-factory use of the removed constants (row 69).",
    method=["Keep every other field, its default and its validator wiring unchanged."],
    details=[
        "Verified 2026-11-21: the four fields are built with `default_factory` from the constants in "
        "`scripts/agent/constants.py`, which becomes dead once this row lands."
    ],
    completion=[
        "No removed map field exists on the dataclass, and no default value for a removed concept "
        "remains in the module."
    ],
)

add(
    "scripts/agent/config_section_builders.py",
    goal="Remove the builders for the removed fields and the dry-run tool validation (REQ-005, REQ-009, REQ-011; "
    "AC-05).",
    design=[
        "No builder is retained to preserve a value that can be derived from a declared field."
    ],
    procedure="Delete the builders that populate the removed fields, remove `_validate_dry_run_tools()`, and "
    "remove its call from the approval-section builder.",
    method=[
        "Keep the builders for the remaining fields and the existing unknown-key handling."
    ],
    details=[
        "Verified 2026-11-21: `_validate_dry_run_tools()` builds its supported set from the removed "
        "constants and is called from the approval-section builder; both the function and its supported-set "
        "read disappear with this row."
    ],
    completion=[
        "The config-build path produces no value for a removed field, and the removed validator is not "
        "called from anywhere."
    ],
)

add(
    "scripts/agent/constants.py",
    goal="Remove the default constants for the removed maps so each concept has one source (REQ-011).",
    assumptions=[
        "The constants are read only by the builders and the dataclass defaults, which are removed by "
        "rows 30 and 31; no test references them."
    ],
    design=[
        "Leaving the definitions as dead constants would keep a second source for a concept the plan removes, "
        "so the definitions are deleted rather than left unused."
    ],
    procedure="Delete `_DEFAULT_APPROVAL_RISK_RULES`, `_DEFAULT_RESOURCE_KEYS` and `_DEFAULT_DRY_RUN_TOOLS` and "
    "their imports in the modules that used them.",
    method=[
        "Keep `_DEFAULT_PLAN_BLOCKED_TOOLS`, `_DEFAULT_PROTECTED_PATHS`, the high-risk branch and allowed-repo "
        "defaults, and the shell safe prefixes: those are operational exceptions the plan keeps."
    ],
    details=[
        "Verified 2026-11-21: no test references these three constants; the test fixtures use their own "
        "mirror values, which the test rows update."
    ],
    completion=[
        "The module defines no default value for a removed concept, and `uv run ruff check scripts/` "
        "reports no unused import."
    ],
)

add(
    "scripts/agent/services/mcp_status.py",
    goal="Derive a server's risk level from the declared tiers instead of the configuration map (REQ-004; AC-04).",
    design=[
        "The display value is still the highest risk among the server's tools; only its source becomes the "
        "declared field."
    ],
    procedure="Change `_tier_for_server()` and the probe path to read the declared tier on each registered entry.",
    method=[
        "Remove the `tool_safety_tiers` argument and the dictionary read; iterate the registry entries the "
        "server owns.",
        "Keep the `McpTier` output shape so the `/mcp` status display is unchanged.",
    ],
    details=[
        "Verified 2026-11-21: the current code reads `ctx.cfg.approval.tool_safety_tiers` and the highest-"
        "risk helper over that map."
    ],
    completion=[
        "A server's displayed level comes from the declared tiers, and no configuration map is read."
    ],
)

add(
    "scripts/agent/services/config_service_sync.py",
    goal="Change the tier mapping type and its source (REQ-004; AC-04).",
    design=[
        "The sync path no longer builds a policy-derived tier map, because the registry keeps the declared "
        "value (row 04)."
    ],
    procedure="Remove the `tool_safety_tiers` mapping construction and the argument passed to `apply_policy()`.",
    method=[
        "Keep the rest of `sync_all()` and the hot-reload behaviour unchanged; the field set it validates is "
        "the one from row 29."
    ],
    details=[
        "Verified 2026-11-21: the current code passes a `Mapping[str, AgentSafetyTier]` built from the "
        "removed configuration field."
    ],
    completion=[
        "No removed configuration field is read here, and `apply_policy()` is called without a tier map."
    ],
)

add(
    "scripts/agent/commands/cmd_config_display.py",
    goal="Remove the display lines for the removed maps (REQ-05 placeholder; AC-05).",
    design=[
        "No substitute line is added: the values they showed no longer exist as configuration."
    ],
    procedure="Remove the risk-rule, dry-run, tool-safety-count lines from the approval and tool-safety display "
    "sections.",
    method=["Keep the remaining display sections and the output shape unchanged."],
    details=[
        "Verified 2026-11-21: the display reads `approval_risk_rules`, `approval_dry_run_tools` and the "
        "count of `tool_safety_tiers` entries."
    ],
    completion=["The config display prints no line for a removed field."],
)

add(
    "scripts/agent/services/routing_drift.py",
    goal="Turn the tier drift check into a report against declared metadata (REQ-007; AC-10).",
    design=[
        "The report names a disagreement between a declaration and the reference data and changes no "
        "decision; the startup consequence stays owned by ADR-004 and is not restated here."
    ],
    procedure="Remove the configuration-map argument from `check_routing_safety_tiers()` and let the changed "
    "shared check (row 07) produce the findings.",
    method=[
        "Keep the function's return shape (a list of messages) and its call site in the startup pipeline.",
        "Rename the reported stage only where the message names the removed map (row 27).",
    ],
    details=[
        "Verified 2026-11-21: the current function builds a findings list from "
        "`check_tool_safety_tiers(tool_safety_tiers=...)`."
    ],
    completion=[
        "The function returns findings that compare declarations with reference data, and nothing that "
        "consumes them changes a decision."
    ],
)

add(
    "scripts/agent/services/mcp_tool_discovery.py",
    goal="Compare declared write classification with the reference sets only as a drift report (REQ-007; AC-10).",
    design=[
        "The existing ADR-003 INV-03 report keeps its shape; its wording states that the declared value is "
        "the authority and the reference sets are comparison data."
    ],
    procedure="Change `_build_write_classification_findings()` to read the declared field and keep the comparison "
    "with the reference sets as a finding only.",
    method=[
        "Keep the security-posture gate and the existing finding aggregation unchanged."
    ],
    details=[
        "Verified 2026-11-21: the current finding text describes a disagreement between the runtime flag and "
        "the static tool sets; with the priority inverted, the declared value is the reference and the "
        "static set is the comparison."
    ],
    completion=[
        "The finding reports disagreement without changing any decision, and the phrase that presents the "
        "static sets as the authority is removed."
    ],
)

add(
    "scripts/agent/services/mcp_tool_discovery_registry.py",
    goal="Build registered tools through the extended required field set (REQ-002, REQ-003; AC-02, AC-03).",
    assumptions=[
        "The field set and the vocabulary come from rows 01, 02, 08 and 68 in the same release unit."
    ],
    design=[
        "The discovery path passes the values the producer declared; it does not supply defaults, so an entry "
        "that omits a field is rejected before registration."
    ],
    procedure="Pass the new required fields from the `/v1/tools` entry to `build_runtime_tool()` in "
    "`_build_runtime_tools()` and `_dedupe_and_build()`.",
    method=[
        "Keep the duplicate detection and the single-assignment install behaviour unchanged.",
        "Keep the exclusion of a server whose security posture is not accepted unchanged.",
    ],
    details=[
        "Verified 2026-11-21: the module builds `RuntimeTool` instances from the discovered definitions, so "
        "it is the path that turns a producer declaration into a registry entry."
    ],
    completion=[
        "An entry that omits a required field is not registered, and a complete entry is registered with "
        "the values it declared."
    ],
    compat=[
        "The contract test that asserts this behaviour lives in "
        "`tests/shared/test_runtime_tool_registry.py`, which is a separate document in this pass."
    ],
)
