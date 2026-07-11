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

# Workflow: pre-flight definition + schema check (see docs/02_deployment.md §2.3)
echo "--- Pre-flight: workflow definition and schema check ---"

WORKFLOW_JSON="/opt/llm/config/workflows/default.json"
WORKFLOW_DB="/opt/llm/db/workflow.sqlite"

if [ ! -f "${WORKFLOW_JSON}" ]; then
  echo "[FATAL] Missing required workflow definition: ${WORKFLOW_JSON}" >&2
  echo "Run deploy/deploy.sh before deploy/setup_services.sh." >&2
  exit 1
fi

if ! PYTHONPATH=/opt/llm/scripts uv run python -m agent.workflow.validate "${WORKFLOW_JSON}"; then
  echo "[FATAL] Deployed workflow definition failed validation: ${WORKFLOW_JSON}" >&2
  echo "Run the workflow schema initialization step before starting the agent." >&2
  exit 1
fi

if [ ! -f "${WORKFLOW_DB}" ]; then
  echo "[FATAL] Workflow database schema is missing or incomplete." >&2
  echo "Run the workflow schema initialization step before starting the agent." >&2
  exit 1
fi

REQUIRED_WORKFLOW_TABLES="tasks attempts processed_events artifacts approvals"
MISSING_TABLES=""
for t in ${REQUIRED_WORKFLOW_TABLES}; do
  FOUND=$(sqlite3 "${WORKFLOW_DB}" \
    "SELECT name FROM sqlite_master WHERE type='table' AND name='${t}';")
  if [ -z "${FOUND}" ]; then
    MISSING_TABLES="${MISSING_TABLES} ${t}"
  fi
done
if [ -n "${MISSING_TABLES}" ]; then
  echo "[FATAL] Workflow database schema is missing or incomplete." >&2
  echo "Missing table(s):${MISSING_TABLES}" >&2
  echo "Run the workflow schema initialization step before starting the agent." >&2
  exit 1
fi

EXPECTED_SCHEMA_VERSION=$(PYTHONPATH=/opt/llm/scripts uv run python -c \
  "from db.schema_sql import WORKFLOW_SCHEMA_VERSION; print(WORKFLOW_SCHEMA_VERSION)")
ACTUAL_SCHEMA_VERSION=$(sqlite3 "${WORKFLOW_DB}" \
  "SELECT version FROM workflow_schema_version ORDER BY applied_at DESC LIMIT 1;")
echo "Workflow schema version: ${ACTUAL_SCHEMA_VERSION:-<none>} (expected: ${EXPECTED_SCHEMA_VERSION})"
if [ "${ACTUAL_SCHEMA_VERSION}" != "${EXPECTED_SCHEMA_VERSION}" ]; then
  echo "[FATAL] Workflow schema version mismatch: expected ${EXPECTED_SCHEMA_VERSION}, found ${ACTUAL_SCHEMA_VERSION:-<none>}." >&2
  echo "Run deploy/init_db.sh to migrate the workflow schema before starting services." >&2
  exit 1
fi

echo "OK: workflow definition and schema pre-flight checks passed"
echo ""

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

# ── Event Bus (port 8015) ──────────────────────────────────────────────────────
echo "--- Event Bus 起動 ---"
PYTHONPATH=/opt/llm/scripts \
    python -m eventbus.app \
    >> /opt/llm/logs/eventbus.log 2>&1 &
echo "  Event Bus PID: $!"
echo "  Health: $(sleep 2 && curl -s http://127.0.0.1:8015/health 2>/dev/null || echo 'まだ起動中')"

# ── ヘルスチェック ────────────────────────────────────────────────────────────
echo "--- ヘルスチェック (モデルロードに数十秒かかる場合があります) ---"
echo "  embed-llm      (:8003): $(curl -s http://127.0.0.1:8003/health 2>/dev/null || echo 'まだ起動中')"
echo "  agent-llm      (:8001): $(curl -s http://127.0.0.1:8001/health 2>/dev/null || echo 'まだ起動中')"
echo "  eventbus       (:8015): $(curl -s http://127.0.0.1:8015/health 2>/dev/null || echo 'まだ起動中')"
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
echo "  cd /opt/llm && uv run python -m rag.ingestion.crawler"
echo "  cd /opt/llm && uv run python -m rag.ingestion.chunk_splitter"
echo "  cd /opt/llm && uv run python -m rag.ingestion.ingester"
