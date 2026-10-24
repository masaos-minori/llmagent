# tool005: the default `masked_fields` names match no real tool argument, so masking is inert for the file tools

## Priority
Medium

## Summary
Replace the default `masked_fields = ["file_content"]` with the argument key names the file write
tools actually use, so the redaction feature redacts something on a default installation. File the
change as its own issue rather than folding it into `plans/20261023-072425_plan.md`, whose frozen
target table does not include any config or defaults file.

## Background
`plans/20261023-072425_plan.md` `UNK-01` asked whether production config relies on
`masked_fields = ["file_content"]`. Measuring that name against the actual tool schemas showed it
matches nothing: `file_content` appears only inside GitHub MCP `get_file_contents` implementation
symbols (`scripts/mcp_servers/github/github_service_file.py:47`,
`scripts/mcp_servers/github/github_service_dispatch.py:111`), never as an argument key. The tool
*names* are `github_get_file_contents` (`scripts/mcp_servers/github/tools_file.py:52`,
`scripts/shared/tool_constants.py:146`), which masking cannot match because masking compares
argument keys. The Plan recorded this as a correction, and the owner decided (2026-10-24) to keep the
Plan's six frozen rows unchanged and route the default-value change to this issue.

## Problem
The three places that define the default are
- `scripts/agent/config_dataclasses.py:182` — `masked_fields: list[str] = field(default_factory=lambda: ["file_content"])`,
- `scripts/agent/config_section_builders.py:204-205` — `masked_fields=_get_or_default(cfg, "masked_fields", _get_list, ["file_content"])`,
- `config/agent.toml:98` — `masked_fields = ["file_content"]` (the deployed copy `/opt/llm/config/agent.toml:98` is identical).

The real argument names are `content` for `write_file` (`scripts/mcp_servers/file/write_tools.py:22`)
and `old_text` / `new_text` inside the `edits` list items for `edit_file` (`write_tools.py:55`, `:61`).
So with the shipped default, `mask_args()` masks no key for any tool this project registers, and the
only test that exercises masking (`tests/agent/test_tool_approval_preflight.py:417`) passes its own
`masked_fields=["secret"]` instead of the default.

## Reason for Change
`plans/20261023-072425_plan.md` is turning masking into a documented logging/audit boundary and is
extending it to nested containers. Leaving the default list pointing at a name no tool uses means
the boundary being documented protects nothing by default, and the nesting fix has no observable
effect in a default deployment.

## Implementation Intent
Change the default value in the two dataclass/builder defaults and in both TOML files, keep the
setting's shape unchanged (a list of key names, matched by name at any depth once nested masking
lands), and update the one assertion that pins the default. No change to which sinks are masked:
that boundary is already decided by `plans/20261023-072425_plan.md` (`REQ-001`, its Design section).

## Target Files or Areas
- `scripts/agent/config_dataclasses.py` (`ToolConfig`, `:182`)
- `scripts/agent/config_section_builders.py` (`ToolConfigBuilder.build`, `:204-205`)
- `config/agent.toml` (`:98`)
- `/opt/llm/config/agent.toml` (`:98`, deployed copy — shared infrastructure)
- `tests/agent/test_config_builders.py` (`:155`, `assert cfg.tool.masked_fields == ["file_content"]`)
- `docs/23_agent/agent_08_03_configuration-tools-memory.md` (`:32`, the `masked_fields` bullet — the
  only prose mention of the setting in `docs/`; `grep -rn "masked_fields" docs/` finds no other)

## Required Changes
- Change the default list in `config_dataclasses.py:182` and `config_section_builders.py:204-205` to
  the real argument names decided in `Unresolved Questions` (candidate: `["content", "old_text", "new_text"]`).
- Change `config/agent.toml:98` to the same list.
- Apply the same change to `/opt/llm/config/agent.toml:98` only after explicit confirmation for the
  shared production config.
- Update `tests/agent/test_config_builders.py:155` to the new expected default.
- Update the `masked_fields` bullet in `docs/23_agent/agent_08_03_configuration-tools-memory.md:32`
  so it states the default key names and that they name file-write tool arguments.

## Constraints
- Ordering: `old_text`/`new_text` live inside the `edits` list items, not at the top level. With the
  current top-level-only `mask_args` (`scripts/agent/tool_result_formatter.py:42-47`) the new names
  still match nothing for `edit_file`. This issue must land after, or in the same release as, the
  nested-masking work in `implementations/20261024-124138_01_scripts_agent_tool_result_formatter.py.md`
  and `_02`.
