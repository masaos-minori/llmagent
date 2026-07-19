## Goal

Implementation step 3 of `plans/20260717-180307_plan.md` (requirement 19): create a new
Markdown file, `docs/04_mcp_03_06_tool-runtime-availability-metadata.md`, as the canonical
specification for the `config_dependent` / `enabled` / `disabled_reason` tool-availability
metadata contract, the `/v1/tools` always-returns-all-tools and disabled-not-omitted rules, the
`/v1/call_tool` disabled-rejected-before-dispatch rule, and RuntimeToolRegistry's expected
handling of disabled tools (LLM-visibility filtering, no dispatch through the registry's routing
path). This is documentation only; the contract described is **target design, not yet
implemented** in `scripts/` (confirmed: zero occurrences of `config_dependent`,
`disabled_reason`, or `RuntimeToolRegistry` under `scripts/` as of this writing) — the new file
must say so explicitly.

## Scope

**In scope**: create the single new file `docs/04_mcp_03_06_tool-runtime-availability-metadata.md`
with frontmatter matching the existing `04_mcp_*` convention and the 7 content sections listed
in the plan's Design section.

**Out of scope**: registering the new file in `docs/04_mcp_00_document-guide.md` (Implementation
step 4, separate procedure doc); editing the 4 catalog docs (step 5, separate doc); editing
`docs/05_agent_08_04_configuration-mcp-approval-obs.md` (step 6, separate doc); editing
`docs/04_mcp_90_inconsistencies_and_known_issues.md` (step 7, separate doc); any change to
`scripts/`, `tests/`, or `config/` — none of the described behavior is implemented by this step.

## Assumptions

- Repo convention for `04_mcp_*` files (verified by reading `docs/04_mcp_03_02_tool-registry.md`
  L1-16) requires YAML frontmatter with `title`, `category: mcp`, `tags` (list), and `related`
  (list of sibling doc filenames). The new file must follow this exact shape.
