## Goal

Trim ADR-004's `ADR-004-D1-profile-config-model-still-present` Known Deviations entry's
"残課題" (remaining items) list to name only the still-real cross-profile
`security_profile` parametrization gap, removing the two items that have since been
confirmed complete (the default-value test and the issue archive).

## Scope

Modify exactly the "残課題" clause of the `ADR-004-D1-profile-config-model-still-present`
bullet in `docs/adr/ADR-004-environment-failure-handling-policy.md`'s Known Deviations
section (current line 451). No other Known Deviations entry, and no Decision/Rationale/
Invariants section, is touched.

## Assumptions

- **Partially-implemented discrepancy found during adversarial verification**: a prior
  implementation cycle (`implementations/done/20260902-121047_006_adr004_known_deviations_update.md`,
  same `Source plan`/`Related target files` as this document) already rewrote this same
  entry to its current "部分解決" / three-item "残課題" form. That prior document's own
  scope was to change the entry from claiming full resolution ("解決済み") to partial
  resolution — it predates, and does not cover, the current Plan's further finding (row
  6 of `plans/20260901-102432_plan.md`) that two of those three "残課題" items are now
  themselves complete. This document implements only that further trim, per
  `plan-to-implementation-procedure` Step 3's "Partially implemented" handling.
- Confirmed by direct read of `docs/adr/ADR-004-environment-failure-handling-policy.md`
  line 451: the current "残課題" clause reads (in full): "REQ-002のクロスプロファイル
  等価テスト（`tests/agent/services/test_mcp_tool_discovery.py`）、REQ-001のデフォルト
  値テスト（`tests/shared/test_mcp_config.py`）、REQ-004のissueアーカイブ
  （`issues/done/`）。" — matching the Plan's evidence exactly, no drift.
- The default-value test (`test_required_default_true_on_direct_construction`,
  `test_required_default_true_from_toml_absent_key`) is confirmed present in
  `tests/shared/test_mcp_config.py` (Plan row 4, struck through as already implemented).
  The issue archive (`issues/done/20260831-173019_adr004_01_mcp_config_failure_model_alignment.md`)
  is confirmed present (Plan row 5, struck through as already implemented). Both are
  genuinely resolved, so both may be removed from "残課題".
- The cross-profile `security_profile` parametrization (this same Plan's row 3,
  implemented by the sibling document `implementations/20260902-183208_03_tests_agent_services_test_mcp_tool_discovery.py.md`)
  is the one item that remains genuinely open until that sibling document's change
  lands — so it stays in "残課題".

## Design decisions

Remove the two now-completed clauses from the "残課題" sentence, keeping the sentence
structure and Japanese phrasing style otherwise identical, per the Plan's own
instruction to change only Known Deviations, not Decision/Rationale/Invariants.

## Alternatives considered

Removing the "残課題" clause entirely (implying the deviation is now fully resolved) —
rejected: the cross-profile parametrization item is still genuinely open until the
sibling document lands; removing the whole clause would misrepresent the deviation as
closed prematurely. The Plan's own Design section is explicit that only the two
now-stale items are to be removed, not the clause itself.

## Implementation

### Target file

`docs/adr/ADR-004-environment-failure-handling-policy.md`

### Procedure

Edit the `ADR-004-D1-profile-config-model-still-present` Known Deviations bullet's
"残課題" clause to name only the cross-profile parametrization item.

### Method

Current text (line 451, "残課題" clause only, in context):
```
...環境に基づく分岐ロジックは削除され、必須性の決定が環境非依存となった。**残課題**:
REQ-002のクロスプロファイル等価テスト（`tests/agent/services/test_mcp_tool_discovery.py`）、
REQ-001のデフォルト値テスト（`tests/shared/test_mcp_config.py`）、REQ-004のissueアーカイブ
（`issues/done/`）。**影響**: INV-01, INV-02, INV-09 → 解消済み。INV-14 →
テストカバレッジ未完了のため保留中。
```

