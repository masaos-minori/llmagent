#!/bin/bash
# setup_services.sh
# サービスをデプロイし、起動する。
# deploy.sh 実行後に実行すること。
#
# MCP サーバ (ports 8004-8014) はエージェント管理 subprocess として起動。
# LLM サーバ (ports 8001-8003) もエージェント管理 subprocess として起動する。
#
# 使用例:
#   bash deploy/setup_services.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== setup_services.sh: サービス設定開始 ==="

# ── LLM サービスのサブプロセス起動 ─────────────────────────────────────────────
# MCP サーバ (8004-8014) はエージェントが subprocess として管理するため登録不要
echo "--- LLM サービスの起動 ---"
for svc in embed-llm agent-llm; do
    echo "  起動: ${svc}"
done

# ── LLM サービス起動 (llama-agent はモデルロード後に手動起動) ─────────────────
echo "--- LLM サービス起動 ---"
for svc in embed-llm agent-llm; do
    echo "  起動: ${svc}"
done

# ── ヘルスチェック ────────────────────────────────────────────────────────────
echo "--- ヘルスチェック (モデルロードに数十秒かかる場合があります) ---"
echo "  embed-llm      (:8003): $(curl -s http://127.0.0.1:8003/health 2>/dev/null || echo 'まだ起動中')"
echo "  agent-llm      (:8001): $(curl -s http://127.0.0.1:8001/health 2>/dev/null || echo 'まだ起動中')"
echo ""
echo "  ※ MCP サーバ (ports 8004-8014) はエージェント起動時に自動起動します"
echo "     llama-agent 起動後に /mcp status で確認してください"

echo ""
echo "=== setup_services.sh: 完了 ==="
echo ""
echo "次のステップ:"
echo "  # LLM サービスのモデルロード完了を確認してから llama-agent を起動する"
echo "  curl -s http://127.0.0.1:8003/health  # embed-llm"
echo "  curl -s http://127.0.0.1:8001/health  # agent-llm"
echo ""
echo "  # ドキュメント収集・投入 (uv run を使用)"
echo "  cd /opt/llm"
echo "  PYTHONPATH=/opt/llm/scripts uv run python /opt/llm/scripts/Crawler.py"
echo "  PYTHONPATH=/opt/llm/scripts uv run python /opt/llm/scripts/ChunkSplitter.py"
echo "  PYTHONPATH=/opt/llm/scripts uv run python /opt/llm/scripts/RagIngester.py"
