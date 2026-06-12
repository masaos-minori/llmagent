# ツール実行の依存関係解析付きスケジューリング

- 改善案:
  - asyncio.gather() による全並列と serial_tool_calls による全直列の二択をやめ、ツール単位・リソース単位で依存関係を解析し、部分並列化する
- 効果:
  - write→read のような依存関係がある呼び出しでは安全性を保ちつつ、独立ツールは並列化できるため、全直列より高速、全並列より安全な実行が可能になる
- リスク:
  - 依存判定が不完全だと順序バグが残ること。ツール定義メタの追加管理が必要
- 実装方式:
  - tool_definitions に side_effect、resource_scope、requires_serial 等を追加し、同一 resource_scope への write を直列化し、それ以外を並列化する実行プランを生成する方式
- 実装対象:
  - agent_repl.py
  - agent_commands.py
  - agent_config.py
  - tool_executor.py 相当
  - config/agent.json
