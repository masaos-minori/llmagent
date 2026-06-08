# 1. 改修計画書

## 1.1 目的

本計画はの主目的は、後方互換性のために残されている経路を削除し、ツール実行基盤の責務を単純化することにある。
特に、`tool_result_formatter.py` に関する backward compatibility 用 re-export、`tool_runner.py` に残る legacy 実行経路、`tool_approval.py` / `tool_policy.py` に分散した判定責務、`tool_audit.py` の監査イベント不整合を優先的に整理する。

## 1.2 全体方針

- 後方互換性のために残されている機能は削除する。`tool_result_formatter.py` には「`mask_args` moved here from registry.py; registry re-exports it for backward compatibility.」と明記されているため、registry 側の re-export は削除対象とする。
- 実行順序制御は `tool_scheduler.py` の `build_execution_groups()` に一本化する。`tool_runner.py` に残る `_execute_with_dag_legacy()` は旧実装であり、resource-scoped scheduler ベースの経路へ統一する。
- 承認判定、事前 deny、リスク分類の基準は `tool_policy.py` を唯一の源泉に寄せる。`tool_approval.py` に重複しうる repo/path/branch 判定は整理対象とする。
- 監査ログは approval と execution のイベント構造を揃え、masked args・resource scope・decision 情報の一貫性を高める。

## 1.3 対象ファイル

- `agent/tool_result_formatter.py`
- `agent/tool_runner.py`
- `agent/tool_scheduler.py`
- `agent/tool_approval.py`
- `agent/tool_policy.py`
- `agent/tool_audit.py`
- `agent/tool_loop_guard.py`

---

# 2. ファイル別改修内容

## 2.1 `agent/tool_result_formatter.py`

### 2.1.1 現状
docstring に「`mask_args` moved here from `registry.py`; registry re-exports it for backward compatibility.」と記載されている。つまり、`mask_args` の定義元はこのファイルだが、旧参照経路のために別モジュール側でも再公開している。

### 2.1.2 問題点
`mask_args` の参照経路が複数存在すると、マスキング仕様の変更時に依存追跡が難しくなる。後方互換のためだけに re-export を残す構造であり、責務の単一性を損なう。

### 2.1.3 改修方針
- backward compatibility のための re-export を削除する。
- `mask_args` は `tool_result_formatter.py` を唯一の定義元・参照先とする。

### 2.1.4 修正案
- registry 側の `mask_args` 再公開を削除する。
- 呼び出し元 import を `agent.tool_result_formatter import mask_args` に統一する。

### 2.1.5 影響範囲
- 承認、監査、実行結果表示の各経路で使う `mask_args` の import 先が統一される。`tool_approval.py` と `tool_audit.py` は既にこのモジュールへ依存している。

---

## 2.2 `agent/tool_runner.py`

### 2.2.1 現状
`tool_runner.py` は `execute_all_tool_calls()` を public entry point とし、単一 tool call 実行、DAG / serial ordering、結果収集、history injection をまとめて担っている。また、`_execute_with_dag_legacy()` と `_execute_with_dag()` が併存している。

### 2.2.2 問題点
- `_execute_with_dag_legacy()` は名称上も legacy 実装であり、resource-scoped scheduler ベースの `_execute_with_dag()` と重複している。実行順序制御の実装が二重化している。
- 実行順序決定、承認後実行、結果収集、history 反映まで 1 モジュールが抱えており、責務が広い。

### 2.2.3 改修方針
- `_execute_with_dag_legacy()` を削除する。
- DAG / parallel / serial の順序制御は `tool_scheduler.py` ベースの一経路へ統一する。

### 2.2.4 修正案
- `_execute_with_dag_legacy()` を削除し、実行グループの構築は `build_execution_groups()` に統一する。
- `tool_runner.py` は「承認済み call 群の実行」と「結果の集約・履歴反映」を主責務とする方向へ整理する。

### 2.2.5 影響範囲
- `execute_all_tool_calls()` から呼ばれる実行順序が変わる。
- side-effect tool の処理方針は `tool_scheduler.py` のグループ定義へ寄るため、scheduler 側のメタ定義が実質上の唯一の正になる。

---

## 2.3 `agent/tool_scheduler.py`

### 2.3.1 現状
`build_execution_groups()` は `requires_serial=True` の global serial barrier、同一 `resource_scope` かつ `is_write=True` の直列化、それ以外の並列実行をグルーピングする責務を持つ。

### 2.3.2 問題点
scheduler の意図は明確だが、`tool_runner.py` に legacy 実装が併存しているため、現状では execution order の唯一の情報源になり切っていない。

### 2.3.3 改修方針
- `tool_scheduler.py` を execution order の唯一の正とする。
- 他モジュールに残る旧順序ロジックは削除する。

### 2.3.4 修正案
- `tool_runner.py` から legacy 実装を除去し、scheduler の group 結果だけで実行を制御する。

### 2.3.5 影響範囲
- side-effect を含む batch 実行の並列性 / 直列性が scheduler に一本化される。

---

## 2.4 `agent/tool_policy.py`

