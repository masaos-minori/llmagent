# Implementation Procedure: Remove Obsolete Direct-Execution Fallback Documentation (Validation and Troubleshooting Part 1)

## Goal

Remove the parenthetical reference to `workflow_mode` in the validation and troubleshooting documentation and simplify to just state no config setting can disable the check.

## Scope

- `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md` only
- Removing one parenthetical reference; no new content creation

## Assumptions

1. The requirement `requires/20260714_01_require.md` is the canonical specification for this task.
2. Workflow support is mandatory; no degraded workflow mode exists.
3. No source code changes are required — documentation updates only.

## Implementation

### Target file

`docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part1.md`

### Procedure

1. **Locate line 29**: Find the sentence containing the parenthetical reference to `workflow_mode`.
2. **Remove the parenthetical**: Delete the parenthetical text "(2026-07-09に確認済み: `workflow_mode` は有効な設定キーではない — 詳細は [Configuration: AgentConfig Structure](...) を参照)".
3. **Simplify the sentence**: Rewrite to just state no config setting can disable the check.

### Method

- Parenthetical text removal via file edit.
- Sentence rewrite for clarity.
- Preserve surrounding context and formatting.

### Details

- Line 29: The current sentence reads something like "ワークフロー定義ファイルが存在することを無条件に検証する — これを無効化・縮退させる設定は存在しない (2026-07-09に確認済み: `workflow_mode` は有効な設定キーではない — 詳細は [Configuration: AgentConfig Structure](...) を参照)". Simplify to: "ワークフロー定義ファイルが存在することを無条件に検証する — これを無効化・縮退させる設定は存在しない".
- The parenthetical adds unnecessary detail about a specific date and a link to another document. Since the core fact (no config setting can disable it) is sufficient, remove the elaboration.

## Validation plan

1. Verify the simplified sentence still clearly states the unconditional nature of the check.
2. Confirm the removed link does not break any cross-references.
3. Run `pre-commit run --all-files` if markdown linting is configured.
