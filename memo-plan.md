# memo-plan.md — plans/done/*.md 監査結果

## 概要

- 総計画書: 2596
- 表形式(`### Execution Status`)計画: 706
  - 未対応ステップあり: 23
  - 全完了: 683
- チェックボックス形式計画: 1887（うち未チェック項目あり: 1848）

## 判定方法

- 信頼できる完了信号は **Execution Status 表**を持つ計画のみ。チェックボックス形式（約1887本）は完了信号として不正確のため詳細リストから除外（未チェック項目数のみ付記）。
- 未対応 = Status が `Completed`/`Done` 以外（`Pending`/`In Progress`/`Blocked`/`Obsolete`）。
- 実行済みと推定される条件: 計画書が**自身の手続文档**（`implementations/YYYYMMDD-HHMMSS_NN_`、生成時刻＝計画時刻以降）を明示参照すること。この参照がない場合は実行証拠なしとみなす（同一日の複数計画生成による帰属誤りを避けるため。）。
- 本監査は**報告のみ**で、計画書の変更は行わない。

## 分類内訳

| 分類 | ファイル数 | 内容 |
|---|---|---|
| B. 未着手と推定 | 24 | 自身の手続文档参照なし＝信頼できる実行証拠なし。 |
| C. 全完了（完了済み） | 4 | 全ステップがCompleted。memo-plan.mdから除外済み。 |
| D. Obsolete ステップあり | 1 | 一部ステップがObsolete（対象ファイル消滅・統合済み）。 |

## B. 未着手と推定（未対応ステップあり）

合計 24 本。自身の手続文档参照なし＝未着手/実装未着手(self-flag)/正当なPending残留。

### B-1. 全ステップ Pending

- **20260918-120636_plan.md** — 未対応 11 件 [Pending, Pending, Pending, Pending, Pending, Pending, Completed, Completed, Pending, Pending, Completed, Pending, Pending, Pending]
  - `1` [Pending]: Update INV-003 row citation (`docs/adr-index.md`)
  - `2` [Pending]: Update INV-006 row citation (`docs/adr-index.md`)
  - `3` [Pending]: Update INV-007 row citation (`docs/adr-index.md`)
  - `4` [Pending]: Update INV-008 row citation (`docs/adr-index.md`)
  - `5` [Pending]: Update INV-014 row citation (`docs/adr-index.md`)
  - `6` [Pending]: Correct INV-015 row (`docs/adr-index.md`)
  - `7` [Completed]: Create `tests/shared/test_tool_routing_validation.py` + cite INV-005 — INV-005 引用あり
  - `8` [Completed]: Add `rebuild_fts()` test to `tests/rag/test_fts_sync.py` + cite INV-009 — INV-009 引用あり
  - `9` [Pending]: Create `tests/agent/test_failure_handling_policy_cross_cutting.py` (INV-010) + cite
  - `10` [Pending]: Add INV-011 test to same new file + cite
  - `11` [Completed]: Add monotonicity test to `tests/eventbus/test_eventbus_offsets.py` + cite INV-012 — INV-012 引用あり
  - `12` [Pending]: Add ordering test to `tests/eventbus/test_eventbus_publish.py` + cite INV-013
  - `13` [Pending]: Confirm no `scripts/`/`config/` change; no deploy step needed
  - `14` [Pending]: Run full test suite for the 5 new/edited test files

- **20260919-113758_plan.md** — 未対応 4 件 [In Progress, Pending, Pending, Pending]
  - `1` [In Progress]: Verify current state and understand dependencies
  - `2` [Pending]: Core Logic Extraction — extract 6 private methods
  - `3` [Pending]: Documentation Update — update docstring
  - `4` [Pending]: Test Fixes — fix 14 pre-existing failures

- **20261003-150043_plan.md** — 未対応 2 件 [Pending, Pending]
  - `1` [Pending]: Phase 1: Preparation / Investigation
  - `2` [Pending]: Phase 2: Core Logic Implementation

- **20261003-150911_plan.md** — 未対応 2 件 [Pending, Pending]
  - `1` [Pending]: Phase 1: Preparation / Investigation
  - `2` [Pending]: Phase 2: Core Logic Implementation

- **20261003-153234_plan.md** — 未対応 2 件 [Pending, Pending]
  - `1` [Pending]: Phase 1: Preparation / Investigation
  - `2` [Pending]: Phase 2: Core Logic Implementation

- **20261003-153350_plan.md** — 未対応 2 件 [Pending, Pending]
  - `1` [Pending]: Phase 1: Preparation / Investigation
  - `2` [Pending]: Phase 2: Core Logic Implementation

- **20261003-153514_plan.md** — 未対応 2 件 [Pending, Pending]
  - `1` [Pending]: Phase 1: Preparation / Investigation
  - `2` [Pending]: Phase 2: Core Logic Implementation

- **20261003-153633_plan.md** — 未対応 2 件 [Pending, Pending]
  - `1` [Pending]: Phase 1: Preparation / Investigation
  - `2` [Pending]: Phase 2: Core Logic Implementation

- **20261003-153754_plan.md** — 未対応 2 件 [Pending, Pending]
  - `1` [Pending]: Phase 1: Preparation / Investigation
  - `2` [Pending]: Phase 2: Core Logic Implementation

- **20261003-153913_plan.md** — 未対応 2 件 [Pending, Pending]
  - `1` [Pending]: Phase 1: Preparation / Investigation
  - `2` [Pending]: Phase 2: Core Logic Implementation

- **20261003-154033_plan.md** — 未対応 2 件 [Pending, Pending]
  - `1` [Pending]: Phase 1: Preparation / Investigation
  - `2` [Pending]: Phase 2: Core Logic Implementation

