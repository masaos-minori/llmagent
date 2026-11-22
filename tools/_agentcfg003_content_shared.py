#!/usr/bin/env python3
"""_agentcfg003_content_shared.py — Authored content for the agentcfg003 shared-layer rows.

Private module for tools/generate_agentcfg003_procedures.py; cannot run standalone.
"""

from __future__ import annotations

from tools._agentcfg003_content_base import add

add(
    "scripts/shared/tool_metadata.py",
    goal="Define the closed policy vocabulary the runtime contract uses (REQ-001, REQ-003): side-effect "
    "class, retry policy, reconciliation policy, resource-key kind, capability flag values, and the "
    "single field-set version constant, in the `shared` leaf layer.",
    assumptions=[
        "`shared` stays an import-linter leaf, so this module must not import anything from `agent`.",
        "The owner decision recorded on 2026-11-21 extends the resource-key kind set with a value for keys "
        "that no escalation rule reads; the plan's closed set named only `path`, `branch`, `repo`.",
    ],
    design=[
        "Values are declared as `Literal` aliases plus the matching `frozenset` of allowed values, so the "
        "type checker and `validate_tool_schema_v2()` read the same definition and cannot drift.",
        "The field-set version is one module-level constant, not a per-tool literal (REQ-003). Its value is "
        "UNK-01 and is not chosen by this procedure.",
        "No per-tool constants are introduced here; per-tool values stay in the producer declarations.",
    ],
    procedure="Create the module with one type alias and one closed value set per vocabulary dimension, plus "
    "the version constant.",
    method=[
        "`SideEffectClass` (new) with values `read_only` (new), `local_write` (new), `external_write` (new).",
        "`RetryPolicy` (new) with values `never` (new), `safe_read_retry` (new), `same_logical_call_only` (new), "
        "`reconcile_then_retry` (new).",
        "`ReconciliationPolicy` (new) with values `not_required` (new), `local_state` (new), "
        "`external_state` (new).",
        "`ResourceKeyKind` (new) with values `path`, `branch`, `repo`, and `non_escalating` (new) for keys no "
        "escalation rule reads.",
        "`PreviewCapability` (new): the closed set holds only the values the approval preflight needs now; the "
        "preview-display values stay with the preview work item (UNK-02).",
        "`TOOL_FIELD_SET_VERSION` (new): the single place the version value is written.",
    ],
    details=[
        "Verified 2026-11-21: `AgentSafetyTier` is currently defined only in `scripts/shared/runtime_tool.py`, "
        "so moving the vocabulary here has no second definition to reconcile.",
        "Existing verified values of `resource_scope_keys` include keys that the three named kinds cannot "
        "classify (`owner`, `run_id`, `workflow`, `source`, `destination`); that is the reason for the "
        "`non_escalating` (new) value.",
    ],
    compat=[
        "Producers and Agent consumers both read this module, so it must stay importable from both sides."
    ],
    security=[
        "Closed value sets are the enforcement point for REQ-001: an open value would let a producer "
        "declare a value no consumer can interpret."
    ],
    validation=[
        "`uv run pytest tests/shared/test_tool_metadata.py -v`",
        "`PYTHONPATH=scripts uv run lint-imports` (shared stays a leaf)",
    ],
    completion=[
        "Every vocabulary dimension is a closed set with no per-tool constant, and the module imports "
        "nothing from `agent`.",
        "The version value appears in exactly one place in the repository.",
    ],
    out_of_scope=[
        "The decision rules that use the capability flag (preview work item), and the call-state "
        "contract (REQ-010)."
    ],
)

