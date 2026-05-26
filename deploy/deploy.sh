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

# ── Python スクリプト ─────────────────────────────────────────────────────────
echo "--- scripts/*.py → ${DEPLOY_SCRIPTS}/ ---"
cp "${REPO_ROOT}/scripts/create_schema.py"        "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/web_crawler.py"           "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/chunk_splitter.py"        "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/rag_ingester.py"          "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/agent.py"                 "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/web_search_mcp_server.py" "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/file_mcp_models.py"     "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/file_mcp_service.py"    "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/file_mcp_server.py"     "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/github_mcp_models.py"     "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/github_mcp_service.py"    "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/github_mcp_server.py"     "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/mcp_server.py"            "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/config_loader.py"         "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/agent_repl.py"            "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/agent_repl_debug.py"      "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/agent_repl_health.py"     "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/agent_repl_tool_exec.py"  "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/agent_config.py"          "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/agent_commands.py"        "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/agent_cmd_session.py"     "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/agent_cmd_mcp.py"         "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/agent_cmd_config.py"      "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/agent_cmd_context.py"     "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/agent_cmd_rag.py"         "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/agent_cmd_ingest.py"      "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/agent_session.py"         "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/mcp_models.py"            "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/sqlite_helper.py"         "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/db_maintenance.py"        "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/db_store.py"              "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/logger.py"                "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/rag_utils.py"             "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/rag_types.py"             "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/rag_repository.py"        "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/rag_llm.py"               "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/agent_rag.py"             "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/llm_client.py"            "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/tool_executor.py"         "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/history_manager.py"       "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/agent_context.py"         "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/cli_view.py"              "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/pipeline_utils.py"        "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/formatters.py"            "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/mcp_installer.py"         "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/plugin_registry.py"       "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/tool_result_store.py"     "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/file_mcp_common.py"       "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/file_read_mcp_models.py"  "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/file_read_mcp_service.py" "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/file_read_mcp_server.py"  "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/file_write_mcp_models.py" "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/file_write_mcp_service.py" "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/file_write_mcp_server.py" "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/file_delete_mcp_models.py" "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/file_delete_mcp_service.py" "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/file_delete_mcp_server.py" "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/shell_mcp_models.py"      "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/shell_mcp_service.py"     "${DEPLOY_SCRIPTS}/"
cp "${REPO_ROOT}/scripts/shell_mcp_server.py"      "${DEPLOY_SCRIPTS}/"

# ── プラグイン ────────────────────────────────────────────────────────────────
echo "--- plugins/ → /opt/llm/plugins/ ---"
mkdir -p /opt/llm/plugins
# 既存ファイルを上書きしない (プロダクション固有プラグインを保護)
cp -n "${REPO_ROOT}/plugins/"*.py /opt/llm/plugins/ 2>/dev/null || true

# ── 設定ファイル ──────────────────────────────────────────────────────────────
echo "--- config/*.json → ${DEPLOY_CONFIG}/ ---"
cp "${REPO_ROOT}/config/common.json"               "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/agent.json"                "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/rag_pipeline.json"         "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/web_search_mcp_server.json"  "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/file_mcp_server.json"      "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/github_mcp_server.json"      "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/file_read_mcp_server.json"   "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/file_write_mcp_server.json"  "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/file_delete_mcp_server.json" "${DEPLOY_CONFIG}/"
cp "${REPO_ROOT}/config/shell_mcp_server.json"       "${DEPLOY_CONFIG}/"

# ── SQL 参照定義 ──────────────────────────────────────────────────────────────
echo "--- db/rrf.sql → ${DEPLOY_DB}/ ---"
cp "${REPO_ROOT}/db/rrf.sql" "${DEPLOY_DB}/"

echo "=== deploy.sh: 完了 ==="
echo ""
echo "次のステップ:"
echo "  1. bash deploy/init_db.sh      # DB スキーマ初期化"
echo "  2. bash deploy/setup_services.sh  # OpenRC サービス登録・起動"
