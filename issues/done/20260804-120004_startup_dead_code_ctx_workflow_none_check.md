# 起動処理: `_recover_pending_approvals()` の `ctx.workflow is None` チェックが常にFalseで到達不能

## 優先度
Low

## 概要
`StartupOrchestrator._recover_pending_approvals()`（`scripts/agent/startup.py`）の先頭にある `if ctx.workflow is None: return` は、`ctx.workflow` が `AgentContext.__init__()` で常に `WorkflowState()` インスタンスとして無条件に生成されるため、実行時に成立することがない到達不能コードになっている。

## 変更理由
`scripts/agent/startup.py:515-520` は以下の通り。

```python
async def _recover_pending_approvals(self) -> None:
    """Restore workflow approval-pending state from a previous session."""
    ctx = self._ctx
    if ctx.workflow is None:
        return
    store = StateStore()
    ...
```

一方 `scripts/agent/context.py` の `AgentContext.__init__()`（271-284行目）では次のように無条件に代入されている。

```python
def __init__(self) -> None:
    """Create an empty AgentContext with default state objects."""
    self.conv = ConversationState()
    self.turn = TurnState()
    self.stats = RuntimeStats()
    self.workflow = WorkflowState()
    ...
```

`self.workflow` は型ヒント上も実行時の代入経路上も `WorkflowState | None` ではなく常に `WorkflowState` であり、`AgentContext` のどのメソッドも後から `None` を再代入していない（`grep -rn "ctx.workflow" scripts/agent` で確認した全参照箇所でも、`orchestrator.py` や `commands/cmd_workflow.py` などは `ctx.workflow.xxx` の属性アクセスのみを行っており、`None` チェックは `startup.py` のこの1箇所だけ）。したがって `if ctx.workflow is None:` は常に `False` と評価され、以降のペンディング承認復元処理（`StateStore` からの `find_all_pending_approvals` 呼び出しなど）は常に実行される。

このチェックが「ワークフロー追跡が無効な場合は承認復元処理をスキップする」という意図で書かれたものだとすれば、その意図は現状のコードでは全く機能していない。実害としては、ワークフロー機能を使わない/無効化したい場合であっても毎回 `StateStore()` 接続と `find_all_pending_approvals` の問い合わせが行われる、という軽微な無駄処理にとどまるが、コードの意図と実際の挙動が食い違っており、将来の変更時に誤読を招く。

## 実装方針
以下のいずれかを選択する。
- (a) 到達不能であることを踏まえ、`if ctx.workflow is None: return` を削除する。
- (b) 本来「ワークフロー追跡が無効な場合はスキップする」という意図だったのであれば、実際にその状態を表すフラグ（例: ワークフロー定義が読み込めなかったことを示す `Orchestrator._workflow_def is None` 相当の状態、あるいは設定フラグ）を参照するよう修正する。

いずれを選ぶかは、この分岐が導入された経緯（当時 `ctx.workflow` が `Optional` だった名残りかどうか）を踏まえて判断する必要があるため、対応時に確認すること。

## 対象ファイル
- `scripts/agent/startup.py`（`StartupOrchestrator._recover_pending_approvals()`）
- `scripts/agent/context.py`（`AgentContext.__init__()`, `WorkflowState` 定義、参考情報として）

## 必要な変更
- 到達不能な `None` チェックの削除、または本来意図していたであろう有効な条件への置き換え。

## 受け入れ基準
- `_recover_pending_approvals()` の呼び出しが、意図した条件（もしあれば）でのみペンディング承認復元処理を実行することを確認する。
- 既存の承認復元機能（前回セッションからの pending approval 復元）に回帰がないことを確認する。

## テスト方針
- 変更後、通常の起動シーケンスで pending approval が正しく復元されることを既存テスト（`tests/agent/test_startup.py` 等、存在する場合）で確認する。
- (b) を選んだ場合は、意図した条件でスキップされるケースのテストを追加する。

## ドキュメントへの影響
特になし。

## 対象外
`WorkflowState` や `Orchestrator._workflow_def` の設計自体の変更は本Issueの対象外。あくまで到達不能な条件分岐の整理が対象。

## AI実装時の制約
- この分岐が本当に到達不能かどうかを実装前に再確認すること（`grep -rn "ctx.workflow ="`等で `AgentContext` 以外からの再代入がないことを確認する）。
- 意図が不明な場合は (a) の単純削除を優先し、意図の復元（(b)）は別途要件確認のうえで対応すること。
