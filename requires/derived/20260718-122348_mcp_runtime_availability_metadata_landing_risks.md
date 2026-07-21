# RuntimeToolRegistry / MCP runtime-availability-metadata migration (requirements 14-20): consolidated landing-status risks (2026-07-18)

**Largely resolved (2026-07-20/21), one gap remains.** Verified against current source:

- **Requirement 14** (`requires_config` → `config_dependent`): fully landed. `grep -rn "requires_config" scripts/` returns 0 matches; `config_dependent` is the live field name (13 matches).
- **Requirement 15** (`enabled`/`disabled_reason` in `/v1/tools`): landed for all 4 originally-targeted handlers plus more — `scripts/mcp_servers/file/{read,write,delete}_server.py` and `scripts/mcp_servers/git/git_server.py` all compute and return `(enabled, disabled_reason)` via `availability_flags()`/per-tool helpers.
- **Requirement 17** (`RuntimeToolRegistry` wiring): fully resolved, and then some — `McpToolDiscoveryService` is now wired into `startup.py`/`context.py` (landed 2026-07-20 in commit `d510c87f`), and a same-day later change made `RuntimeToolRegistry` the **sole** routing authority (removing the `ToolRegistry` fallback entirely — see `docs/04_mcp_03_01_dispatch-and-routing.md` / `04_mcp_03_02_tool-registry.md`). No longer "inert" in any sense.
- **Requirement 19** (`docs/04_mcp_03_06_tool-runtime-availability-metadata.md`): exists and has been kept current through several rounds of edits since.
- **Requirement 20** (`include_disabled`/`disabled_code`): still zero matches in `scripts/` — but per the original issue text this was always meant to stay a documented-but-deferred, on-paper proposal, not a landing gap. No action needed.

**Remaining gap, not yet closed — worse than first described (2026-07-21 re-investigation):** `enabled`/`disabled_reason` are computed and returned by the 4 servers above, but `scripts/agent/services/mcp_tool_discovery.py` still does not read them when building each `RuntimeTool` — `build_runtime_tool()`'s `enabled_for_llm` parameter is never passed a value derived from the live response's `enabled` field, and `build_runtime_tool()` defaults `enabled_for_llm` to `False` when omitted. Tracing the consumer side (`RuntimeToolRegistry.llm_tool_definitions()` → `llm_turn_runner.py::_filter_disabled_tool_definitions()`) shows this is not merely "a disabled tool stays visible" — it is the inverse and far more severe: **every discovered tool has `enabled_for_llm=False`, so `_filter_disabled_tool_definitions()` filters ALL of them out of the LLM's tool payload once `ctx.services_required.runtime_tools` is populated** (which `startup.py:230` does on every successful discovery — the normal case, not an edge case). This is plausibly a full agent tool-calling outage under ordinary operation, not a cosmetic metadata gap. Filed as `requires/20260721_03_require.md` (Critical) for a proper fix — do not treat as a minor follow-up.

## Context

This note consolidates three separate risk files that all trace back to the same root cause — the
`RuntimeToolRegistry` / MCP tool-availability-metadata plan batch (requirements 14-20, all authored
2026-07-17) depends on a chain of sibling plans, several of which had not landed in real `scripts/`
source at authorship time:

- Requirement 14 — `plans/done/20260717-173602_plan.md`: rename `requires_config` → `config_dependent`.
- Requirement 15 — `plans/done/20260717-174024_plan.md`: add `enabled`/`disabled_reason` to `/v1/tools`.
- Requirement 17 — `plans/done/20260717-175327_plan.md`: `RuntimeToolRegistry` (disabled-tool
  visibility, hidden from the LLM).
- Requirement 19 — `plans/done/20260717-180307_plan.md`: document the `config_dependent`/`enabled`/
  `disabled_reason` contract in a new file, `docs/04_mcp_03_06_tool-runtime-availability-metadata.md`.
- Requirement 20 — `plans/done/20260717-181151_plan.md`: evaluate (not implement) two further options,
  `include_disabled` query param and a `disabled_code` structured enum.