- **20261003-154150_plan.md** — 未対応 2 件 [Pending, Pending]
  - `1` [Pending]: Phase 1: Preparation / Investigation
  - `2` [Pending]: Phase 2: Core Logic Implementation

- **20261003-154314_plan.md** — 未対応 2 件 [Pending, Pending]
  - `1` [Pending]: Phase 1: Preparation / Investigation
  - `2` [Pending]: Phase 2: Core Logic Implementation

- **20261003-154435_plan.md** — 未対応 2 件 [Pending, Pending]
  - `1` [Pending]: Phase 1: Preparation / Investigation
  - `2` [Pending]: Phase 2: Core Logic Implementation

- **20261003-154602_plan.md** — 未対応 2 件 [Pending, Pending]
  - `1` [Pending]: Phase 1: Preparation / Investigation
  - `2` [Pending]: Phase 2: Core Logic Implementation

### B-2. 一部 In Progress（コード実装中）

- **20261004-182816_plan.md** — 未対応 6 件 [In Progress, In Progress, In Progress, In Progress, In Progress, In Progress]
  - `1` [In Progress]: Phase 1a: Check TurnState for approval metadata
  - `2` [In Progress]: Phase 1b: Verify startup sequence order
  - `3` [In Progress]: Phase 2a: Add comparison before overwrite
  - `4` [In Progress]: Phase 2b: Update warning message
  - `5` [In Progress]: Phase 3a: Add regression tests
  - `6` [In Progress]: Phase 3b: Run existing tests

- **20261004-194533_plan.md** — 未対応 3 件 [In Progress, Completed, In Progress, In Progress]
  - `1` [In Progress]: Phase 1: Preparation — confirm `retry_helper` delegation
  - `2` [Completed]: Phase 2: Core logic — value-leak fix 実装済み（`m.group(1) + "***MASKED***"` に変更、値の長さ非依存の完全マスク）
  - `3` [In Progress]: Phase 3: Tests & verification — new module + validation sequence
  - `4` [In Progress]: Phase 4: Documentation — update startup-and-health doc

- **20261006-100352_plan.md** — 全完了（全ステップ完了）
  - `1` [Completed]: No preparation required — single-token substitution
  - `2` [Completed]: Replace in `deploy/start_agent.sh` (UV_SYSTEM_CERTS=true に置換済み)
  - `3` [Completed]: Replace in `deploy/setup_services.sh` (UV_SYSTEM_CERTS=true に置換済み)
  - `4` [Completed]: Replace in `deploy/init_db.sh` (UV_SYSTEM_CERTS=true に置換済み)
  - `5` [Completed]: Replace in `deploy/deploy.sh` (UV_SYSTEM_CERTS=true に置換済み)
  - `6` [Completed]: Static grep + `start_agent.sh` runtime verification（UV_NATIVE_TLS 消滅確認済み）

- **20261006-113432_plan.md** — 未対応 1 件 [Pending, Completed, Pending]
  - `1` [Pending]: Phase 1: Preparation / Refactoring (if needed)
  - `2` [Completed]: Phase 2: Core Logic Implementation — same-state STOPPED→STOPPED transition 追加済み（`_VALID_TRANSITIONS[LifecycleState.STOPPED] |= frozenset({LifecycleState.STOPPED})`）
  - `3` [Pending]: Phase 3: Deployment & Verification

- **20261006-114718_plan.md** — 未対応 2 件 [Pending, In Progress]
  - `1` [Pending]: Phase 1: Preparation / Investigation
  - `2` [In Progress]: Phase 2: Core Logic Implementation

- **20261014-093347_plan.md** — 未対応 1 件 [In Progress]
  - `4` [In Progress]: Deploy via `deploy.sh` production validation gate

- **20261014-160933_plan.md** — 未対応 1 件 [Pending, Completed, Completed]
  - `1` [Pending]: Phase 1: Preparation — confirm schema via `scripts/db/schema_sql.py`
  - `2` [Completed]: Phase 2: Core Logic — add `message_count` (session.py), extend `SessionRow` (models.py), render column (cmd_session.py) — コミット `3e3eaa1ea` で実装済み
  - `3` [Completed]: Phase 3: Tests, Docs & Verification — unit test, roundtrip test, doc updates, lint/type checks

### B-3. 一部 Pending（完了済みステップあり）

- **20261006-093924_plan.md** — 全完了（全ステップ完了）
  - `7` [Completed]: `start_agent.sh` integration check — `uv` が両 allowlist に追加済み（`http_lifecycle_command_validator.py:27`, `http_lifecycle.py:69`）

- **20261006-095454_plan.md** — 未対応 3 件 [Pending, Pending, Pending]
  - `1` [Pending]: Resolve UNK-01..03 with a maintainer (confirm allowed paths/repos/workflows)
  - `5` [Pending]: Deploy via `deploy/deploy.sh`
  - `6` [Pending]: Startup + per-server operation verification

## D. Obsolete ステップあり

合計 1 本。一部ステップが Obsolete（対象ファイル消滅・統合済み）。

- **20260903-090104_plan.md** — 未対応 1 件 [Obsolete]
  - `3` [Obsolete]: `docs/04_mcp_90_inconsistencies_and_known_issues.md` — ファイル統合済み（`docs/00_governance_03_issue-and-uncertainty-management.md` に移行）
  - `1` [Completed]: `docs/agent_13_reference-api.md` — `server_configs` 主張削除済み
  - `2` [Completed]: `docs/04_mcp_03_01_dispatch-and-routing.md` — 追加分加筆済み（ただし当該ファイルも後に削除）

## 付記：チェックボックス形式

- チェックボックス形式計画 1887 本（うち未チェック項目あり 1848 本）。
- 完了信号として不正確なため詳細リストから除外。個別確認が必要なら別途監査が必要。
