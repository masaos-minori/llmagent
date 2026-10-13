#!/bin/bash
# setup_services.sh
# サービスをデプロイし、起動する。
# deploy.sh 実行後に実行すること。
#
# MCP サーバ (ports 8004-8014) はエージェント管理 subprocess として起動。
# LLM サーバ (ports 8080-8081) はリモートサービスです。本スクリプトは起動せず、スクリプト内でヘルス検証します。
#
# 使用例:
#   bash deploy/setup_services.sh

set -euo pipefail

# Production never installs the dev dependency group and never rewrites uv.lock.
UV_PROD_FLAGS=(--frozen --no-dev)

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

if ! PYTHONPATH=/opt/llm/scripts UV_SYSTEM_CERTS=true uv run "${UV_PROD_FLAGS[@]}" python -m agent.workflow.validate "${WORKFLOW_JSON}"; then
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

EXPECTED_SCHEMA_VERSION=$(PYTHONPATH=/opt/llm/scripts UV_SYSTEM_CERTS=true uv run "${UV_PROD_FLAGS[@]}" python -c \
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

# ── LLM サービスのヘルスチェック（リモート）─────────────────────────────────────
# embed-llm / agent-llm はリモートサービス（本リポジトリは起動せず、ヘルスを検証するだけ）。
# config/agent.toml の embed_url / llm_url から base を読み取り、/health が HTTP 200 かを確認する。
echo "--- LLM サービスのヘルスチェック ---"

# 待機上限（REQ-002: 未確定値。運用確認後に固定推奨）。既定値は 30 回 x 5 秒 ~= 150 秒。
# 環境変数で上書き可能（デプロイ時の調整用）。
LLM_HEALTH_RETRIES="${LLM_HEALTH_RETRIES:-30}"
LLM_HEALTH_INTERVAL="${LLM_HEALTH_INTERVAL:-5}"

read_llm_base() {
    # config/agent.toml から指定キー(base URL)を uv run python で読み取る。
    # 既存のスキーマ読み取りパターンと同様。キー欠落・エラー時は空文字を返す。
    PYTHONPATH=/opt/llm/scripts UV_SYSTEM_CERTS=true uv run "${UV_PROD_FLAGS[@]}" python -c \
        "import tomllib,sys
try:
    print(tomllib.load(open(sys.argv[1],'rb')).get('${1}','').rstrip('/'))
except Exception:
    pass" \
        "${REPO_ROOT}/config/agent.toml" || true
}

EMBED_URL=$(read_llm_base embed_url)
LLM_URL=$(read_llm_base llm_url)

if [ -z "${EMBED_URL}" ] || [ -z "${LLM_URL}" ]; then
    echo "[FATAL] LLM base URL(s) not configured in config/agent.toml (embed_url/llm_url)." >&2
    exit 1
fi

HEALTH_URL_EMBED="${EMBED_URL}/health"
HEALTH_URL_LLM="${LLM_URL}/health"

code_embed=""
code_llm=""
ready=0
for (( attempt=1; attempt<=LLM_HEALTH_RETRIES; attempt++ )); do
    code_embed=$(curl -fsS -o /dev/null -w '%{http_code}' --max-time 5 "${HEALTH_URL_EMBED}" 2>/dev/null || true)
    code_llm=$(curl -fsS -o /dev/null -w '%{http_code}' --max-time 5 "${HEALTH_URL_LLM}" 2>/dev/null || true)
    if [ "${code_embed}" = "200" ] && [ "${code_llm}" = "200" ]; then
        ready=1
        break
    fi
    echo "  ...待機 (${attempt}/${LLM_HEALTH_RETRIES}): embed-llm=${code_embed:---}, agent-llm=${code_llm:---}"
    sleep "${LLM_HEALTH_INTERVAL}"
done

if [ "${ready}" -ne 1 ]; then
    echo "[FATAL] LLM services did not become ready within ${LLM_HEALTH_RETRIES} attempts (~$((LLM_HEALTH_RETRIES * LLM_HEALTH_INTERVAL))s)." >&2
    echo "  embed-llm (${HEALTH_URL_EMBED}): last status ${code_embed:-unreachable}" >&2
    echo "  agent-llm (${HEALTH_URL_LLM}): last status ${code_llm:-unreachable}" >&2
    exit 1
fi

echo "OK: remote LLM services healthy (embed-llm=${HEALTH_URL_EMBED}, agent-llm=${HEALTH_URL_LLM})"

# ── Event Bus (port 8015) ──────────────────────────────────────────────────────
echo "--- Event Bus 起動 ---"
PYTHONPATH=/opt/llm/scripts \
    python -m eventbus.app \
    >> /opt/llm/logs/eventbus.log 2>&1 &
echo "  Event Bus PID: $!"
echo "  Health: $(sleep 2 && curl -s http://127.0.0.1:8015/health 2>/dev/null || echo 'まだ起動中')"

# ── ヘルスチェック ────────────────────────────────────────────────────────────
echo "--- ヘルスチェック (モデルロードに数十秒かかる場合があります) ---"
echo "  embed-llm      : ${HEALTH_URL_EMBED} (上記ゲートで確認済み)"
echo "  agent-llm      : ${HEALTH_URL_LLM} (上記ゲートで確認済み)"
echo "  eventbus       (:8015): $(curl -s http://127.0.0.1:8015/health 2>/dev/null || echo 'まだ起動中')"
echo ""
echo "  ※ MCP サーバ (ports 8004-8014) はエージェント起動時に自動起動します"
echo "     llama-agent 起動後に /mcp status で確認してください"

echo ""
echo "=== setup_services.sh: 完了 ==="
echo ""
echo "次のステップ:"
echo "  # LLM サービスのヘルスは本スクリプトで自動確認済み (config/agent.toml の embed_url / llm_url)"
echo "  # llama-agent の起動はモデルロード完了後に行う"
echo ""
echo "  # ドキュメント収集・投入 (uv run を使用)"
echo "  cd /opt/llm"
echo "  cd /opt/llm && UV_SYSTEM_CERTS=true uv run --frozen --no-dev python -m rag.ingestion.crawler"
echo "  cd /opt/llm && UV_SYSTEM_CERTS=true uv run --frozen --no-dev python -m rag.ingestion.chunk_splitter"
echo "  cd /opt/llm && UV_SYSTEM_CERTS=true uv run --frozen --no-dev python -m rag.ingestion.ingester"
