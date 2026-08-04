# 起動処理: SIGINT/SIGTERM が起動シーケンス完了までまったく効かない

## 優先度
High

## 概要
`AgentREPL.run()`（`scripts/agent/repl.py`）はREPL入力ループ開始前に SIGTERM/SIGINT のシグナルハンドラを登録するが、`StartupOrchestrator.run()`（`scripts/agent/startup.py`）の起動シーケンス自体はこのシャットダウン要求をどこでも参照していない。そのため、起動処理中（MCPサブプロセスのヘルスチェック待ちなど、数十秒単位でブロックしうる区間）にユーザーが Ctrl-C や SIGTERM を送っても、起動シーケンスが自然に終了する（成功または失敗）までプロセスは一切反応しない。

## 変更理由
`scripts/agent/repl.py` の `run()` は以下のようにシグナルハンドラを登録してから起動処理を呼び出す。

```python
loop = asyncio.get_running_loop()
self._shutdown_event = asyncio.Event()

def _sigterm_handler() -> None:
    self._ctx.conv.shutdown_requested = True
    if self._shutdown_event is not None:
        self._shutdown_event.set()
    ...

for sig in (signal.SIGTERM, signal.SIGINT):
    try:
        loop.add_signal_handler(sig, _sigterm_handler)
    ...

startup = StartupOrchestrator(self._ctx, self._view)
...
self._cmds, self._orchestrator, _spawned_subprocesses = await startup.run()
```

`loop.add_signal_handler()` により、SIGINT を受け取っても `KeyboardInterrupt` は発生せず、代わりに `_sigterm_handler()` が呼ばれて `ctx.conv.shutdown_requested` と `self._shutdown_event` がセットされるだけになる。ところが `scripts/agent/startup.py` 全体を検索しても `shutdown_event` や `shutdown_requested` への参照は一件も存在しない（`grep -n "shutdown_event\|shutdown_requested" scripts/agent/startup.py` の結果は0件）。

`StartupOrchestrator._start_servers()`（`scripts/agent/startup.py:133-204`）や `_verify_mcp_health()`（206-252行目）は、設定されたMCPサブプロセスサーバー1台につき最大 `cfg.startup_timeout_sec` 秒のヘルスチェック待ちループ（`scripts/agent/http_lifecycle.py` の `HttpServerLifecycleManager.start()` 内、0.5秒間隔のポーリング）を行い、さらに1回の起動失敗につき `HEALTH_CHECK_RETRY_DELAY_SEC=1.0` 秒後にリトライを行う。サーバー台数が複数あり、それぞれの `startup_timeout_sec` が数十秒に設定されている場合、起動シーケンス全体が数分間ブロックしうる。この間、`_sigterm_handler()` がフラグを立てるだけで、`await asyncio.sleep(...)` や `await client.get(...)` などの進行中の待機処理は一切中断されない（`_repl_loop()` に入って初めて `shutdown_event`/`shutdown_requested` を参照する競走が始まるため）。

結果として、起動処理がハングしている、あるいは単に時間がかかっている状況で、運用者が Ctrl-C を送っても何も起こらず、SIGKILL 等の強制終了に頼らざるを得ない。強制終了は [[20260804-120001_startup_mcp_subprocess_orphan_on_partial_failure]] で指摘した孤児プロセス問題をさらに悪化させる（正常なクリーンアップ経路を経ずに親プロセスが消えるため、`shutdown_all()` が絶対に呼ばれない）。

## 実装方針
`StartupOrchestrator` に、起動シーケンスの主要な待機ポイント（サーバー起動ループの各イテレーション開始前、ヘルスチェックポーリングループの各反復、リトライ前の `asyncio.sleep` など）で `shutdown_event`（または同等のキャンセルトークン）を参照し、シャットダウン要求があれば速やかに起動処理を中断してこれまでに起動済みのサブプロセスを後始末するロジックを追加する。`asyncio.wait` で本処理タスクと `shutdown_event.wait()` を競走させ、後者が先に完了した場合は `asyncio.CancelledError` 相当で打ち切る、という `scripts/agent/repl.py` の `_repl_loop()` で既に使われているパターンを起動フェーズにも適用することが考えられる。

## 対象ファイル
- `scripts/agent/startup.py`（`StartupOrchestrator.run()`, `_start_servers()`, `_verify_mcp_health()`）
- `scripts/agent/repl.py`（`AgentREPL.run()`、`StartupOrchestrator` へ `shutdown_event` を渡す配線）
- `scripts/agent/http_lifecycle.py`（`HttpServerLifecycleManager.start()` のヘルスチェックポーリングループ、中断可能にする場合）

## 必要な変更
- `StartupOrchestrator` のコンストラクタまたは `run()` に `asyncio.Event`（シャットダウン要求）を渡せるようにする。
- サーバー起動・ヘルスチェックの待機ループにキャンセル判定を組み込み、要求があれば安全にロールバック（`lifecycle.shutdown_all()`）してから終了する。

## 受け入れ基準
- MCPサブプロセスのヘルスチェックが応答しない（または非常に遅い）状況を再現し、起動シーケンス中に SIGINT/SIGTERM を送った場合に、数秒以内に安全に終了処理へ移行することを確認する。
- 起動が正常に完了するケースでは、シグナル登録の追加によって既存の起動フローに回帰がないことを確認する。

## テスト方針
- 起動処理を模した非同期タスク実行中に `shutdown_event.set()` を呼び出し、`StartupOrchestrator.run()` が長時間ブロックせずに終了（例外送出または明示的な中断）することを検証するテストを追加する。
- 既存の起動成功シナリオのテストが壊れていないことを確認する。

## ドキュメントへの影響
運用ドキュメント（起動・停止手順に関するもの、例えば `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` 系）に、起動中のシグナル応答性について記載がある場合は更新が必要か確認する。

## 対象外
REPLループ開始後（`_repl_loop()` 内）のシャットダウン処理は本Issueの対象外。既にシグナル応答の仕組みが存在するため変更不要。

## AI実装時の制約
- `_repl_loop()` で既に確立されている「タスクと `shutdown_event.wait()` を `asyncio.wait(..., return_when=FIRST_COMPLETED)` で競走させる」パターンを踏襲し、独自の新しいキャンセルモデルを導入しないこと。
- 中断時も [[20260804-120001_startup_mcp_subprocess_orphan_on_partial_failure]] で修正されるロールバック処理（`lifecycle.shutdown_all()`）が確実に呼ばれるようにすること。両Issueは合わせて対応することが望ましい。
