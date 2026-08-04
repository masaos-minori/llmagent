# 起動処理: MCPサブプロセス起動が途中失敗した際に既に起動済みのサブプロセスが後始末されず孤児化する

## 優先度
Critical

## 概要
`StartupOrchestrator.run()`（`scripts/agent/startup.py`）において、`_start_servers()` が複数のMCPサブプロセスを順番に起動する途中で例外を送出した場合、それ以前に正常起動済みのMCPサブプロセスが `shutdown_all()` によって停止されず、プロセスが孤児化（orphan）する。

## 変更理由
`StartupOrchestrator.run()` は次のようになっている（`scripts/agent/startup.py:67-94`）。

```python
async def run(self) -> tuple[CommandRegistry, Orchestrator, list[subprocess.Popen]]:
    self._initialize()
    _servers_started = False
    self._spawned_subprocesses: list[subprocess.Popen] = []
    try:
        self._spawned_subprocesses = await self._start_servers()
        _servers_started = True
        await self._verify_mcp_health()
        ...
    except Exception as setup_err:
        if _servers_started:
            try:
                await self._ctx.services_required.lifecycle.shutdown_all()
            except Exception as shutdown_err:
                logger.error(...)
        raise setup_err
```

`_servers_started = True` は `await self._start_servers()` が **正常に return した後** にのみ設定される。しかし `_start_servers()`（`scripts/agent/startup.py:133-204`）は、設定されたMCPサーバーを1台ずつ順番に起動するループの途中で、2台目以降の起動に失敗すると例外を送出する。特に `security_profile == SecurityProfile.PRODUCTION` の場合、リトライ後も失敗すると次の通り即座に `RuntimeError` を送出する（`scripts/agent/startup.py:189-195`）。

```python
except (OSError, RuntimeError) as retry_err:
    if ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION:
        msg = f"{OutputTag.FATAL} MCP subprocess {key!r} failed to start after retry: {retry_err}"
        masked_msg = _mask_secrets(msg)
        logger.error(masked_msg)
        raise RuntimeError(masked_msg) from retry_err
```

このとき、ループの前段で既に正常起動していた別のMCPサーバーのサブプロセスは、`scripts/agent/factory.py` の `_ServerLifecycleRouter`（内部的には `HttpServerLifecycleManager._http_procs`）に既に登録済みである。しかし `_start_servers()` 自体が例外で終了するため `run()` 側の `_servers_started` は `False` のままとなり、`except Exception as setup_err:` ブロックの `if _servers_started:` 条件が成立せず、`lifecycle.shutdown_all()` が一切呼ばれない。

さらに呼び出し元 `scripts/agent/repl.py` の `AgentREPL.run()`（743-851行目）側の後始末処理も救済にならない。

```python
try:
    self._cmds, self._orchestrator, _spawned_subprocesses = await startup.run()
except Exception as e:
    self._view.write_fatal(f"Startup failed: {e}")
    all_procs = _spawned_subprocesses
    if hasattr(startup, "_spawned_subprocesses"):
        all_procs = list(all_procs) + list(startup._spawned_subprocesses)
    for proc in all_procs:
        if proc.poll() is None:
            proc.terminate()
    raise
```

`startup.run()` が例外を送出した場合、タプルへの代入は行われないため `_spawned_subprocesses` は空リストのままである。また `startup._spawned_subprocesses`（`StartupOrchestrator.run()` 内で `_start_servers()` 呼び出し前に `[]` として初期化され、`_start_servers()` が正常 return した場合のみ上書きされるインスタンス属性、`scripts/agent/startup.py:71,73`）も、`_start_servers()` が例外送出した今回のケースでは空リストのままである。

結果として、先に起動済みのMCPサブプロセスは `StartupOrchestrator` からも `AgentREPL` からも参照されず、`terminate()` も `shutdown_all()` も呼ばれずにプロセスとして残り続ける。

## 実装方針
`_servers_started`（または同等のフラグ）を、「`_start_servers()` が正常に return したか」ではなく「1台でもMCPサブプロセスの起動を試みたか」を表すよう変更する。具体的には、`_start_servers()` を呼び出す **前** に `_servers_started = True` を設定するか、`ctx.services_required.lifecycle`（この時点で `_initialize()` により既に構築済み）が保持する内部状態を根拠に、`run()` の `except` ブロックで無条件に `lifecycle.shutdown_all()` を呼び出すようにする。`lifecycle` オブジェクトは `_initialize()` の時点で既に生成されているため、`_start_servers()` の成否に関わらず `shutdown_all()` を安全に呼び出せる。

## 対象ファイル
- `scripts/agent/startup.py`（`StartupOrchestrator.run()`, `_start_servers()`）
- `scripts/agent/repl.py`（`AgentREPL.run()` の後始末ロジック、必要であれば）

## 必要な変更
- `StartupOrchestrator.run()` で、MCPサブプロセスの起動を1つでも試みた場合は必ず `lifecycle.shutdown_all()` が呼ばれるようにフラグの設定タイミングを修正する。
- 可能であれば `_start_servers()` 自体が、途中で例外を送出する前に既に起動したプロセスの一覧を呼び出し元へ伝搬できるようにする（例外オブジェクトに部分結果を添付する、または `finally` で `self._spawned_subprocesses` を更新するなど）。

## 受け入れ基準
- 複数のMCPサブプロセスサーバーが設定された状態で、2台目以降の起動が失敗するケースを再現し、1台目のサブプロセスが確実に終了することを確認する。
- production プロファイルおよび non-production プロファイルの両方で確認する。

## テスト方針
- `tests/agent/test_startup.py`（または相当するテストファイル）に、複数サーバー設定のうち後段のサーバー起動が失敗するシナリオを追加し、先行して起動したサブプロセスの `Popen` オブジェクトに対して `terminate` 相当の処理が呼ばれること（またはプロセスが実際に終了すること）をモックで検証するテストを追加する。

## ドキュメントへの影響
特になし。挙動修正であり、既存ドキュメントとの矛盾は確認されていない。

## 対象外
`HttpServerLifecycleManager` 自体の起動・終了ロジック（`scripts/agent/http_lifecycle.py`）は本Issueの対象外。あくまで `StartupOrchestrator.run()` 側のロールバック判定条件の修正が対象。

## AI実装時の制約
- `_servers_started` フラグの意味変更に伴い、`shutdown_all()` が二重に呼ばれても副作用がないこと（`HttpServerLifecycleManager.shutdown_all()` は空の `_http_procs` に対して安全に動作する）を確認した上で実装すること。
- 変更範囲を `StartupOrchestrator.run()` とその直接の呼び出し関係に限定し、無関係なリファクタリングを行わないこと。