add(
    "scripts/shared/runtime_tool.py",
    goal="Add the typed metadata fields to `RuntimeTool` and remove the risk-lowering default from "
    "`build_runtime_tool()` (REQ-002, AC-02).",
    assumptions=[
        "The vocabulary comes from `scripts/shared/tool_metadata.py` (row 01), which lands in the same release unit."
    ],
    design=[
        "`build_runtime_tool()` keeps its shape; only the required argument set grows, so producer call sites "
        "keep their current style.",
        "`agent_safety_tier` becomes a required argument: the current `WRITE_DANGEROUS` default is the last "
        "default that lowers risk, and it is removed rather than re-pointed at another default.",
    ],
    procedure="Extend the `RuntimeTool` TypedDict with the new required fields and change `resource_scope_keys` "
    "to the key-to-kind mapping; remove the `agent_safety_tier` default from `build_runtime_tool()`.",
    method=[
        "New required fields on `RuntimeTool` (new): `side_effect_class` (new), `retry_policy`, "
        "`reconciliation_policy` (new), `idempotency_required` (new), `preview_capability` (new), "
        "`policy_version`.",
        "`resource_scope_keys` value type becomes the key-to-`ResourceKeyKind` mapping.",
        "No default value is added for any new field: a missing value raises, matching the current behavior of "
        "the four schema-2.0 fields.",
    ],
    details=[
        "Verified 2026-11-21: `AgentSafetyTier` currently defaults to `WRITE_DANGEROUS` and `is_write`, "
        "`requires_serial`, `resource_scope_kind`, `resource_scope_keys` are required.",
        "The shared test factory `tests/shared/runtime_tool_factory.py` is the only place that supplies the "
        "permissive defaults; production call sites must not gain defaults.",
    ],
    compat=[
        "Every producer declaration and every consumer that reads these fields is in the same release unit; "
        "this file alone does not pass validation."
    ],
    security=[
        "REQ-002 is fail-closed: an absent value must raise at build time, not fall back to a lower-risk "
        "value."
    ],
    completion=[
        "`build_runtime_tool()` rejects a call that omits any required field, and no default that "
        "lowers risk remains in the function.",
        "The import-linter contract keeps `tests/shared/runtime_tool_factory.py` out of production "
        "imports.",
    ],
)

add(
    "scripts/shared/resource_scope.py",
    goal="Extend `validate_tool_schema_v2()` to the required field set and resolve scope keys through the "
    "declared key kinds (REQ-002, REQ-008; AC-02, AC-07).",
    design=[
        "The validator reports a missing required field as a problem, which is how the registration path already "
        "excludes an incomplete entry; no new failure mode is introduced.",
        "Kind-based reading replaces tool-name reading: the resolver keeps its composed-kind behaviour and reads "
        "the mapping instead of a key list.",
    ],
    procedure="Add the new required fields to the field set the validator checks, and read `resource_scope_keys` "
    "as a key-to-kind mapping.",
    method=[
        "The field set named by `TOOL_SCHEMA_V2_FIELDS` is read from the same definition the producers are "
        "checked against, so the validator and the contract test cannot disagree.",
        "`resolve_resource_scopes()` and `_scope_keys_problems()` resolve kinds from the mapping; keys typed "
        "`non_escalating` still resolve a scope string but are never used by an escalation rule.",
    ],
    details=[
        "Verified 2026-11-21: `validate_tool_schema_v2()` is the enforcement point named by "
        "`docs/22_mcp/mcp_06_11_new-tool-registration-procedure.md`; `_COMPOSED_KIND_SEPARATORS` handles the "
        "composed kinds, and an unscoped tool returns an empty tuple.",
    ],
    compat=[
        "Changing the value type is a contract change for every producer literal, so it lands with rows 08 "
        "and 68 in the same release unit."
    ],
    security=[
        "Fail-closed behaviour for a missing field is preserved; the fallback write scope for an "
        "unresolved write tool is unchanged."
    ],
)

add(
    "scripts/shared/runtime_tool_registry.py",
    goal="Stop applying a configuration-derived safety tier in `apply_policy()` (REQ-004, REQ-005; AC-04).",
    assumptions=[
        "The change to ADR-003 Decision 9 needs a maintainer approval record (UNK-04); if it is not "
        "given, this row keeps its current behaviour and is re-scoped."
    ],
    design=[
        "The tier a tool carries is the declared value, so `apply_policy()` no longer has a policy-derived "
        "tier to overwrite; the single-assignment install behaviour stays as ADR-003 Decision 9 describes."
    ],
    procedure="Remove the tier-map argument and the tier overwrite from `apply_policy()`; keep the complete-"
    "replacement-and-single-assignment behaviour.",
    method=[
        "Drop the `tier_map` parameter and the per-tool tier lookup; the mapping is built from the "
        "registered entries as they already are."
    ],
    details=[
        "Verified 2026-11-21: `apply_policy()` is called with `ctx.cfg.approval.tool_safety_tiers` from "
        "`scripts/agent/services/config_service_sync.py`, so removing the field here also removes the "
        "caller's argument (row 35)."
    ],
    completion=[
        "After a policy application, the tier a lookup returns is the tier the entry was declared with, "
        "and no configuration source is read."
    ],
)