- `config/agent.toml:98` sits in the flat top-level region under the `# ── Security ──` comment
  (`:96`); there is no `[security]` table header before it (the first table is `[diagnostics]` at `:230`),
  so the key must stay in the same region or `[tool]`-section loading must be re-verified.
- Deployments that already set `masked_fields` explicitly keep their own value; only the default
  changes.
- `docs/23_agent/agent_08_03_configuration-tools-memory.md` is a `churn30d=17` hot file (`docs/00_index.md:325`).

## Acceptance Criteria
1. `grep -n "file_content" scripts/agent/config_dataclasses.py scripts/agent/config_section_builders.py config/agent.toml`
   reports no `masked_fields` default using `file_content`.
2. `uv run pytest tests/agent/test_config_builders.py -q` passes with the new default asserted.
3. A `write_file` call with `content` set, and an `edit_file` call with `edits` items carrying
   `old_text`/`new_text`, produce `***` in the audit events written by `scripts/agent/tool_audit.py`
   and in the REPL tool-call line written by `scripts/agent/tool_runner.py`, with no explicit
   `masked_fields` configuration.
4. `uv run python tools/check_config_keys.py` and `uv run python tools/check_config_defaults.py`
   report no issue after the change.
5. The full `rules/toolchain.md` validation sequence passes with no new failure.

## Testing Expectations
- Update `tests/agent/test_config_builders.py:155` and any sibling default-pinning assertion in that file.
- Add a regression test that masks default-configured args end to end: build config with
  `load_config()`'s defaults, pass `write_file`-shaped and `edit_file`-shaped args through
  `mask_args(args, cfg.tool.masked_fields)`, and assert `***` at the real key names.
- Extend `tests/agent/test_tool_approval_preflight.py:417` (`test_masked_fields_applied_to_args`) or
  add a sibling case that uses the real default names instead of `["secret"]`.
- Re-run `uv run python tools/check_docs_consistency.py --domain agent` after the doc bullet update.

## Documentation Impact
Required, one bullet: `docs/23_agent/agent_08_03_configuration-tools-memory.md:32` must state the
default key names and that they are file-write tool argument names. If a key-name list is added
anywhere else (for example a new table), index it in `docs/00_index.md` per its Document References
by Task mapping for "AgentConfig / config constants"
(`docs/23_agent/agent_08_01_configuration-loading-agent-config.md`), which currently does not name
`masked_fields`.

## Out of Scope
- Changing which outputs are masked (approval previews stay unmasked; decided by
  `plans/20261023-072425_plan.md` `REQ-001`).
- Changing `plan_blocked_tools` or any other `ToolConfig` field.
- Masking tool *results* rather than tool *arguments*.
- Adding pattern, glob, or path-based matching to `masked_fields`.
- Lazy loading of the Step 0 mandatory-load set — no action required: the fixed load is absorbed by the prompt cache (user decision 2026-10-24).

## Dependencies
- Depends on the nested-masking rows of `plans/20261023-072425_plan.md`
  (`implementations/20261024-113446_01_scripts_agent_tool_result_formatter.py.md`,
  `_02_tests_agent_test_tool_result_formatter.py.md`) — see Constraints.
- Related: [issues/20261024-124138_tool005-args-preview-is-written-to-the-audit-log-unbounded.md](20261024-124138_tool005-args-preview-is-written-to-the-audit-log-unbounded.md)
  — masking more keys also changes how much of the audit payload is redacted.

## Unresolved Questions
- Should `file_content` remain in the default list for backward compatibility, or be replaced
  outright? Replacing it is the cleaner reading of "the default should match real arguments", but it
  changes behavior for any deployment relying on the shipped value.
- Should `content` be masked at all, given `write_file` previews are deliberately unmasked
  (`plans/20261023-072425_plan.md` Design)? Masking applies to logs and audit rows only, so the
  preview decision does not block this, but the two features read as contradictory unless the
  documentation states the split.

## AI Implementation Instruction
Change only the default value and its pinned test plus the one documentation bullet. Do not change
`mask_args`, its callers, or which sinks are masked. Do not edit `/opt/llm/config/agent.toml`
without explicit confirmation. Verify the claim about real argument names against
`scripts/mcp_servers/file/write_tools.py` before choosing the list, and re-run the config checkers
in `rules/toolchain.md` because both a dataclass default and a TOML value change together.

## Traceability
- **Workflow phase**: `plan-to-implementation-procedure` (Plan Gap found while verifying the Plan against the current tree)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-072425_plan.md` (`UNK-01`)
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261024-124138
- **Related target files**: `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py`, `config/agent.toml`, `/opt/llm/config/agent.toml`, `tests/agent/test_config_builders.py`, `docs/23_agent/agent_08_03_configuration-tools-memory.md`