- `ToolRegistry` (documented in `04_mcp_03_02_tool-registry.md`, confirmed by its L20 sentence:
  "ToolRegistry の責任はツールからサーバーへの所有関係とルーティングのみであり、スキーマレジ
  ストリではない。`ToolDefinition.description` / `input_schema` は予約済みで未使用である。")
  is explicitly static, ownership/routing-only, and distinct from the runtime,
  per-request `enabled`/`disabled_reason` concept. The new `04_mcp_03_06` file must be written as
  a **sibling** to `04_mcp_03_02`, not a merge into it — this matches the plan's Affected-areas
  note and the existing split pattern (`03_01` dispatch/routing, `03_02` tool-registry, `03_03`
  transport-and-health part1/part2, `03_04` tool-call-tracing, `03_05` lifecycle).
- Field semantics (per plan Assumption 4, itself sourced from sibling requirement plans
  14-17): `config_dependent` is a static per-tool boolean in each server's `TOOL_LIST`
  (replaces `requires_config`, same boolean values, no compatibility shim — requirement 14's
  plan). `enabled`/`disabled_reason` are computed per-request from each server's current `_cfg`
  state and added to each tool dict in the live `/v1/tools` response (requirement 15/16's
  plans). Standard `disabled_reason` values: `"allowed_dirs is empty"` (file
  read/write/delete), `"allowed_repo_paths is empty"` (git, takes precedence over
  `read_only`), `"read_only=true"` (git write tools only, when the allowlist is non-empty), plus
  reserved/forward-looking `"command_allowlist is empty"` / `"workflow_allowlist is empty"`
  (shell/cicd — requirement 15's plan explicitly scopes shell/cicd implementation OUT, so these
  two values must be marked reserved/not-yet-active, not documented as already live).
  `RuntimeToolRegistry` tracks four states (discovered / MCP-server-enabled /
  agent-policy-enabled / LLM-visible) per requirement 17's plan, with `enabled_for_llm` as a
  derived field; disabled tools are tracked for diagnostics but never surfaced to the LLM and
  never dispatchable through the registry's own routing path.
- **Superseded by post-review decision (2026-07-18)**: the CLAUDE.md task-level warning below
  originally directed this doc to follow the 6-field lineage; a cross-batch review has since
  resolved the incompatibility and adopted the 13-field/9-method lineage as the single baseline
  (see the correction note in `implementations/20260718-084710_runtime_tool.py.md`). The two
  lineages referenced here are: 13-field/9-method routing version at
  `implementations/20260717-203121_runtime_tool.py.md` /
  `implementations/20260717-203200_runtime_tool_registry.py.md` (**adopted baseline**), vs. the
  6-field disabled-visibility version at `implementations/20260718-094020_runtime_tool.py.md` /
  `implementations/20260718-094055_runtime_tool_registry.py.md` (neither base doc was actually
  written; superseded). This plan's requirement 19 is explicitly about disabled-tool-visibility
  documentation (per its own title: "Document MCP runtime availability metadata and disabled tool
  behavior"), so the RuntimeToolRegistry section of the new doc must now describe the
  disabled-visibility fields/methods (`config_dependent`/`enabled`/`disabled_reason`/
  `enabled_for_llm`/`diagnostics()`/`get_llm_visible_definitions()`) as an **extension of the
  13-field/9-method lineage**, not as a separate 6-field class. No third incompatible variant was
  found; this plan does not need to reconcile a third lineage, only describe the one adopted
  baseline correctly.

## Implementation

### Target file

`docs/04_mcp_03_06_tool-runtime-availability-metadata.md` (new file)

### Procedure

1. Write YAML frontmatter modeled on `04_mcp_03_02_tool-registry.md`'s frontmatter block
   (title/category/tags/related), with `related` listing:
   `04_mcp_00_document-guide.md`, `04_mcp_03_02_tool-registry.md`, `04_mcp_04_01_web-search-file-read-github.md`,
   `04_mcp_04_02_file-write-file-delete-shell.md`, `04_mcp_04_03_rag-pipeline-and-cicd.md`,
   `04_mcp_04_05_git.md`, `05_agent_08_04_configuration-mcp-approval-obs.md`,
   `04_mcp_90_inconsistencies_and_known_issues.md`.
2. Write an "Implementation status" callout box at the very top of the body (per Design item 7),
   stating explicitly this contract is target design, not yet live, with a pointer to the 4
   implementing plans.
3. Write the 6 remaining content sections in the order given in the plan's Design section.
4. Confirm (grep) the new file contains `config_dependent`, `disabled_reason`, and
   `enabled_for_llm` at least once each, and does not describe `requires_config` as currently
   active anywhere outside the explicit "removed/obsolete" callout.

### Method

Direct Markdown authoring (no code). Structure and content given below is the full intended
prose/data outline — write it as literal Markdown/JSON, since this document IS the doc-file
content, not source code.

### Details

Frontmatter shape (model directly on `04_mcp_03_02_tool-registry.md` L1-16):

```
---
title: "Tool Runtime Availability Metadata: config_dependent, enabled, disabled_reason"
category: mcp
tags:
  - mcp
  - routing
  - tool-registry
  - runtime-tool-registry
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_03_02_tool-registry.md
  - 04_mcp_04_01_web-search-file-read-github.md
  - 04_mcp_04_02_file-write-file-delete-shell.md
  - 04_mcp_04_03_rag-pipeline-and-cicd.md
  - 04_mcp_04_05_git.md
  - 05_agent_08_04_configuration-mcp-approval-obs.md
  - 04_mcp_90_inconsistencies_and_known_issues.md
---
```

Body — 7 sections, in order:

0. **Implementation status callout** (top of body, before section 1): a blockquote or bold-lead
   paragraph stating e.g. "As of 2026-07-17 this contract is documented as target design;
   production code still uses `requires_config` and has no `enabled`/`disabled_reason`/
   `RuntimeToolRegistry` — see `plans/20260717-173602_plan.md` through
   `plans/20260717-175630_plan.md` (requirements 14-18) for the implementing work." This must be
   visually distinct (e.g. `> **Implementation status:** ...`) so a skimming reader cannot miss
   it.

1. **`config_dependent` (static)** — a per-tool boolean field in each server's `TOOL_LIST`,
   direct rename of `requires_config` with identical boolean semantics, no compatibility shim.
   State explicitly: `requires_config` is removed; any remaining doc/code reference to it
   describes obsolete behavior.

2. **`enabled` / `disabled_reason` (runtime, request-time-computed)** — added to each tool dict
   in the live `/v1/tools` response body, computed per-request from the owning server's current
   config state (`_cfg`). Invariant: `enabled=True` <-> `disabled_reason == ""`; `enabled=False`
   <-> `disabled_reason` is a non-empty standard string (enumerated in section 3).

3. **Standard `disabled_reason` values** — a table:

   | `disabled_reason` value | Applies to | Status |
   |---|---|---|
   | `"allowed_dirs is empty"` | file read/write/delete servers | active |
   | `"allowed_repo_paths is empty"` | git (takes precedence over `read_only`) | active |
   | `"read_only=true"` | git write tools only, when allowlist is non-empty | active |
   | `"command_allowlist is empty"` | shell | reserved — not yet implemented (requirement 15 scopes shell/cicd out) |
   | `"workflow_allowlist is empty"` | cicd | reserved — not yet implemented (requirement 15 scopes shell/cicd out) |

4. **`/v1/tools` behavioral rules** — always returns every implemented tool; disabled tools are
   never omitted from the response. Example JSON response block, one enabled + one disabled tool
   side by side:

   ```json
   {
     "tools": [
       {
         "name": "git_status",
         "config_dependent": true,
         "enabled": true,
         "disabled_reason": ""
       },
       {
         "name": "git_push",
         "config_dependent": true,
         "enabled": false,
         "disabled_reason": "read_only=true"
       }
     ]
   }
   ```

5. **Dispatch rule** — disabled tools must be rejected by `/v1/call_tool` before reaching the
   dispatch table (server-side gate). Reference requirement 16's plan
   (`plans/20260717-174848_plan.md`) for the exact response shape:
   `CallToolResponse(result="Tool disabled: <reason>", is_error=True)`.

6. **RuntimeToolRegistry (agent-side)** — disabled tools are tracked for diagnostics
   (`enabled_for_llm` derived field) but never included in the LLM-facing tool list and never
   dispatchable through the registry's own routing path. Four states: discovered /
   MCP-server-enabled / agent-policy-enabled / LLM-visible. Reference requirement 17's plan
   (`plans/20260717-175327_plan.md`) — per the post-review decision above, this section must
   describe the disabled-visibility fields/methods as an extension of the **adopted 13-field/
   9-method `RuntimeTool`/`RuntimeToolRegistry` lineage**
   (`implementations/20260717-203121_runtime_tool.py.md`,
   `implementations/20260717-203200_runtime_tool_registry.py.md`,
   `implementations/20260718-084710_runtime_tool.py.md`), not as a separate 6-field class
   (`implementations/20260718-094020_runtime_tool.py.md`,
   `implementations/20260718-094055_runtime_tool_registry.py.md` — neither was actually written).

## Validation plan

- `grep -c "config_dependent\|disabled_reason\|enabled_for_llm"
  docs/04_mcp_03_06_tool-runtime-availability-metadata.md` → expect > 0.
- `grep -n "requires_config" docs/04_mcp_03_06_tool-runtime-availability-metadata.md` → expect
  0 matches, OR matches only inside the explicit "removed/obsolete" sentence in section 1 (never
  presented as currently active).
- Manual check: the "Implementation status" callout is present and near the top of the file
  (not buried at the bottom).
- Manual check: frontmatter `related:` list resolves to files that all actually exist (all 8
  listed files already exist in `docs/` as of this writing, or are created earlier in the same
  plan's step sequence — `04_mcp_00`, `04_mcp_03_02`, the 4 catalog docs, `05_agent_08_04`,
  `04_mcp_90` all pre-exist; only `04_mcp_03_06` itself is new).
- Downstream (Implementation step 4's own doc): confirm the new file is registered in
  `docs/04_mcp_00_document-guide.md`'s File Index or `tests`/`check-mcp-docs` consistency
  conventions are not violated (that file's own doc-consistency test does not check the File
  Index — see the format-precheck procedure doc — so this is a manual convention check, not an
  automated one).