### 2.4.1 現状
`tool_policy.py` は「Tool risk classification and pre-flight access checks」を担い、`classify_operation_type()`、`classify_risk()`、`check_allowed_root()`、`check_allowed_repo()`、`preflight_deny_reason()` などを持つ。

### 2.4.2 問題点
本来このモジュールが policy ルールの検証可能な唯一の源泉であるべきだが、`tool_approval.py` 側にも GitHub repo 許可判定や escalation に近いロジックがあり、責務が分散しやすい。

### 2.4.3 改修方針
- repo/path/branch に関わるリスク分類と deny 判定は `tool_policy.py` に統一する。
- `tool_approval.py` には承認 UI / approval flow のみを残す。

### 2.4.4 修正案
- `tool_approval.py` にある `_check_github_repo_allowed()` や `_escalate_by_args()` のような policy 由来の判定を、必要に応じて `tool_policy.py` へ移す。
- risk / deny / escalation ルールは `tool_policy.py` 側に集約する。

### 2.4.5 影響範囲
- `tool_approval.py` の判断ロジック。
- `tool_audit.py` で使う operation type や resource scope の監査内容。

---

## 2.5 `agent/tool_approval.py`

### 2.5.1 現状
`tool_approval.py` は「Interactive tool approval flow: risk-based prompts and plan-mode blocking」を担い、`tool_policy.py`、`tool_audit.py`、`tool_result_formatter.py` に依存している。

### 2.5.2 問題点
`tool_approval.py` の中に、repo 許可判定、arg による escalation、dry-run preview、interactive prompt、approval decision 構築が混在している。approval flow と policy 判定が完全に分離されていない。

### 2.5.3 改修方針
- `tool_approval.py` は「承認処理の進行」と「UI interaction」に責務を限定する。
- policy 由来の判定は `tool_policy.py` に寄せる。

### 2.5.4 修正案
- `_check_github_repo_allowed()` と `_escalate_by_args()` の責務を見直し、policy 層へ移動できるものは移す。
- `check_approval()` / `run_approval_checks()` の戻り値表現は、今後 approval result 型へ統一する前提で整理する。高優先度としてはまず責務の整理を先行する。

### 2.5.5 影響範囲
- 承認 prompt の前に表示する preview および deny / escalate の判定順序。
- `tool_runner.py` が呼ぶ approval flow 全体。

---

## 2.6 `agent/tool_audit.py`

### 2.6.1 現状
`tool_audit.py` は `audit_approval()`、`log_approval_decision()`、`audit_tool_exec()` の 3 系統の structured audit log を出す。`audit_approval()` では resource scope を記録するが、`audit_tool_exec()` では `mcp_request_id` と `args_preview` 中心であり、approval 側と項目が揃っていない。

### 2.6.2 問題点
承認イベントと実行イベントで監査項目が非対称であるため、後段の分析で「どの resource に対して 어떤 decision の後に 어떤 exec が行われたか」を追いにくい。

### 2.6.3 改修方針
- approval / decision / exec の監査イベント schema を揃える。
- masked args、operation type、resource scope、decision / is_error の扱いを統一する。

### 2.6.4 修正案
- `audit_tool_exec()` にも approval 側と同程度の resource scope / operation type を含める構造へ見直す。
- `log_approval_decision()` を含め、approval 系 event の共通 schema を定める。

### 2.6.5 影響範囲
- audit logger の downstream 解析。
- `tool_approval.py` と `tool_runner.py` の監査呼び出し。

---

## 2.7 `agent/tool_loop_guard.py`

### 2.7.1 現状
`tool_loop_guard.py` は `orchestrator.py` から抽出された guard であり、`TurnLoopState` に per-turn mutable state を集約し、duplicate call detection、cycle detection、retry suppression、consecutive error limiting を担当する。

### 2.7.2 問題点
このモジュールへ guard 責務を集約した意図は明確だが、もし caller 側に旧 guard 相当ロジックが残っていれば、状態管理や hint 注入が二重化する。分割後の唯一の guard 実装として固定すべきである。

### 2.7.3 改修方針
- dedup / cycle / retry suppression / consecutive error のロジックは `tool_loop_guard.py` を唯一の実装にする。
- caller 側に残る互換コードがあれば削除する。

### 2.7.4 修正案
- `TurnLoopState` を唯一の per-turn state 形として扱い、外部で同等 state を持たないよう整理する。

### 2.7.5 影響範囲
- `LLMTurnRunner` からの guard 呼び出し経路。取得済み記述では `ToolLoopGuard` は per-turn mutable state を伴う唯一の guard として使われる前提である。

---

# 3. 実施順序

## 3.1 Phase 1
1. `tool_result_formatter.py` の backward compatibility 経路削除。
2. `tool_runner.py` の `_execute_with_dag_legacy()` 削除。
3. `tool_scheduler.py` を execution order の唯一の正へ統一。

## 3.2 Phase 2
4. `tool_policy.py` と `tool_approval.py` の責務再編。
5. `tool_audit.py` の監査 event schema 統一。

## 3.3 Phase 3
6. `tool_loop_guard.py` を唯一の guard 実装として固定し、caller 側残存ロジックを除去。
