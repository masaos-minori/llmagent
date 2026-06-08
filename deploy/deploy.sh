#!/bin/bash
# deploy.sh
# Python スクリプト・設定ファイル・SQL ファイルをデプロイ先にコピーする。
# 実行前提: リポジトリのルートディレクトリから実行すること。
#
# 使用例:
#   cd /path/to/repo
#   bash deploy/deploy.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEPLOY_SCRIPTS="/opt/llm/scripts"
DEPLOY_CONFIG="/opt/llm/config"
DEPLOY_DB="/opt/llm/db"
DEPLOY_LOGS="/opt/llm/logs"
DEPLOY_RAG_SRC="/opt/llm/rag-src"

echo "=== deploy.sh: デプロイ開始 ==="
echo "リポジトリ: ${REPO_ROOT}"

# ── ディレクトリ作成 ──────────────────────────────────────────────────────────
echo "--- ディレクトリ作成 ---"
mkdir -p "${DEPLOY_SCRIPTS}"
mkdir -p "${DEPLOY_CONFIG}"
mkdir -p "${DEPLOY_DB}"
mkdir -p "${DEPLOY_LOGS}"
mkdir -p "${DEPLOY_RAG_SRC}/chunk"
mkdir -p "${DEPLOY_RAG_SRC}/registered"
mkdir -p /opt/llm/memory

# ── uv プロジェクト設定 ───────────────────────────────────────────────────────
echo "--- pyproject.toml / uv.lock → /opt/llm/ ---"
cp "${REPO_ROOT}/pyproject.toml" "/opt/llm/"
cp "${REPO_ROOT}/uv.lock" "/opt/llm/"

# ── Python スクリプト (パッケージ構造ごと同期) ────────────────────────────────
echo "--- scripts/ → ${DEPLOY_SCRIPTS}/ ---"
rsync -av --delete \
  --exclude="__pycache__/" \
  --exclude="*.pyc" \
  --exclude="*.pyo" \
  "${REPO_ROOT}/scripts/" "${DEPLOY_SCRIPTS}/"

# ── プラグイン ────────────────────────────────────────────────────────────────
echo "--- plugins/ → /opt/llm/plugins/ ---"
mkdir -p /opt/llm/plugins
# 既存ファイルを上書きしない (プロダクション固有プラグインを保護)
cp -n "${REPO_ROOT}/plugins/"*.py /opt/llm/plugins/ 2>/dev/null || true

# ── 設定ファイル ──────────────────────────────────────────────────────────────
echo "--- config/*.toml → ${DEPLOY_CONFIG}/ ---"
cp "${REPO_ROOT}/config/common.toml"                    "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/agent.toml"                     "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/rag_pipeline.toml"              "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/web_search_mcp_server.toml"     "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/github_mcp_server.toml"         "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/file_read_mcp_server.toml"      "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/file_write_mcp_server.toml"     "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/file_delete_mcp_server.toml"    "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/shell_mcp_server.toml"          "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/rag_pipeline_mcp_server.toml"   "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/sqlite_mcp_server.toml"         "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/cicd_mcp_server.toml"          "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/mdq_mcp_server.toml"           "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/git_mcp_server.toml"           "${DEPLOY_CONFIG}/"

# ── SQL 参照定義 ──────────────────────────────────────────────────────────────
echo "--- db/rrf.sql → ${DEPLOY_DB}/ ---"
cp "${REPO_ROOT}/db/rrf.sql" "${DEPLOY_DB}/"

echo "=== deploy.sh: 完了 ==="
echo ""
echo "次のステップ:"
echo "  1. bash deploy/init_db.sh      # DB スキーマ初期化"
echo "  2. bash deploy/setup_services.sh  # OpenRC サービス登録・起動"