add(
    "scripts/shared/tool_constants.py",
    goal="Demote the static tool-name sets to reference data used only for drift detection and tests, and move "
    "`RETRYABLE_TOOLS` ownership to the declared retry policy (REQ-007; AC-04, AC-10).",
    assumptions=[
        "The per-server tool lists used inside an MCP server for its own write-protection gate are out "
        "of scope (UNK-05)."
    ],
    design=[
        "The sets stay in the module as reference data because the drift checks need something to compare a "
        "declaration against; what changes is that no decision reads them.",
        "`RETRYABLE_TOOLS` is kept as reference data only, with a note that the declared `retry_policy` is "
        "the authority; the ownership statement is recorded in the ADR change (row 67).",
    ],
    procedure="Mark the sets as reference data in the module docstring and comments, and remove their use as a "
    "decision input from this module's own helpers.",
    method=[
        "Keep the existing `READ_TOOLS`, `WRITE_TOOLS`, `DELETE_TOOLS`, `RETRYABLE_TOOLS` and the "
        "per-server sets unchanged in content; the change is the stated role, so a reader cannot mistake a "
        "drift report for a decision.",
        "Keep the existing note that the classification dimensions are not to be conflated, and restate it "
        "in terms of declared fields.",
    ],
    details=[
        "Verified 2026-11-21: `RETRYABLE_TOOLS` is currently named as the single source of truth by "
        "`scripts/agent/tool_runner.py`, which credits ADR-008; that credit is what the ADR row records as "
        "moved."
    ],
    completion=[
        "No runtime decision reads a set in this module; only drift comparisons and tests read it.",
        "The drift test against the shared dedup config `[retry_class]` mirror still compares declarations with this data.",
    ],
    compat=[
        "Tests that assert ownership of `RETRYABLE_TOOLS` are updated by the companion test file listed on "
        "this row."
    ],
)

add(
    "scripts/shared/mcp_dedup.py",
    goal="Take the retry classification from the caller-supplied declared policy instead of from a static "
    "reference set (REQ-007, REQ-010; AC-09).",
    assumptions=[
        "The `[retry_class]` mirror in the shared dedup config stays as a drift comparison; its removal is "
        "decided by the open dedup configuration issue (UNK-06).",
        "The call-state contract itself stays with the MCP two-layer defense issues (REQ-010).",
        "The lease/identity contract in this module is covered by "
        "`implementations/20261121-093956_01_scripts_shared_mcp_dedup.py.md` from the earlier dedup plan; this "
        "document covers only the retry-classification input, so the two documents do not overlap.",
    ],
    design=[
        "The module receives the classification as an argument; it keeps no ownership of retry behaviour.",
        "The comparison against the shared dedup config mirror stays, but its result is reported as a disagreement "
        "and cannot change the classification used for a call.",
    ],
    procedure="Change the classification input from the reference set to the declared policy value, and turn the "
    "existing cross-check into a drift finding.",
    method=[
        "The caller (`scripts/agent/tool_runner.py`, row 25) supplies the declared `retry_policy`; this file "
        "does not read `RETRYABLE_TOOLS`.",
        "Keep the reconciliation behaviour and the existing cross-check output, and label the output as a "
        "drift finding.",
    ],
    details=[
        "Verified 2026-11-21: the cross-check reads the shared dedup config's `[retry_class]` map against "
        "`RETRYABLE_TOOLS`; this is the reconciliation coupling the issue describes, not "
        "`scripts/db/recovery.py`."
    ],
    completion=[
        "A disagreement between a declaration and the mirror is reported without changing the "
        "classification applied to the call."
    ],
)