Replace with:
```
...環境に基づく分岐ロジックは削除され、必須性の決定が環境非依存となった。**残課題**:
REQ-002のクロスプロファイル等価テスト（`tests/agent/services/test_mcp_tool_discovery.py`、
`security_profile`を第2パラメータ軸として追加）のみ。REQ-001のデフォルト値テスト
（`tests/shared/test_mcp_config.py`）およびREQ-004のissueアーカイブ（`issues/done/`）は
解決済み。**影響**: INV-01, INV-02, INV-09 → 解消済み。INV-14 →
テストカバレッジ未完了のため保留中。
```

### Details

The "影響" (Impact) clause and INV-14 status are left unchanged — this Plan's row does
not address INV-14's separate, still-open gap (unconfigured-component-criticality
startup-continuation test coverage), which is a distinct concern the Plan's own
Out-of-Scope defers to the not-yet-existing per-component criticality Specification
(`issues/20260831-192510_adr004_06_missing_component_criticality_specification.md`).

## Compatibility considerations

Documentation-only change to ADR-004's Known Deviations section; Decision, Rationale,
and Invariants sections are unmodified. No code, schema, or runtime behavior affected.

## Security considerations

N/A: no security-relevant content in a Known Deviations wording trim.

## Rollback considerations

Trivially revertable via `git revert`/`git checkout` of this single file — reverts to
the three-item "残課題" list, which would then again misstate two already-resolved
items as outstanding.

## Validation plan

- Manual review: confirm only the "残課題" clause changed; Decision/Rationale/
  Invariants sections and the rest of the Known Deviations bullet (Known Issue
  description, 影響/Impact clause) are byte-identical to before the edit.
- `uv run python tools/check_docs_quality.py` and `uv run python
  tools/check_docs_structure.py docs/adr/ADR-004-environment-failure-handling-policy.md`
  — structural checks for the edited file.
- `uv run python tools/check_docs_consistency.py --domain mcp` — this ADR is under the
  `mcp` domain checker's scope (ADR-004 governs MCP server failure handling).

## Completion criteria

The "残課題" clause names only the cross-profile `security_profile` parametrization
item; the default-value-test and issue-archive items are removed from that clause (and
stated as resolved instead); no other part of the document changed.

## Out of scope

Modifying `tests/agent/services/test_mcp_tool_discovery.py` (separate row, seq 03 of
this same Plan). INV-14's own separate, still-open gap (Plan Out-of-Scope). Any
Decision/Rationale/Invariants section content (Plan's own explicit constraint).

## Documentation

`docs/00_index.md`'s "Document References by Task" table maps ADR edits under the
`mcp`/governance area; per `code-implementation` workflow's Step 5, this is itself the
target `docs/*.md` file being edited (not a downstream doc requiring a separate
cross-reference update) — no additional doc beyond this target file is in scope.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-02TXX:XX:XX | 2026-09-02TXX:XX:XX | Trimmed REQ-001/REQ-004 items from "残課題" clause |
| 2 | Add or update tests per Validation plan | Completed | 2026-09-02TXX:XX:XX | 2026-09-02TXX:XX:XX | N/A: documentation-only change, no automated test |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-09-02TXX:XX:XX | 2026-09-02TXX:XX:XX | Doc-quality/structure/consistency checkers passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-09-02TXX:XX:XX | 2026-09-02TXX:XX:XX | N/A: this row's own target file is the documentation being updated |

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
- **Requirement ID**: REQ-005 (trim the "残課題" list to the still-real gap only — the
  entry's rewrite from "解決済み" to "部分解決" was already delivered by a prior cycle,
  see Assumptions)
- **Source issue**: `issues/20260831-192510_adr004_05_mcp_config_alignment_superseded_by_policy_reversal.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-102432_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-183208
- **Related target files**: `docs/adr/ADR-004-environment-failure-handling-policy.md`
