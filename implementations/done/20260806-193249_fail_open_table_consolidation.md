## Goal

Consolidate redundant Fail-Open/Fail-Closed summary tables in `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` by replacing them with a cross-reference to the canonical table in `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`, while preserving mdq-specific information.

## Scope

- **In-Scope**:
  - Edit `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`:
    - Remove Table 2 ("deny-all を引き起こす設定").
    - Replace Table 1 ("Fail-open 対 Fail-closed のデフォルト") with a cross-reference.
    - Refactor Table 3 ("Fail-Open / Fail-Closed 設定のレビュー"): remove `workflow_allowlist` and `command_allowlist` rows; retain `tool_definitions_strict`, `shell_sandbox_backend`, and `allowed_dirs` (mdq-mcp).
- **Out-of-Scope**:
  - Modifying `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`.
  - Any changes to source code or other documentation files.

## Assumptions

1. The canonical table in `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` contains the authoritative generic fail-open/fail-closed defaults.
2. The mdq-specific caveat about `allowed_dirs` being excluded from startup audits must be preserved.

## Design decisions

- Use targeted table edits rather than rewriting sections — minimizes change surface and avoids cascading rewrites.
- Preserve mdq-specific rows in Table 3 because they are unique to the MDP server context.

## Alternatives considered

- Delete all three tables and link entirely to `05_03`: rejected because it loses mdq-specific information.
- Keep both tables side-by-side: rejected because it creates maintenance burden and inconsistency risk.

## Compatibility considerations

- Readers who previously relied on the duplicate tables will now follow a cross-reference for generic settings and stay on-page for mdq-specific settings.
- No API contract changes — this is purely a documentation consolidation.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If the canonical doc (`05_03`) is later modified or deleted, the cross-reference will break.
- If mdq-specific rows in Table 3 need updating simultaneously, coordinate before making changes.

## Implementation

### Target file

`docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`

### Procedure

**Step a: Remove Table 2**

Delete the entire "deny-all を引き起こす設定" section (lines ~199-205).

### Method

Direct file edit using sed or manual editing.

### Details

```bash
# Locate the section boundaries
sed -n '195,210p' docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md
```

After verification, delete lines ~199-205.

**Step b: Replace Table 1**

Replace the "Fail-open 対 Fail-closed のデフォルト" table (lines ~156-166) with a single line of text.

### Method

Direct file edit.

### Details

```bash
# Locate the section boundaries
sed -n '152,170p' docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md
```

Replace the table with prose such as:
> Fail-open/fail-closed基本方針は [docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md](04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md) を参照。mdq-mcp 固有のロックダウン規則(deny-all時の挙動)は本ファイル末尾に別途記載。

**Step c: Refactor Table 3**

In the "Fail-Open / Fail-Closed 設定のレビュー" table:
- Remove the row for `workflow_allowlist`.
- Remove the row for `command_allowlist`.
- Retain `tool_definitions_strict`, `shell_sandbox_backend`, and `allowed_dirs` (mdq-mcp).

### Method

Direct file edit.

### Details

```bash
# Locate Table 3 boundaries
grep -n "Fail-Open / Fail-Closed\|workflow_allowlist\|command_allowlist\|tool_definitions_strict\|shell_sandbox_backend\|allowed_dirs" docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md
```

After verification:
- Delete the `workflow_allowlist` row.
- Delete the `command_allowlist` row.
- Keep the remaining rows intact.

## Verification

- Verify `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md` no longer contains duplicate rows for `command_allowlist` or `workflow_allowlist` found in `05_03`.
- Confirm `05_05` still correctly lists `tool_definitions_strict` and `shell_sandbox_backend`.
- Confirm `05_05` still preserves the mdq-specific caveat for `allowed_dirs`.
- Ensure all internal links and references remain valid.

```bash
# Verify no duplicate rows remain
grep -n "command_allowlist\|workflow_allowlist" docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md
# Expected: no matches (or only in the cross-reference prose)

# Verify mdq-specific rows exist
grep -n "tool_definitions_strict\|shell_sandbox_backend\|allowed_dirs" docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md
# Expected: at least one match each

# Verify cross-reference exists
grep -n "04_mcp_05_03_fail-open-fail-closed-and-risk-tiers" docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md
# Expected: at least one match
```

## Out of scope

- Source code modifications (`scripts/`).
- Changes to `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`.
- Modifications to other documentation not listed above.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260804-124600_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-193249
- Related target files: docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md
