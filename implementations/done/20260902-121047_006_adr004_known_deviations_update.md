# Implementation Procedure Output Template (Canonical)

## Goal

Update ADR-004's Known Deviations entry `ADR-004-D1-profile-config-model-still-present` to reflect the resolved environment-independence gap. Only Known Deviations section is modified — Decision, Rationale, and Invariants sections MUST NOT be changed.

## Scope

One Known Deviations entry update in `docs/adr/ADR-004-environment-failure-handling-policy.md`. No changes to Decision, Rationale, or Invariants sections.

## Assumptions

- Field collapse (`required_in_production`/`required_in_local` → `required: bool = True`) is already implemented in `scripts/shared/mcp_config.py` (confirmed: line 94).
- Classification branch removal (`cfg.required` direct read) is already implemented in `scripts/agent/services/mcp_tool_discovery.py` (confirmed: line 130).
- The existing Known Deviations entry text ("解決済み") reflects the intent but needs refinement based on adversarial verification findings.

## Design decisions

- Update the Known Deviations entry to accurately describe what was resolved vs. what remains pending.
- Do NOT modify Decision, Rationale, or Invariants sections per requirement scope.
- Keep the entry in Japanese to match the existing ADR language.

## Alternatives considered

**Alternative A: Remove the Known Deviations entry entirely** — Since the gap is resolved, remove it.
- Advantage: cleaner ADR; no stale reference.
- Disadvantage: loses historical context; future reviewers won't understand why the entry existed.

**Alternative B: Mark as "Resolved" with detailed status** — Keep the entry but add resolution details.
- Advantage: preserves history while clarifying current state.
- Disadvantage: slightly longer entry.

Chose Alternative B because it provides traceability for future reviewers who encounter this entry during ADR review.

## Implementation

### Target file

`docs/adr/ADR-004-environment-failure-handling-policy.md`

### Procedure

1. Locate the Known Deviations section (line 450-455).
2. Find the `ADR-004-D1-profile-config-model-still-present` entry.
3. Update the entry to reflect:
   - What was resolved: field collapse + classification branch removal
   - What remains pending: test coverage (cross-profile equivalence), issue lifecycle (adr004_01 archive)
4. Leave all other Known Deviations entries unchanged.

### Method

Replace the existing Known Deviations entry text:

```markdown
- **Known Issue**: ADR-004-D1-profile-config-model-still-present — `scripts/shared/mcp_config.py`の`McpServerConfig`と`scripts/agent/services/mcp_tool_discovery.py`は、`security_profile`（環境）の値に基づいて`required_in_production`／`required_in_local`のいずれを参照するか分岐していた。**解決済み**: REQ-001 through REQ-004により、`required_in_production`/`required_in_local`を統合した単一の`required`フィールドに置換し、`FailurePolicy`をFAIL_FASTのみに簡素化。これにより環境に基づく分岐ロジックは削除され、必須性の決定が環境非依存となった。**影響**: INV-01, INV-02, INV-09, INV-14 → 解消済み。
```

With:

```markdown
- **Known Issue**: ADR-004-D1-profile-config-model-still-present — `scripts/shared/mcp_config.py`の`McpServerConfig`と`scripts/agent/services/mcp_tool_discovery.py`は、`security_profile`（環境）の値に基づいて`required_in_production`／`required_in_local`のいずれを参照するか分岐していた。**部分解決**: REQ-001およびREQ-002により、`required_in_production`/`required_in_local`を統合した単一の`required`フィールドに置換し、`McpToolDiscoveryService.discover_all()`の分類分岐を`cfg.required`直接読み取りに置き換え。環境に基づく分岐ロジックは削除され、必須性の決定が環境非依存となった。**残課題**: REQ-002のクロスプロファイル等価テスト（`tests/agent/services/test_mcp_tool_discovery.py`）、REQ-001のデフォルト値テスト（`tests/shared/test_mcp_config.py`）、REQ-004のissueアーカイブ（`issues/done/`）。**影響**: INV-01, INV-02, INV-09 → 解消済み。INV-14 → テストカバレッジ未完了のため保留中。
```

### Details

- Changed "解決済み" to "部分解決" to accurately reflect that the core implementation is done but test coverage and issue lifecycle remain incomplete.
- Added explicit listing of remaining tasks (REQ-002 cross-profile test, REQ-001 default-value test, REQ-004 issue archive).
- Updated INV-14 status from "解消済み" to "保留中" because the test coverage for INV-14 (unconfigured component criticality startup continuation prohibition) is not yet complete.
- Kept INV-01, INV-02, INV-09 as "解消済み" since their verification does not depend on the remaining tests.

## Compatibility considerations

- This is a documentation-only change in the Known Deviations section.
- Does NOT touch Decision, Rationale, or Invariants sections.
- Preserves the original entry's structure and language (Japanese).
- The entry remains visible for future ADR reviewers.

## Security considerations

None — this is a pure documentation update. No security-sensitive behavior is affected.

## Rollback considerations

If the update introduces inaccuracies, the rollback is simply reverting the Known Deviations entry to its previous text. However, the previous text was misleading (claiming full resolution when some items were still pending), so reverting would reintroduce the same problem.

## Validation plan

1. Read the updated ADR-004 file and verify:
   - Only Known Deviations section was modified
   - Decision, Rationale, and Invariants sections are unchanged
   - The entry accurately describes what was resolved vs. what remains pending
2. Confirm no stale references to `required_in_production`/`required_in_local` remain in production code: `rg 'required_in_local|required_in_production' scripts/` returns zero matches.

## Completion criteria

- Known Deviations entry updated to accurately reflect current state.
- Decision, Rationale, and Invariants sections unchanged.
- No stale references to `required_in_production`/`required_in_local` in production code.

## Out of scope

- Modifying production code in `mcp_config.py` or `mcp_tool_discovery.py` (already done).
- Adding tests (`tests/shared/test_mcp_config.py`, `tests/agent/services/test_mcp_tool_discovery.py`).
- Archiving `adr004_01` issue.
- Updating other ADRs or documentation files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update Known Deviations entry | Done | 2026-09-02 | 2026-09-02 | Changed "解決済み" to "部分解決", added remaining tasks list, updated INV-14 status |
| 2 | Validate update | Done | 2026-09-02 | 2026-09-02 | No stale references to required_in_production/required_in_local remain in production code |

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
- **Requirement ID**: REQ-005
- **Source issue**: `issues/20260831-192510_adr004_05_mcp_config_alignment_superseded_by_policy_reversal.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-102432_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-121047
- **Related target files**: `docs/adr/ADR-004-environment-failure-handling-policy.md`
