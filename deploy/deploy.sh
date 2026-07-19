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

# Workflow: existence + content validation (see docs/02_deployment.md §2.2)
# Mandatory-artifact existence check (source). Scoped to default.json only,
# not the config/workflows/ directory as a whole.
if [[ ! -f "${REPO_ROOT}/config/workflows/default.json" ]]; then
  echo "[FATAL] Missing required workflow definition: config/workflows/default.json" >&2
  echo "This agent requires a valid workflow definition and does not support workflow-disabled mode." >&2
  exit 1
fi

# Workflow: content validation (parseable JSON, required fields/stages/retry-policy)
if ! PYTHONPATH="${REPO_ROOT}/scripts" UV_NATIVE_TLS=true uv run python -m agent.workflow.validate \
     "${REPO_ROOT}/config/workflows/default.json"; then
  echo "[FATAL] Workflow definition failed validation; aborting deployment." >&2
  exit 1
fi

echo "Workflow definition:"
echo "Source   : config/workflows/default.json"
echo "Deployed : /opt/llm/config/workflows/default.json"
PYTHONPATH="${REPO_ROOT}/scripts" UV_NATIVE_TLS=true uv run python -m agent.workflow.validate \
  --print-metadata "${REPO_ROOT}/config/workflows/default.json"
SOURCE_SHA256=$(sha256sum "${REPO_ROOT}/config/workflows/default.json" | awk '{print $1}')
echo "SHA256 (source)   : ${SOURCE_SHA256}"

DEPLOY_SCRIPTS="/opt/llm/scripts"
DEPLOY_CONFIG="/opt/llm/config"
DEPLOY_DB="/opt/llm/db"
DEPLOY_LOGS="/opt/llm/logs"
DEPLOY_RAG_SRC="/opt/llm/rag-src"
DEPLOY_TESTS="/opt/llm/tests"

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
mkdir -p "${DEPLOY_TESTS}"
mkdir -p /opt/llm/storage
mkdir -p /opt/llm/offsets
mkdir -p /opt/llm/deadletter

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

# ── 設定ファイル ──────────────────────────────────────────────────────────────
echo "--- config/*.toml → ${DEPLOY_CONFIG}/ ---"
# Agent
cp "${REPO_ROOT}/config/agent.toml"                     "${DEPLOY_CONFIG}/"
# MCP サーバー (各サーバー専用設定; agent.toml は読み込まない)
cp "${REPO_ROOT}/config/web_search_mcp_server.toml"     "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/github_mcp_server.toml"         "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/file_read_mcp_server.toml"      "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/file_write_mcp_server.toml"     "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/file_delete_mcp_server.toml"    "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/shell_mcp_server.toml"          "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/rag_pipeline_mcp_server.toml"   "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/cicd_mcp_server.toml"           "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/mdq_mcp_server.toml"            "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/git_mcp_server.toml"            "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/browser_mcp_server.toml"        "${DEPLOY_CONFIG}/"
# 取込パイプライン (各スクリプト専用設定; agent.toml は読み込まない)
cp "${REPO_ROOT}/config/crawler.toml"                   "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/chunk_splitter.toml"            "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/ingester.toml"                  "${DEPLOY_CONFIG}/"
# Event Bus
cp "${REPO_ROOT}/config/eventbus.toml"                  "${DEPLOY_CONFIG}/"

# ── Event Bus スキーマ配置 ────────────────────────────────────────────────────
echo "--- schemas/ → /opt/llm/schemas/ ---"
mkdir -p /opt/llm/schemas
cp -r "${REPO_ROOT}/schemas/." /opt/llm/schemas/

# ── ワークフロー定義 ──────────────────────────────────────────────────────────
echo "--- config/workflows/ → ${DEPLOY_CONFIG}/workflows/ ---"
mkdir -p "${DEPLOY_CONFIG}/workflows"
cp -r "${REPO_ROOT}/config/workflows/." "${DEPLOY_CONFIG}/workflows/"

DEPLOYED_SHA256=$(sha256sum "${DEPLOY_CONFIG}/workflows/default.json" | awk '{print $1}')
echo "SHA256 (deployed) : ${DEPLOYED_SHA256}"
if [ "${SOURCE_SHA256}" != "${DEPLOYED_SHA256}" ]; then
  echo "[FATAL] Deployed workflow definition checksum does not match source; deployment corrupted." >&2
  exit 1
fi

# Workflow: mandatory-artifact existence check (deployed copy). Scoped to default.json only.
if [[ ! -f "${DEPLOY_CONFIG}/workflows/default.json" ]]; then
  echo "[FATAL] Deployed workflow definition missing after copy: ${DEPLOY_CONFIG}/workflows/default.json" >&2
  exit 1
fi

# ── テスト ────────────────────────────────────────────────────────────────────
echo "--- tests/ → ${DEPLOY_TESTS}/ ---"
rsync -av --delete \
  --exclude="__pycache__/" \
  --exclude="*.pyc" \
  --exclude="*.pyo" \
  "${REPO_ROOT}/tests/" "${DEPLOY_TESTS}/"

# ── 起動スクリプト ─────────────────────────────────────────────────────────────
echo "--- start_agent.sh → /opt/llm/ ---"
cp "${REPO_ROOT}/deploy/start_agent.sh" "/opt/llm/"
chmod +x /opt/llm/start_agent.sh

echo "=== deploy.sh: 完了 ==="
echo ""
echo "次のステップ:"
echo "  1. bash deploy/build_sqlite_vec.sh  # sqlite-vec 拡張ビルド (初回のみ)"
echo "  2. bash deploy/init_db.sh           # DB スキーマ初期化"
echo "  3. bash deploy/setup_services.sh    # サブプロセス登録・起動"
echo "  4. /opt/llm/start_agent.sh          # AgentREPL 起動"