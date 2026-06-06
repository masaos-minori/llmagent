# MCP ヘルスチェックの起動時警告から劣化制御付き運用への強化

- 改善案:
  - 起動時の警告表示だけで継続する方式から、MCP サーバごとに healthy / degraded / unavailable 状態を持ち、劣化時には該当ツールを自動的に無効化する方式へ強化
- 効果:
  - 落ちているツールを LLM が呼び続ける無駄を防ぎ、現在利用不可なツール群をユーザーへ明示できること。障害時の誤動作抑制
- リスク:
  - 一時障害で過剰に無効化すると可用性が落ちること。復旧判定戦略が必要になる
- 実装方式:
  - サーバごとに状態、最終失敗時刻、再起動回数を保持し、ToolExecutor が unavailable サーバのツールを dispatch 対象外にし、/mcp 出力に状態表示を追加する方式
- 実装対象:
  - agent_repl_health.py 相当
  - agent_context.py
  - agent_commands.py
  - tool_executor.py 相当
