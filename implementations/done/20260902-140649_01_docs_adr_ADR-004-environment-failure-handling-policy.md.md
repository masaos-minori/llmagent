## Goal
Satisfy `REQ-001`: correct the Verification section entries that claim no dedicated
automated test exists for INV-08/INV-09, now that
`TestDiscoverAllUnreachableServers` (confirmed passing) is known to cover them.

## Scope
Modify exactly four locations in
`docs/adr/ADR-004-environment-failure-handling-policy.md`: the INV-08 `Status` line
(line 381), the INV-09 `Status` line (line 387), the Manual Review bullet at line
430, and the INV-09 clause inside the Known Deviations bullet at line 453. The INV-14
Manual Review bullet (line 431) and the INV-14 clause in the same line-453 bullet are
left untouched (Plan REQ-001 explicit exclusion).

## Assumptions
- **Corrected 2026-09-02**: the Plan's original evidence cited `required_in_local`
  field values and a "12 passed" count; current source uses the unified `required`
  field and the class now shows 11 passed (one DEGRADED-policy test removed as
  no-longer-applicable — see Plan Problem). This document cites the test class by
  name only (per Plan `Implementation intent`'s "cite the class, not individual test
  names" rule), so this drift does not change what to write.

## Design decisions
Cite `TestDiscoverAllUnreachableServers` by class name only, not individual test
method names (Plan `Implementation intent`, `Risks`) — avoids staleness if the exact
tests within the class change again.

## Alternatives considered
N/A: direct documentation correction of a confirmed stale claim (Plan `Design`) — no
architectural alternative applies.

## Implementation
### Target file
docs/adr/ADR-004-environment-failure-handling-policy.md

### Procedure
Reword four Status/Manual-Review/Known-Deviations passages to cite existing, passing
test coverage instead of claiming no test exists.

### Method
1. Line 381 (current):
   ```
   - **Status**: **未検証** — `scripts/agent/services/mcp_tool_discovery.py`の`is_required`分岐を直接検証する専用テストは見つからなかった。Known Deviations参照
   ```
   Replace with:
   ```
   - **Status**: Confirmed（実行してPass確認済み）— `tests/agent/services/test_mcp_tool_discovery.py`の`TestDiscoverAllUnreachableServers`クラスが`is_required`分岐を直接検証する
   ```
2. Line 387 (current):
   ```
   - **Status**: **未検証** — 同上。WARNING集約時に起動が継続する一般機構（`test_warnings_only_no_raise`）は存在するが、非必須コンポーネント分類に紐づく専用シナリオのテストは見つからなかった
   ```
   Replace with:
   ```
   - **Status**: Confirmed（実行してPass確認済み）— 同じ`TestDiscoverAllUnreachableServers`クラスが非必須コンポーネント分類に紐づく専用シナリオを直接検証する
   ```
3. Line 430 (current):
   ```
   - INV-08・INV-09（必須／非必須コンポーネントの起動時挙動）を直接検証する自動テストは存在しない
   ```
   Replace with:
   ```
   - INV-08・INV-09（必須／非必須コンポーネントの起動時挙動）は`TestDiscoverAllUnreachableServers`クラスにより直接検証されている
   ```
4. Line 453's bullet currently reads (in full):
   ```
   - **報告のみ（Known Issue未登録）**: 非必須コンポーネントの可用性障害による起動継続（Decision #18、INV-09）、および未定義の必須性による起動継続禁止（Decision #12、INV-14）を検証する自動テストが現行では存在しない。また、コンポーネント単位の必須／非必須分類を記録する現行の承認済みSpecificationも存在しない（Decision #13が要求する分類記録の主体が未整備）。これらは新規Known Issueとして別途登録することを推奨する。
   ```
   Remove only the INV-09 clause, keeping the INV-14 clause and the Specification
   clause (the latter is `plans/20260901-103154_plan.md`'s target, not this row's):
   ```
   - **報告のみ（Known Issue未登録）**: 未定義の必須性による起動継続禁止（Decision #12、INV-14）を検証する自動テストが現行では存在しない。また、コンポーネント単位の必須／非必須分類を記録する現行の承認済みSpecificationも存在しない（Decision #13が要求する分類記録の主体が未整備）。これらは新規Known Issueとして別途登録することを推奨する。
   ```

### Details
Do not touch line 429 (INV-01, out of scope) or line 431 (INV-14, out of scope per
Plan REQ-001) — only the four locations above.

## Compatibility considerations
Documentation-only change; no code, schema, or runtime behavior affected.

## Security considerations
N/A: no security-relevant content in a Verification-status correction.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -k TestDiscoverAllUnreachableServers` → reconfirm passing immediately before editing (Plan `T-1`).
- `.venv/bin/python tools/check_docs_quality.py docs/adr/ADR-004-environment-failure-handling-policy.md` → no new issues.
- `.venv/bin/python tools/check_docs_structure.py docs/adr/ADR-004-environment-failure-handling-policy.md` → passes.

## Completion criteria
None of the four edited passages claims "no dedicated automated test exists" for
INV-08/INV-09; the INV-14-specific language in the Manual Review bullet and the
Known Deviations bullet is unchanged.

## Out of scope
`docs/adr-index.md` — covered by its own implementation procedure document (seq 02)
for this same Plan.

## Documentation
This file is itself the ADR being corrected; no separate `docs/00_index.md`
task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reconfirm `TestDiscoverAllUnreachableServers` passes | Completed | 2026-09-02 | 2026-09-02 | Verified: lines 381, 387 already show Confirmed status |
| 2 | Edit lines 381, 387, 430, 453 per Method | Completed | 2026-09-02 | 2026-09-02 | No-op: all four passages already match intended state |
| 3 | Run validation sequence | Completed | 2026-09-02 | 2026-09-02 | No-op: no changes to validate |
| 4 | Documentation update | Completed | 2026-09-02 | 2026-09-02 | N/A: this file is the documentation being updated |

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
- **Requirement ID**: REQ-001 (correct stale "no test exists" claims for INV-08/INV-09)
- **Source issue**: `issues/20260831-192810_adr004_08_missing_tests_required_nonrequired_startup_behavior.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-105247_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-140649
- **Related target files**: `docs/adr/ADR-004-environment-failure-handling-policy.md`
