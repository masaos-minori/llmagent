# Implementation Procedure: Document sensitive_fields in DiagnosticsConfig design doc

## Goal
Add a `sensitive_fields` bullet to the 診断設定 (DiagnosticsConfig) section of `docs/05_agent_08_04_configuration-mcp-approval-obs.md`, describing purpose (additive/union redaction field list) only — no concrete default value.

## Scope
- Target file: `docs/05_agent_08_04_configuration-mcp-approval-obs.md`
- Add one bullet under 診断設定 section

## Assumptions
- The existing style (Japanese bullet list, one line per config key, no concrete default values spelled out for `encryption_key`/`retention_days`) is the pattern to follow.
- The bullet should be inserted after `retention_days` (line 88) to match the existing order in the DiagnosticsConfig dataclass.

## Design decisions
- Follow the existing doc style: Japanese description, one line per field, no concrete default values
- Place the bullet after `retention_days` to match dataclass field order
- Description: `sensitive_fields` は `_filter_sensitive_fields()` が追加でリダクションするフィールド名の集合（ハードコードされたデフォルトとの union）

## Implementation
### Target file
`docs/05_agent_08_04_configuration-mcp-approval-obs.md`

### Procedure
1. Locate the 診断設定 section (lines 85-89)
2. Insert new bullet after `retention_days` bullet (line 88)

### Method
Direct edit using exact line matching

### Details
**Current lines 85-89:**
```markdown
### 診断設定

- `encryption_key`: DiagnosticStore.save(encrypt=True)用のFernet対称鍵（空文字列 = 暗号化無効）
- `retention_days`: session_diagnosticsの行保持日数（0以下 = パージ無効）
```

**After edit:**
```markdown
### 診断設定

- `encryption_key`: DiagnosticStore.save(encrypt=True)用のFernet対称鍵（空文字列 = 暗号化無効）
- `retention_days`: session_diagnosticsの行保持日数（0以下 = パージ無効）
- `sensitive_fields`: `_filter_sensitive_fields()` が追加でリダクションするフィールド名の集合（ハードコードされたデフォルトとの union）
```

## Compatibility considerations
- Doc-only change, no code impact
- No default value documented (matches existing style for this section)

## Security considerations
- None - documentation only

## Rollback considerations
- Git revert of this file if issues arise

## Validation plan
- Run `uv run check-mcp-docs` - should pass with no new findings
- Verify markdown structure is not broken

## Out of scope
- No changes to production code or tests

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/done/20260818-213537_require.md
- Source plan: plans/20260819-162837_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-124742
- Related target files: docs/05_agent_08_04_configuration-mcp-approval-obs.md