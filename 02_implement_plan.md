# MCP Transport Transparency and Dual Startup Modes - 実装計画

## Goal

MCPサーバーのTransport（HTTP/stdio）と起動モード（persistent/ondemand）を抽象化し、AgentがTransportと起動モードの違いを意識せずにMCPサーバーを利用できるようにする。

## Scope

- MCPサーバーのTransportと起動モードの設定を明示的に定義
- ToolExecutorをTransport透明なクライアント層にリファクタリング
- ServerLifecycleManagerを導入し、persistent/ondemandの起動を管理
- mcp_server.pyをHTTP/stdioの両方に対応する双方向サーバーベースにリファクタリング
- web-search-mcp, file-mcp, github-mcpサーバーを双方向モードに対応
- tool-definitionチェックをTransport非依存に
- watchdogと/mcpコマンドをTransportと起動モードに対応

## Assumptions

- 現在のHTTPとstdioのTransportはすでに実装されている
- ToolExecutorはHttpTransportとStdioTransportの両方をサポートしている
- 現在のMCPサーバーはHTTP専用の実装になっている
- AgentREPLは現在の初期化と終了処理の流れを維持する必要がある

## Unknowns

- 現在のMCPサーバーの実装で、transport非依存なdispatchメソッドが正しく実装されているか
- stdioモードでのサーバー起動と終了処理の実装方法
- 現在のtool-definitionチェックの仕組みがstdioモードに対応できるか
- 現在のwatchdogと/mcpコマンドの実装がTransport非依存にできるか

## Affected areas

- `tool_executor.py` - ToolExecutorのリファクタリング
- `mcp_server.py` - MCPサーバー基底クラスのリファクタリング
- `web_search_mcp_server.py`, `fileop_mcp_server.py`, `github_mcp_server.py` - 各MCPサーバーの--stdioモード対応
- `agent_repl.py` - AgentREPLの初期化と終了処理の変更
- `agent_commands.py` - /mcpコマンドの出力変更
- `config/agent.toml` - McpServerConfigの拡張

## Design

1. McpServerConfigにtransportとstartup_modeのフィールドを追加
2. ToolExecutorをTransport透明なクライアント層に変更
3. ServerLifecycleManagerを導入し、起動モードを管理
4. mcp_server.pyをHTTP/stdioの両方に対応する双方向サーバーベースに変更
5. 各MCPサーバーに--stdioモードを追加
6. tool-definitionチェックをTransport非依存に
7. watchdogと/mcpコマンドをTransportと起動モードに対応

## Implementation steps

1. McpServerConfigの拡張
2. ToolExecutorのリファクタリング
3. ServerLifecycleManagerの導入
4. mcp_server.pyのリファクタリング
5. 各MCPサーバーの--stdioモード対応
6. tool-definitionチェックのTransport非依存化
7. watchdogと/mcpコマンドの変更

## Validation plan

- 各MCPサーバーがHTTPモードとstdioモードの両方で正しく動作することを確認
- ToolExecutorがTransport非依存に動作することを確認
- ServerLifecycleManagerが起動モードに応じて適切に動作することを確認
- /mcpコマンドがTransportと起動モードを正しく表示することを確認

## Risks

- Toolの動作がTransportによって異なる可能性
  - 現在の実装では、dispatchメソッドが各MCPサーバーのサブクラスで実装されるため、transport非依存な動作を保証する必要があります。
  - 対策: 各MCPサーバーのdispatchメソッドがtransport非依存であることを確認し、テストで検証する。

- stdioの生存確認がHTTPのhealthチェックより困難
  - stdioサーバーはプロセスの生存確認と、ツールの応答性を確認する必要があります。
  - 対策: `_fetch_stdio_tools()` 関数を使用して、stdioサーバーのツールリストを取得し、応答性を確認する。

- ondemand起動による初回呼び出しの遅延
  - ondemandサーバーは初回呼び出し時に起動するため、遅延が発生する可能性があります。
  - 対策: ondemandサーバーの起動時間と遅延を監視し、必要に応じて設定を調整する。

- 現在のOpenRC中心の運用モデルとの競合
  - HTTP + persistentの運用モデルを維持しつつ、stdio + ondemandを追加するため、既存の運用モデルとの整合性を保つ必要があります。
  - 対策: HTTPサーバーのOpenRC管理とstdioサーバーの起動管理を分離し、それぞれの運用モデルを明確にする。