add(
    "scripts/shared/tool_routing_validation.py",
    goal="Make the tier checks drift reports rather than decision inputs (REQ-007; AC-10).",
    design=[
        "The checks compare declared metadata with the reference data and return findings; nothing that reads "
        "the result changes a decision."
    ],
    procedure="Change `check_tool_safety_tiers()` and `check_unknown_tool_safety_tiers()` to compare declared "
    "tiers with the reference data, and remove the configuration-map argument.",
    method=[
        "Read the registry's declared tiers instead of `cfg.approval.tool_safety_tiers`; keep the message "
        "shape so the callers' report paths do not change.",
        "Keep the startup consequence owned by ADR-004 as it is written today, and do not restate it here.",
    ],
    details=[
        "Verified 2026-11-21: both functions are called from `scripts/agent/services/routing_drift.py`, "
        "which is updated by row 37; `test_tool_routing_validation.py` is not a row of this plan."
    ],
    completion=[
        "A disagreement is reported as a finding, and no caller uses the result to classify a tool."
    ],
    out_of_scope=[
        "The test file that exercises these functions through fixtures only (covered by the follow-up "
        "test-audit work item)."
    ],
)

add(
    "scripts/mcp_servers/server.py",
    goal="Extend the per-tool required field set that a `/v1/tools` response must carry (REQ-003; AC-03).",
    design=[
        "`MCP_TOOL_SCHEMA_VERSION` stays at its current value: only the required field set grows, so the "
        "envelope contract tests are not affected.",
        "The field-set version is imported from `scripts/shared/tool_metadata.py` so it is recorded in one "
        "place; this module does not define a second copy.",
    ],
    procedure="Add the new fields to `TOOL_SCHEMA_V2_FIELDS` and read the version constant from the vocabulary "
    "module.",
    method=[
        "Keep the existing four schema-2.0 field names unchanged and append the new required names.",
        "Keep validation behaviour: an entry missing a required field is reported, not defaulted.",
    ],
    details=[
        "Verified 2026-11-21: `TOOL_SCHEMA_V2_FIELDS` lists the four required keys and "
        "`MCP_TOOL_SCHEMA_VERSION` is the envelope value."
    ],
    completion=[
        "Every producer entry that declares the extended set passes validation; an entry that omits a "
        "field is rejected.",
        "The envelope version value is unchanged from the current one.",
    ],
    compat=[
        "This is the contract the 13 producer files must satisfy, so the row lands in the same release unit."
    ],
)

add(
    "scripts/mcp_servers/models.py",
    goal="Declare the extended required field set on the `McpTool` TypedDict that every producer `TOOL_LIST` "
    "literal is typed against (REQ-003; AC-03).",
    assumptions=[
        "This row was added during procedure generation by the owner's decision: the producer literals "
        "cannot type-check against the extended set without the TypedDict being extended."
    ],
    design=[
        "Use the type aliases from `scripts/shared/tool_metadata.py` as the value types, so the TypedDict and "
        "the closed value sets have one definition.",
        "`resource_scope_keys` value type becomes the key-to-`ResourceKeyKind` mapping, matching row 03.",
    ],
    procedure="Add the new `Required[]` entries to `McpTool` and change the `resource_scope_keys` annotation to "
    "the mapping type.",
    method=[
        "No field is added as `NotRequired`: a field the plan requires must be declared, so an omitted key "
        "fails at type-check time as well as at validation."
    ],
    details=[
        "Verified 2026-11-21: `McpTool` currently declares `name`, `description`, `inputSchema`, `status`, "
        "`config_dependent`, `is_write`, `requires_serial`, `resource_scope_kind`, `resource_scope_keys` as "
        "`Required`; producer literals are typed as `list[McpTool]`."
    ],
    completion=[
        "Every producer literal carries the extended set, and `uv run mypy --no-namespace-packages "
        "scripts/ tests/eventbus tools` reports no missing key.",
        "The value types are the same definitions the contract test checks.",
    ],
    compat=[
        "The TypedDict is the type the 13 producer files are written against; it lands with them in the same "
        "release unit."
    ],
)

add(
    "config/agent.toml",
    goal="Remove the four map sections from the shipped configuration and keep the operational exceptions "
    "(REQ-005, REQ-006; AC-05, AC-06).",
    design=[
        "The file keeps `plan_blocked_tools` and the operational exception lists; nothing is added to carry "
        "the removed values, so a deployed file that still contains a removed section is rejected as an "
        "unknown key."
    ],
    procedure="Delete the `[approval_risk_rules]`, `[approval_resource_keys]` and `[tool_safety_tiers]` sections "
    "and the `approval_dry_run_tools` key; update the comments that state the removed precedence.",
    method=[
        "Keep `approval_protected_paths`, `approval_high_risk_branches`, `approval_github_allowed_repos` and "
        "the raise-only exceptions unchanged.",
        "Keep the `plan_blocked_tools` entry and restate its comment as a documented exception denylist on "
        "top of the declared tier.",
    ],
    details=[
        "Verified 2026-11-21: the comments above `plan_blocked_tools` state that the tier map is the rule "
        "and the list is an extension; that wording is what the ADR and doc rows change."
    ],
    completion=[
        "No removed key appears in the file, and the operational exception keys still load."
    ],
    compat=[
        "`deploy/deploy.sh` copies `config/agent.toml` as-is, so only the deployed copy must be re-copied; "
        "no script change is in scope."
    ],
    out_of_scope=[
        "The deployed copy of the file and the test fixtures that supply the removed maps (row 56 and "
        "the follow-up test-audit work item)."
    ],
)