All five plans are filed under `plans/done/` — that reflects **planning-phase** completion only, not
that the described code/doc artifacts exist yet. This consolidated note replaces the following three
files, each individually rewritten once already (2026-07-18) with the same investigation, now merged
here and removed:

- `issues/20260717-175327_risks.md` (requirement 17's RuntimeToolRegistry-depends-on-15 risk)
- `issues/20260717-180437_risks.md` (requirement 19's doc-drift risk)
- `issues/20260717-181151_risks.md` (requirement 20's two deferred-options risks)

## Current status (verified 2026-07-18)

**Requirement 17 (RuntimeToolRegistry) — partially implemented, not wired in**

- `scripts/shared/runtime_tool.py`, `scripts/shared/runtime_tool_registry.py`, and
  `scripts/agent/services/mcp_tool_discovery.py` exist as real source and implement the base shape
  (`RuntimeTool` dataclass, `build_runtime_tool()`, `RuntimeToolRegistry`, `McpToolDiscoveryService`).
- However, `grep -rln "McpToolDiscoveryService\|RuntimeToolRegistry" scripts/` returns matches only
  inside those three files themselves — nothing in `agent/context.py`, `agent/startup.py`,
  `agent/factory.py`, `route_resolver.py`, `tool_policy.py`, or `tool_runner.py` references them.
  `AppServices` has no `runtime_tools` field. The registry is built by nothing and consulted by nothing
  at runtime. Both `runtime_tool_registry.py`'s own docstring and
  `docs/04_mcp_03_02_tool-registry.md:134` ("将来の追加: RuntimeToolRegistry とライブ検出（未配線）")
  already say this explicitly — code and docs agree, no drift here.
- The implemented `mcp_tool_discovery.py` does **not** read `enabled`/`disabled_reason` at all — it
  validates/consumes `status`, `is_write`, `requires_serial`, `resource_scope` only. Requirement 15
  never landed, so requirement 17 shipped independent of it rather than against a mismatched shape.

**Requirements 14/15 (`config_dependent`, `enabled`/`disabled_reason`) — not implemented in source**

- `grep -rn "disabled_reason\|config_dependent" scripts/` returns **zero matches**. The four target
  handlers (`scripts/mcp_servers/file/read_server.py`, `write_server.py`, `delete_server.py`,
  `scripts/mcp_servers/git/server.py`) are unchanged from their pre-plan `list_tools()` shape.
- `grep -rn "requires_config" scripts/` returns 51 occurrences across 10 files — `requires_config` is
  still the live field name everywhere; requirement 14's rename has not landed either.

**Requirement 19 (`docs/04_mcp_03_06_tool-runtime-availability-metadata.md`) — target file does not exist**

- `find docs -iname "04_mcp_03_06*"` returns **zero matches**. There is no live documentation yet that
  could be drifting from anything — the doc-drift risk this requirement originally raised has not had
  a chance to materialize.

**Requirement 20 (deferred `include_disabled` / `disabled_code`) — both proposals remain unimplemented**

- `grep -rn "disabled_code" scripts/` returns zero matches; `include_disabled` is not a recognized
  `/v1/tools` query parameter anywhere. Both remain purely evaluated, on-paper proposals, as intended.

**New since the original notes: a large 2026-07-18 `implementations/` batch addresses these gaps, but is documents-only so far**

`implementations/20260718-095246_requirements_14_15_landing_check_for_availability_metadata_schema_tests.md`
states outright: "no real source changes have been made by ANY plan in this batch yet — this entire
batch produces `implementations/*.md` design/procedure docs only, not code." Relevant docs, mapped to
which original risk they address:

| Doc | Addresses |
|---|---|
| `implementations/20260718-111454_context_py_appservices_runtime_tools.md` | Wires `RuntimeToolRegistry` into `AppServices`/`_check_services()` — the fix for requirement 17's "not wired in" gap. |
| `implementations/20260718-094534_requirement_17_disabled_reason_landing_check.md` | Mechanical pre-merge check (`grep -rn "disabled_reason" scripts/mcp_servers/`) with a concrete landed/not-landed branch — answers the original "no cross-plan tracking" concern. |
| `implementations/20260718-095246_requirements_14_15_landing_check_for_availability_metadata_schema_tests.md` | Analogous gate for requirement 18's schema tests, using `xfail(strict=True)` so drift surfaces as a hard failure. |
| `implementations/20260718-085909_read_tools.py.md` through `..._full_validation_pass_call_tool_disabled_gate.md`, plus `..._read_server.py.md` / `..._write_server.py.md` / `..._delete_server.py.md` / `..._git_server.py.md` / `..._common.py.md` | The not-yet-executed implementation lineage for requirement 15 itself. |
| `implementations/20260718-101441_04_mcp_03_06_tool-runtime-availability-metadata.md` | Step-by-step procedure for creating requirement 19's target file — already bakes in an **"Implementation status" callout** at the top of the body (Design item 0), which is exactly the mitigation the original doc-drift risk asked for. |
| `implementations/20260718-102011_04_mcp_03_06_future_options_appendix.md` | Requirement 20's Future-options content, held in reserve; re-checks the base file's existence before appending — correctly conditional. |
| `implementations/20260718-102052_04_mcp_90_deferred_include_disabled_disabled_code.md` | **Independent workaround**: targets `docs/04_mcp_90_inconsistencies_and_known_issues.md`, which already exists today, so this discoverability fix for requirement 20's content can land *before* requirement 19's base file exists. |
| `implementations/20260718-101407_requires_config_sequencing_check_for_availability_metadata_docs.md` | Re-grep-and-branch procedure so requirement 19's doc edits don't clobber requirement 14's eventual `requires_config` → `config_dependent` rename in the 4 MCP catalog docs. |

None of the above docs have been executed: none exist under `implementations/done/`, and every grep
check they define (`disabled_reason`, `config_dependent`, `include_disabled`, `disabled_code` under
`docs/04_mcp_90...`) still returns its pre-batch (not-landed) result.

## Suggested resolution

1. Land requirement 15/14's server-side changes first (they unblock everything downstream):
   requirement 15's `..._read_server.py.md` / `..._write_server.py.md` / `..._delete_server.py.md` /
   `..._git_server.py.md` / `..._common.py.md` lineage, and requirement 14's `requires_config` →
   `config_dependent` rename.
2. Execute `implementations/20260718-111454_context_py_appservices_runtime_tools.md` to wire
   `RuntimeToolRegistry` into `AppServices`/startup — without this, requirement 17 has no runtime
   effect regardless of what requirement 15 does.
3. Run `implementations/20260718-094534_requirement_17_disabled_reason_landing_check.md`'s landing
   check once step 1 lands, and update `mcp_tool_discovery.py`'s parsing/tests to actually consume
   `enabled`/`disabled_reason`.
4. Execute `implementations/20260718-102052_04_mcp_90_deferred_include_disabled_disabled_code.md`
   independently and soon — it has no dependency on requirement 19 and closes the discoverability gap
   for requirement 20's evaluated-but-deferred proposals right away.
5. Once requirement 19's target file is created (via
   `implementations/20260718-101441_04_mcp_03_06_tool-runtime-availability-metadata.md`, which already
   includes the "Implementation status" callout), execute
   `implementations/20260718-102011_04_mcp_03_06_future_options_appendix.md` to append requirement 20's
   Future-options section.
6. Re-review the `disabled_code` mapping table in `plans/20260717-181151_plan.md` only after
   requirement 15 actually lands — it is currently mapped against `requires_config` semantics, not
   requirement 15's real field shape, and cannot be validated before that.
7. Until step 1-3 land, do not treat requirement 17 as "done" in any user-facing sense — no LLM
   tool-calling behavior is affected by `RuntimeToolRegistry` today; it is inert.

## Severity

Medium overall (driven by requirement 17's inert runtime-registry gap — the most consequential of the
five); the requirement 19/20 documentation-only risks are individually Low. A concrete, sequenced plan
now exists to resolve all of it (the `implementations/` batch above), but none of it has landed yet.
