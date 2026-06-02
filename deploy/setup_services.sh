#!/bin/bash
# setup_services.sh
# OpenRC サービスをデプロイし、default ランレベルに登録して起動する。
# deploy.sh 実行後に実行すること。
#
# MCP サーバ (ports 8004-8014) はエージェント管理 subprocess として起動するため
# OpenRC への登録は不要。LLM サーバ (ports 8001-8003) のみ OpenRC で管理する。
#
# 使用例:
#   bash deploy/setup_services.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== setup_services.sh: サービス設定開始 ==="

# ── LLM サービスの init.d スクリプトのデプロイ ────────────────────────────────
# MCP サーバ (8004-8014) はエージェントが subprocess として管理するため登録不要
echo "--- LLM init.d スクリプトのコピーと実行権限付与 ---"
for svc in embed-llm llama-chat-llm llama-coding-llm llama-agent; do
    cp "${REPO_ROOT}/init.d/${svc}" "/etc/init.d/${svc}"
    chmod +x "/etc/init.d/${svc}"
    echo "  コピー完了: /etc/init.d/${svc}"
done

# ── conf.d 設定ファイルのデプロイ ─────────────────────────────────────────────
echo "--- conf.d 設定ファイルのコピー ---"
cp "${REPO_ROOT}/conf.d/web-search-mcp" "/etc/conf.d/web-search-mcp"
echo "  コピー完了: /etc/conf.d/web-search-mcp"
echo "  ※ Web 検索を使用する場合は /etc/conf.d/web-search-mcp に API キーを設定してください"
echo "     BRAVE_API_KEY=\"<Brave API キー>\""
echo "     BING_API_KEY=\"<Bing API キー>\"  (任意)"

cp "${REPO_ROOT}/conf.d/github-mcp" "/etc/conf.d/github-mcp"
echo "  コピー完了: /etc/conf.d/github-mcp"
echo "  ※ GitHub 操作を使用する場合は /etc/conf.d/github-mcp に PAT を設定してください"
echo "     GITHUB_TOKEN=\"<GitHub Personal Access Token>\""

# ── OpenRC サービス登録 (LLM サーバのみ) ─────────────────────────────────────
echo "--- OpenRC default ランレベルへの登録 (LLM サーバのみ) ---"
for svc in embed-llm llama-chat-llm llama-coding-llm; do
    rc-update add "${svc}" default
    echo "  登録完了: ${svc}"
done

# ── LLM サービス起動 (llama-agent はモデルロード後に手動起動) ─────────────────
echo "--- LLM サービス起動 ---"
for svc in embed-llm llama-chat-llm llama-coding-llm; do
    rc-service "${svc}" start
    echo "  起動完了: ${svc}"
done

# ── ヘルスチェック ────────────────────────────────────────────────────────────
echo "--- ヘルスチェック (モデルロードに数十秒かかる場合があります) ---"
echo "  embed-llm      (:8003): $(curl -s http://127.0.0.1:8003/health 2>/dev/null || echo 'まだ起動中')"
echo "  llama-chat-llm (:8002): $(curl -s http://127.0.0.1:8002/health 2>/dev/null || echo 'まだ起動中')"
echo "  llama-coding-llm (:8001): $(curl -s http://127.0.0.1:8001/health 2>/dev/null || echo 'まだ起動中')"
echo ""
echo "  ※ MCP サーバ (ports 8004-8014) はエージェント起動時に自動起動します"
echo "     llama-agent 起動後に /mcp status で確認してください"

echo ""
echo "=== setup_services.sh: 完了 ==="
echo ""
echo "次のステップ:"
echo "  # LLM サービスのモデルロード完了を確認してから llama-agent を起動する"
echo "  curl -s http://127.0.0.1:8003/health  # embed-llm"
echo "  curl -s http://127.0.0.1:8002/health  # llama-chat-llm"
echo "  rc-service llama-agent start"
echo ""
echo "  # ドキュメント収集・投入"
echo "  source /opt/llm/venv/bin/activate"
echo "  python /opt/llm/scripts/Crawler.py"
echo "  python /opt/llm/scripts/ChunkSplitter.py"
echo "  python /opt/llm/scripts/RagIngester.py"
