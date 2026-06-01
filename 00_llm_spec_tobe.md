# 仕様変更

- LLM に gemma-4-e4b は使わない、Qwen3-Coder-30B-A3B-Instruct Q4_K_M に統一し、切換機能もなし

- 以下の REPL パイプライン処理フローは RAG MCP 呼出に変更、呼出実行をオプションで選択
  ② MQE
  ③ Search
  ④ RRF
  ⑤ Rerank
  ⑥ Dedup
  ⑦ Augment

- MCPサーバは事前に起動済みの前提ではなく、設定に応じてエージェント起動時にサブプロセスで起動
 - MCPサーバの OpenRC サービス起動は不要
 - MCPサーバとの通信は別PCからの呼出を考慮し、HTTPとstdioの両方を残す
