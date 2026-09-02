# Implementation Procedure Output Template (Canonical)

Use this exact Markdown structure when generating
`implementations/{timestamp}_{seq}_{target_file_slug}.md` in the
`plan-to-implementation-procedure` workflow (see
`skills/plan-to-implementation-procedure/workflow.md` Step 3). `seq` is the row's
1-indexed, zero-padded position within the plan's `Implementation Target Files` table
(`templates/plan.md`), so that sorting the generated filenames lexicographically
reproduces the plan's implementation order. Exactly one document per
`Implementation Target Files` row — see Notes on filling sections below. Do not omit
any section. Write every section's body text in English, regardless of the chat
language (see `skills/plan-to-implementation-procedure/SKILL.md` Core Execution
Rules).

Keep each section concise and file-level (a few bullets each) — this is not a broad
architecture document. Use `N/A: {short reason}` for any section that does not apply
to the item.

```markdown
## Goal

Correct stale "no dedicated automated test exists" / "Not verified" claims in
`docs/adr/ADR-004-environment-failure-handling-policy.md`'s Verification section
for INV-08 and INV-09, citing the existing passing tests in
`tests/agent/services/test_mcp_tool_discovery.py::TestDiscoverAllUnreachableServers`.

## Scope

- Update INV-08 entry: change Status from "**未検証**" to cite
  `TestDiscoverAllUnreachableServers` as confirmed passing coverage.
- Update INV-09 entry: same pattern as INV-08.
- Update Manual Review bullet list: remove the bullet stating no automated test
  exists for INV-08/INV-09.
- Update Known Deviations: split single bullet covering both INV-09 and INV-14 into
  two — INV-09 part becomes "Resolved" citing `TestDiscoverAllUnreachableServers`;
  INV-14 part remains unchanged.
- Leave every other Verification-section entry untouched (INV-03, INV-05, INV-06,
  INV-07, INV-10, INV-11, INV-12, INV-15, INV-16, INV-14 Manual Review bullet).

## Assumptions

- All 12 tests in `TestDiscoverAllUnreachableServers` currently pass (confirmed during
  Plan creation; must reconfirm immediately before editing).
- The unified `required` field has replaced `required_in_production`/`required_in_local`
  in current code (per Known Deviations partial resolution).
- No other contributor has modified the Verification section since the Plan was written.

## Design decisions

- Cite the test class name (`TestDiscoverAllUnreachableServers`) rather than enumerating
  individual test method names, consistent with `skills/DESIGN.md` "Avoid
  implementation-reference duplication".
- Match the existing status format precedent in the same Verification section:
  `Confirmed（実行してPass確認済み）`.

## Alternatives considered

- Enumerate all four specific test method names in the ADR prose — rejected per
  DESIGN.md guidance against implementation-reference duplication.
- Add new tests for INV-08/INV-09 before updating documentation — out of scope; the
  Plan explicitly states tests already exist and are passing.

## Implementation
### Target file
`docs/adr/ADR-004-environment-failure-handling-policy.md`

### Procedure
Apply four targeted edits to the Verification section only.

### Method
Direct edit — modify existing prose in-place; do not add or delete section headers.

### Details

#### Edit 1: INV-08 entry (line ~377-381)

Change:
```
- **Test**: 必須コンポーネント（必須MCPサーバー等）の利用不能が起動を中止させること
  - **Verifies**: INV-08
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: **未検証** — `scripts/agent/services/mcp_tool_discovery.py`の`is_required`分岐を直接検証する専用テストは見つからなかった。Known Deviations参照
```

To:
```
- **Test**: 必須コンポーネント（必須MCPサーバー等）の利用不能が起動を中止させること
  - **Verifies**: INV-08
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: Confirmed（`tests/agent/services/test_mcp_tool_discovery.py::TestDiscoverAllUnreachableServers.test_unreachable_required_server_returns_fatal`、`test_classification_equivalent_across_security_profiles(required_value=True)` で検証済み；`uv run pytest tests/agent/services/test_mcp_tool_discovery.py -k TestDiscoverAllUnreachableServers` → 12 passed）
```

#### Edit 2: INV-09 entry (line ~383-387)

Change:
```
- **Test**: 非必須コンポーネントの可用性障害が起動継続を許可し、当該コンポーネントが無効化されること
  - **Verifies**: INV-09
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: **未検証** — 同上。WARNING集約時に起動が継続する一般機構（`test_warnings_only_no_raise`）は存在するが、非必須コンポーネント分類に紐づく専用シナリオのテストは見つからなかった
```

To:
```
- **Test**: 非必須コンポーネントの可用性障害が起動継続を許可し、当該コンポーネントが無効化されること
  - **Verifies**: INV-09
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: Confirmed（`tests/agent/services/test_mcp_tool_discovery.py::TestDiscoverAllUnreachableServers.test_unreachable_non_required_server_with_fail_fast_returns_warning`、`test_unreachable_non_required_server_with_degraded_returns_warning`、`test_classification_equivalent_across_security_profiles(required_value=False)` で検証済み；`uv run pytest tests/agent/services/test_mcp_tool_discovery.py -k TestDiscoverAllUnreachableServers` → 12 passed）
```

#### Edit 3: Manual Review bullet list (line ~429)

Remove the entire bullet:
```
- INV-08・INV-09（必須／非必須コンポーネントの起動時挙動）を直接検証する自動テストは存在しない
```

Leave the remaining bullets intact:
```
- 障害方針の変更レビュー
- コンポーネントの必須性分類の見直し
- INV-01（単一の共通障害処理方針）を直接検証する自動テストは存在しない
- INV-14（未定義の必須性による起動継続禁止）は現行実装で強制されていない（Known Deviations参照）
```

#### Edit 4: Known Deviations — split single bullet (line ~452-453)

Current single bullet:
```
- **報告のみ（Known Issue未登録）**: 非必須コンポーネントの可用性障害による起動継続（Decision #18、INV-09）、および未定義の必須性による起動継続禁止（Decision #12、INV-14）を検証する自動テストが現行では存在しない。また、コンポーネント単位の必須／非必須分類を記録する現行の承認済みSpecificationも存在しない（Decision #13が要求する分類記録の主体が未整備）。これらは新規Known Issueとして別途登録することを推奨する。
```

Split into two bullets:
```
- **報告のみ（Known Issue未登録）**: 非必須コンポーネントの可用性障害による起動継続（Decision #18、INV-09）を検証する自動テストは、`tests/agent/services/test_mcp_tool_discovery.py::TestDiscoverAllUnreachableServers` にて既に検証済み（上記Verificationセクション参照）。この部分のステータスは更新済み。
- **報告のみ（Known Issue未登録）**: 未定義の必須性による起動継続禁止（Decision #12、INV-14）を検証する自動テストが現行では存在しない。また、コンポーネント単位の必須／非必須分類を記録する現行の承認済みSpecificationも存在しない（Decision #13が要求する分類記録の主体が未整備）。これらは新規Known Issueとして別途登録することを推奨する。
```

## Compatibility considerations

- Both target files are documentation-only; no runtime compatibility impact.
- Citing specific test class names could go stale if those tests are renamed or moved —
  mitigated by using the class name (not individual test names) per DESIGN.md guidance.

## Security considerations

- No security impact: this is a documentation correction only.
- No secrets, keys, or credentials are introduced or modified.

## Rollback considerations

- Revert each edit individually if any change proves incorrect after execution.
- Keep a copy of the original Verification section entries before modification.
- If the tests have regressed since this Plan was written, revert all changes and
  re-evaluate whether the documentation should be updated at all.

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| docs/adr/ADR-004-environment-failure-handling-policy.md | Docs structural check | `uv run python tools/check_docs_structure.py docs/adr/ADR-004-environment-failure-handling-policy.md` | Pass, no new violations |
| docs/adr-index.md | Docs structural check | `uv run python tools/check_docs_structure.py docs/adr-index.md` | Pass |
| tests/agent/services/test_mcp_tool_discovery.py (regression) | Unit (existing) | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -k TestDiscoverAllUnreachableServers` | 12 passed |
| tests/agent/ (full suite) | Regression | `uv run pytest tests/agent/` | All pass |

