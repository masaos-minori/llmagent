## Goal

Register `tools/check_issue_inventory_conformance.py` in `tools/TOOL_DESCRIPTIONS.md`'s two tables (summary + detailed), following the bilingual (Japanese) description convention used for `check_needs_confirmation_inventory.py` and `check_known_deviation_sync.py`; run `uv run python tools/check_tool_descriptions_sync.py` to confirm.

## Scope

- Add a new row to the summary table in `tools/TOOL_DESCRIPTIONS.md`.
- Add a new row to the detailed table in `tools/TOOL_DESCRIPTIONS.md`.
- Follow the format model established by `check_needs_confirmation_inventory.py` (lines 28, 59) and `check_known_deviation_sync.py` (line 62).
- Use Japanese descriptions consistent with the existing bilingual convention.

## Assumptions

- The summary table uses a format like:
  ```markdown
  | ツール名 | 説明 |
  |---|---|
  | check_needs_confirmation_inventory.py | NCエントリの必須フィールドとステータス値を検証するスクリプト |
  | check_known_deviation_sync.py | ADR既知の乖離と実装の同期状態を検証するスクリプト |
  ```
- The detailed table uses a format like:
  ```markdown
  ### check_needs_confirmation_inventory.py
  - **目的**: NCエントリ...
  - **入力**: ...
  - **出力**: ...
  ```
- The exact column headers and field names may vary slightly depending on the current file layout — verify against the live document at implementation time.

## Design decisions

- Follow the exact format of existing entries — same column order, same indentation level, same field naming.
- Use Japanese descriptions for the tool's purpose and behavior, consistent with the existing bilingual convention.
- Do not modify any existing rows.

## Alternatives considered

- Using English-only descriptions — rejected because the Plan's intent is to follow the existing bilingual convention.

## Implementation
### Target file

`tools/TOOL_DESCRIPTIONS.md`

### Procedure

1. Locate the summary table in `tools/TOOL_DESCRIPTIONS.md` (approximately lines 28 based on Reference Files evidence).
2. Add a new row after the existing entries, following the same column structure.
3. Locate the detailed descriptions section (approximately line 59 based on Reference Files evidence).
4. Add a new subsection for `check_issue_inventory_conformance.py`, following the same format as existing detailed entries.

### Method

Current state: The summary table has existing entries for `check_needs_confirmation_inventory.py` and `check_known_deviation_sync.py`.

Required additions to summary table:
```markdown
| check_issue_inventory_conformance.py | Issue inventoryの語彙、テンプレート、参照整合性を検証するスクリプト |
```

Required additions to detailed section:
```markdown
### check_issue_inventory_conformance.py
- **目的**: Issue inventoryの語彙（Status/Type/Severity/Area/Owner）、テンプレート（フィールド数）、および参照整合性（Related/Related NC/Target）を検証する
- **入力**: docs/00_governance_03_issue-and-uncertainty-management.md
- **出力**: 違反報告（Blocking/Warning severity）
- **依存関係**: tools/_docs_consistency_lib.py
- **CIトリガー**: .github/workflows/governance-docs-consistency.yml
```

The exact column headers and field names may vary slightly depending on the current file layout — verify against the live document at implementation time.

### Details

The new entry should use the same indentation level and formatting as existing entries. The Japanese descriptions should be concise and accurate — one sentence for the purpose, one line each for input/output/dependencies/triggers.

## Compatibility considerations

- This is a documentation-only change — no code compatibility impact.
- The new entry cross-references the new conformance checker — proper ownership routing via the Governance Verification Matrix.

## Security considerations

- No security impact — documentation-only change.

## Rollback considerations

- If the TOOL_DESCRIPTIONS entry is found to duplicate an existing convention, simply remove it. No behavioral rollback needed since there is none.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/TOOL_DESCRIPTIONS.md` | Sync check | `uv run python tools/check_tool_descriptions_sync.py` | Passes |

## Completion criteria

- The summary table includes a row for `check_issue_inventory_conformance.py`.
- The detailed section includes a subsection for `check_issue_inventory_conformance.py`.
- Both entries follow the same format as existing entries.
- `uv run python tools/check_tool_descriptions_sync.py` passes clean.

## Out of scope

- Modifying any other documentation files.
- Adding additional fields beyond those present in existing entries.
- Changing the format of existing entries.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20260915-200449_gov03_add-conformance-and-referential-integrity-checks-for-the-issue-inventory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-151710_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-151710
- **Related target files**: tools/TOOL_DESCRIPTIONS.md