add(
    "registry/manifests/config_ownership.yaml",
    goal="Remove the ownership entries for the four removed fields (REQ-005, REQ-011; AC-05).",
    procedure="Delete the entries whose `field` is a removed key, including the validator reference left by row 28.",
    design=[
        "The manifest is the ownership record for configuration fields, so a removed field has no entry to keep; "
        "no entry is retained as a compatibility marker.",
    ],
    method=["Keep every other entry and the manifest structure unchanged."],
    details=[
        "Verified 2026-11-21: the entries name the removed fields and one references "
        "`validate_approval_risk_rules` and `validate_tool_safety_tiers`."
    ],
    completion=[
        "`uv run python tools/check_config_ownership.py` reports no entry for a removed field."
    ],
    validation=["`uv run python tools/check_config_ownership.py`"],
)

add(
    "docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md",
    goal="Record the decision and invariant change that moves authority from configuration maps and static sets to "
    "declared metadata, with the maintainer approval record (REQ-012; AC-11).",
    assumptions=[
        "The approval record must be written in the same change as the code; this document records the "
        "requirement and cannot supply the approval, so Phase 1 stops if the approval is not given "
        "(UNK-03, UNK-04)."
    ],
    design=[
        "Decisions 2, 5, 8, 9 and 14 are the statements this change touches; each is edited only where the "
        "authority source changes, and no other decision is restated."
    ],
    procedure="Update Decision 2 (the fields `RuntimeTool` holds), Decision 5 (static definitions limited to "
    "tests, expected values and documentation generation), Decision 8 (the declared tier and write "
    "attributes as the shared reference), Decision 9 (`apply_policy()` no longer applies a "
    "configuration-derived tier) and Decision 14 (reload does not update a tier that is declared rather "
    "than policy-derived).",
    method=[
        "Add the `RETRYABLE_TOOLS` ownership statement that `scripts/agent/tool_runner.py` credits to ADR-008, "
        "and name the declared `retry_policy` as the owner.",
        "Add the maintainer approval record line for the decision/invariant change, as "
        "`docs/10_adr/adr_02_07_016_adr-authority-model.md` requires.",
        "Keep the invariant matrix entries consistent with the changed decisions.",
    ],
    details=[
        "Verified 2026-11-21: Decision 5 already limits static definitions to tests and documentation, so "
        "the change is the wording that makes drift comparison the only use; Decision 14 currently states "
        "that reload updates policy-derived fields including Safety Tier, which is what the approval changes."
    ],
    completion=[
        "The ADR names declared metadata as the authority for the concepts this plan moves, and the "
        "approval record is present in the same change.",
        "`uv run python tools/check_adr_reference.py` and `uv run python tools/check_adr_invariant_matrix.py` "
        "pass.",
    ],
    validation=[
        "`uv run python tools/check_adr_reference.py`",
        "`uv run python tools/check_adr_invariant_matrix.py`",
    ],
    exec_steps=[
        [
            "1",
            "Write the decision/invariant change and the approval record",
            "Blocked",
            "—",
            "—",
            "Phase 1; needs the maintainer approval record (UNK-03, UNK-04)",
        ],
        ["2", "Run the ADR checkers", "Pending", "—", "—", ""],
    ],
    blockers=[
        [
            "1",
            "ADR decision/invariant change requires a maintainer approval record (UNK-03, UNK-04)",
            "No",
            "—",
        ]
    ],
    out_of_scope=[
        "The ADR-004 startup-abort consequence, which this change must not restate.",
        "The field-set version value (UNK-01), which is decided with the MCP contract owner.",
    ],
)