## Completion criteria

- [ ] Step 1: `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -k TestDiscoverAllUnreachableServers` passes (reconfirms cited tests still pass)
- [ ] Step 2: INV-08 entry Status changed from "**未検証**" to cite `TestDiscoverAllUnreachableServers`
- [ ] Step 3: INV-09 entry Status changed from "**未検証**" to cite `TestDiscoverAllUnreachableServers`
- [ ] Step 4: Manual Review bullet about INV-08/INV-09 removed
- [ ] Step 5: Known Deviations bullet split — INV-09 part marked resolved, INV-14 part unchanged
- [ ] Step 6: Both edited files pass `tools/check_docs_quality.py` and `tools/check_docs_structure.py`

## Out of scope

- Updating `docs/adr-index.md` (Row 2 — classified as Already implemented; INV-019/INV-020
  rows already show "Resolved")
- Adding new tests for INV-08/INV-09
- Changing `scripts/agent/services/mcp_tool_discovery.py`, `scripts/shared/mcp_config.py`,
  or any source/test file
- Defining which components are required/non-required (tracked by separate issue)
- Any INV-14 changes beyond splitting the Known Deviations bullet

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-run `TestDiscoverAllUnreachableServers` to reconfirm passing | Pending | — | — | |
| 2 | Update INV-08 entry in ADR-004 Verification section | Pending | — | — | |
| 3 | Update INV-09 entry in ADR-004 Verification section | Pending | — | — | |
| 4 | Remove INV-08/INV-09 bullet from Manual Review | Pending | — | — | |
| 5 | Split Known Deviations bullet (INV-09 resolved, INV-14 unchanged) | Pending | — | — | |
| 6 | Run docs quality/structure checkers on both files | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: `issues/20260831-192810_adr004_08_missing_tests_required_nonrequired_startup_behavior.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-105247_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-134555
- **Related target files**: docs/adr/ADR-004-environment-failure-handling-policy.md
