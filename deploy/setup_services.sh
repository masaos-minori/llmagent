#!/bin/bash
# setup_services.sh
# OpenRC サービスをデプロイし、default ランレベルに登録して起動する。
# deploy.sh 実行後に実行すること。
# llama-agent は LLM サービスのモデルロード完了後に起動すること。
#
# 使用例:
#   bash deploy/setup_services.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== setup_services.sh: サービス設定開始 ==="

# ── init.d スクリプトのデプロイ ───────────────────────────────────────────────
echo "--- init.d スクリプトのコピーと実行権限付与 ---"
for svc in embed-llm llama-chat-llm llama-coding-llm web-search-mcp file-mcp github-mcp llama-agent; do
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

# ── OpenRC サービス登録 ───────────────────────────────────────────────────────
echo "--- OpenRC default ランレベルへの登録 ---"
for svc in embed-llm llama-chat-llm llama-coding-llm web-search-mcp file-mcp github-mcp llama-agent; do
    rc-update add "${svc}" default
    echo "  登録完了: ${svc}"
done

# ── LLM サービス起動 (llama-agent はモデルロード後に手動起動) ─────────────────
echo "--- LLM・MCP サービス起動 ---"
for svc in embed-llm llama-chat-llm llama-coding-llm web-search-mcp file-mcp github-mcp; do
    rc-service "${svc}" start
    echo "  起動完了: ${svc}"
done

# ── ヘルスチェック ────────────────────────────────────────────────────────────
echo "--- ヘルスチェック (モデルロードに数十秒かかる場合があります) ---"
echo "  embed-llm      (:8003): $(curl -s http://127.0.0.1:8003/health 2>/dev/null || echo 'まだ起動中')"
echo "  llama-chat-llm (:8002): $(curl -s http://127.0.0.1:8002/health 2>/dev/null || echo 'まだ起動中')"
echo "  llama-coding-llm (:8001): $(curl -s http://127.0.0.1:8001/health 2>/dev/null || echo 'まだ起動中')"
echo "  web-search-mcp (:8004): $(curl -s http://127.0.0.1:8004/health 2>/dev/null || echo 'まだ起動中')"
echo "  file-mcp       (:8005): $(curl -s http://127.0.0.1:8005/health 2>/dev/null || echo 'まだ起動中')"
echo "  github-mcp     (:8006): $(curl -s http://127.0.0.1:8006/health 2>/dev/null || echo 'まだ起動中')"

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
