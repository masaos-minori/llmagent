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

# Sandbox overrides: defaults preserve the production /opt/llm paths.
# tests/deploy/test_setup_services_eventbus.py uses these to run the shipped
# script against throwaway state (mirrors deploy/init_db.sh DEPLOY_* pattern).
DEPLOY_SCRIPTS="${DEPLOY_SCRIPTS:-/opt/llm/scripts}"
DEPLOY_DB="${DEPLOY_DB:-/opt/llm/db}"
DEPLOY_LOGS="${DEPLOY_LOGS:-/opt/llm/logs}"

# .env パースと必須環境変数ゲートの共有ライブラリ（sourcing 専用。set オプションは本スクリプトの責任）
# The library is shellchecked as its own file; the job does not pass -x, so it is not followed here.
# shellcheck disable=SC1091
source "${REPO_ROOT}/deploy/load_env.sh"

# Workflow: pre-flight definition + schema check (see docs/02_deployment.md §2.3)
echo "--- Pre-flight: workflow definition and schema check ---"

WORKFLOW_JSON="${WORKFLOW_JSON:-/opt/llm/config/workflows/default.json}"
WORKFLOW_DB="${DEPLOY_DB}/workflow.sqlite"

if [ ! -f "${WORKFLOW_JSON}" ]; then
  echo "[FATAL] Missing required workflow definition: ${WORKFLOW_JSON}" >&2
  echo "Run deploy/deploy.sh before deploy/setup_services.sh." >&2
  exit 1
fi

if ! PYTHONPATH="${DEPLOY_SCRIPTS}" UV_SYSTEM_CERTS=true uv run "${UV_PROD_FLAGS[@]}" python -m agent.workflow.validate "${WORKFLOW_JSON}"; then
  echo "[FATAL] Deployed workflow definition failed validation: ${WORKFLOW_JSON}" >&2
  echo "Run the workflow schema initialization step before starting the agent." >&2
  exit 1
fi

if [ ! -f "${WORKFLOW_DB}" ]; then
  echo "[FATAL] Workflow database schema is missing or incomplete." >&2
  echo "Run the workflow schema initialization step before starting the agent." >&2
  exit 1
fi

REQUIRED_WORKFLOW_TABLES="tasks attempts processed_events artifacts"
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

EXPECTED_SCHEMA_VERSION=$(PYTHONPATH="${DEPLOY_SCRIPTS}" UV_SYSTEM_CERTS=true uv run "${UV_PROD_FLAGS[@]}" python -c \
  "from db.schema_sql import WORKFLOW_SCHEMA_VERSION; print(WORKFLOW_SCHEMA_VERSION)")
ACTUAL_SCHEMA_VERSION=$(sqlite3 "${WORKFLOW_DB}" \
  "SELECT version FROM workflow_schema_version ORDER BY applied_at DESC LIMIT 1;")
echo "Workflow schema version: ${ACTUAL_SCHEMA_VERSION:-<none>} (expected: ${EXPECTED_SCHEMA_VERSION})"
if [ "${ACTUAL_SCHEMA_VERSION}" != "${EXPECTED_SCHEMA_VERSION}" ]; then
  echo "[FATAL] Workflow schema version mismatch: expected ${EXPECTED_SCHEMA_VERSION}, found ${ACTUAL_SCHEMA_VERSION:-<none>}." >&2
  echo "Recreate the workflow database (archive the file, then run deploy/init_db.sh) before starting services." >&2
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
# agent-llm は必須（未達で abort）。embed-llm は任意（既定は警告のみ）。
# LLM_GATE_STRICT=1 で embed-llm も必須にする（どちらか未達で abort）。
LLM_GATE_STRICT="${LLM_GATE_STRICT:-0}"

read_llm_base() {
    # config/agent.toml から指定キー(base URL)を uv run python で読み取る。
    # 既存のスキーマ読み取りパターンと同様。キー欠落・エラー時は空文字を返す。
    PYTHONPATH="${DEPLOY_SCRIPTS}" UV_SYSTEM_CERTS=true uv run "${UV_PROD_FLAGS[@]}" python -c \
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

gate_fail() {
    echo "[FATAL] LLM services did not become ready within ${LLM_HEALTH_RETRIES} attempts (~$((LLM_HEALTH_RETRIES * LLM_HEALTH_INTERVAL))s)." >&2
    echo "  embed-llm (${HEALTH_URL_EMBED}): last status ${code_embed:-unreachable}" >&2
    echo "  agent-llm (${HEALTH_URL_LLM}): last status ${code_llm:-unreachable}" >&2
    exit 1
}

code_embed=""
code_llm=""
embed_ok=0
llm_ok=0
for (( attempt=1; attempt<=LLM_HEALTH_RETRIES; attempt++ )); do
    code_embed=$(curl -fsS -o /dev/null -w '%{http_code}' --max-time 5 "${HEALTH_URL_EMBED}" 2>/dev/null || true)
    code_llm=$(curl -fsS -o /dev/null -w '%{http_code}' --max-time 5 "${HEALTH_URL_LLM}" 2>/dev/null || true)
    embed_ok=0
    llm_ok=0
    if [ "${code_embed}" = "200" ]; then embed_ok=1; fi
    if [ "${code_llm}" = "200" ]; then llm_ok=1; fi
    if [ "${embed_ok}" -eq 1 ] && [ "${llm_ok}" -eq 1 ]; then
        break
    fi
    echo "  ...待機 (${attempt}/${LLM_HEALTH_RETRIES}): embed-llm=${code_embed:---}, agent-llm=${code_llm:---}"
    sleep "${LLM_HEALTH_INTERVAL}"
done

if [ "${llm_ok}" -ne 1 ]; then
    gate_fail
fi

LLM_STATE="healthy"
EMBED_STATE="healthy"
if [ "${embed_ok}" -ne 1 ]; then
    if [ "${LLM_GATE_STRICT}" = "1" ]; then
        gate_fail
    fi
    EMBED_STATE="UNREACHABLE (last status ${code_embed:-unreachable}) - degraded, non-fatal"
    echo "[WARN] embed-llm unreachable at ${HEALTH_URL_EMBED} (last status ${code_embed:-unreachable}); continuing. Embedding-dependent features are degraded." >&2
else
    echo "OK: remote LLM services healthy (embed-llm=${HEALTH_URL_EMBED}, agent-llm=${HEALTH_URL_LLM})"
fi

# ── Event Bus (port 8015) ──────────────────────────────────────────────────────
echo "--- Event Bus 起動 ---"

ENV_FILE=""
if [[ -f "/opt/llm/.env" ]]; then
    ENV_FILE="/opt/llm/.env"
elif [[ -f "${REPO_ROOT}/.env" ]]; then
    ENV_FILE="${REPO_ROOT}/.env"
fi
if [[ -n "${ENV_FILE}" ]]; then
    parse_env_file "${ENV_FILE}"
fi

# EVENTBUS_CONFIG_PATH is env-overridable and is exported to the app process,
# so the app actually reads the config file this script validated.
if [[ -z "${EVENTBUS_CONFIG_PATH:-}" ]]; then
    if [[ -f "/opt/llm/config/eventbus.toml" ]]; then
        EVENTBUS_CONFIG_PATH="/opt/llm/config/eventbus.toml"
    elif [[ -f "${REPO_ROOT}/config/eventbus.toml" ]]; then
        EVENTBUS_CONFIG_PATH="${REPO_ROOT}/config/eventbus.toml"
    fi
fi
require_env_vars "Event Bus" "bash deploy/setup_services.sh" "${EVENTBUS_CONFIG_PATH}"

# Deeper config-level gate (REQ-005): build token maps the same way the app's
# lifespan does and abort before launching if the config cannot produce them.
preflight_eventbus_tokens

EB_AUTH_HEADER="Authorization: Bearer ${EVENTBUS_AUTH_TOKEN:-}"

EVENTBUS_HEALTH_URL="${EVENTBUS_HEALTH_URL:-http://127.0.0.1:8015/health}"

PYTHONPATH="${DEPLOY_SCRIPTS}" UV_SYSTEM_CERTS=true EVENTBUS_CONFIG_PATH="${EVENTBUS_CONFIG_PATH}" \
    uv run "${UV_PROD_FLAGS[@]}" python -m eventbus.app \
    >> "${DEPLOY_LOGS}/eventbus.log" 2>&1 &
EB_PID=$!
echo "  Event Bus PID: ${EB_PID}"

# --- EventBus readiness gate (REQ-004) -------------------------------------
# Ready only when the /health body reports db == ok AND dlq_task == running.
# A 503 carrying only capacity-only degraded_reasons (lock_wait_high,
# slow_consumers_detected, query_duration_high, broker_queue_backlog_high,
# subscribers_at_capacity) still satisfies the predicate and does NOT fail
# the gate (contract: scripts/eventbus/health_route.py).
EB_READY=0
EB_LAST_CODE=""
EB_LAST_BODY=""

eb_gate_fail() {
    echo "[FATAL] Event Bus did not become ready within ${LLM_HEALTH_RETRIES} attempts (~$((LLM_HEALTH_RETRIES * LLM_HEALTH_INTERVAL))s)." >&2
    echo "  Event Bus (${EVENTBUS_HEALTH_URL}): last status ${EB_LAST_CODE:-unreachable} ${EB_LAST_BODY:-<none>}" >&2
    kill "${EB_PID}" 2>/dev/null || true
    wait "${EB_PID}" 2>/dev/null || true
    exit 1
}

EB_BODY_FILE="$(mktemp)"
for (( eb_attempt=1; eb_attempt<=LLM_HEALTH_RETRIES; eb_attempt++ )); do
    if ! kill -0 "${EB_PID}" 2>/dev/null; then
        echo "  [FATAL] Event Bus process exited during startup (see ${DEPLOY_LOGS}/eventbus.log)." >&2
        rm -f "${EB_BODY_FILE}"
        eb_gate_fail
    fi
    # No -f/--fail: a 503 body is required to tell capacity-only degradation
    # apart from db_unavailable / dlq_task_stopped. Connection failure yields
    # the write-out code 000 (the only retried branch).
    EB_LAST_CODE=$(curl -sS -o "${EB_BODY_FILE}" -w '%{http_code}' --max-time 5 -H "${EB_AUTH_HEADER}" "${EVENTBUS_HEALTH_URL}" 2>/dev/null || true)
    EB_LAST_BODY="$(tr -d '\n ' < "${EB_BODY_FILE}")"
    if [ -z "${EB_LAST_CODE}" ] || [ "${EB_LAST_CODE}" = "000" ]; then
        echo "  ...起動中 (${eb_attempt}/${LLM_HEALTH_RETRIES}): eventbus=${EB_LAST_CODE:-unreachable}"
        sleep "${LLM_HEALTH_INTERVAL}"
        continue
    fi
    if [[ "${EB_LAST_BODY}" == *'"db":"ok"'* && "${EB_LAST_BODY}" == *'"dlq_task":"running"'* ]]; then
        EB_READY=1
        break
    fi
    echo "  Event Bus /health returned HTTP ${EB_LAST_CODE} without the readiness predicate (db=ok, dlq_task=running)." >&2
    rm -f "${EB_BODY_FILE}"
    eb_gate_fail
done
rm -f "${EB_BODY_FILE}"
if [ "${EB_READY}" -ne 1 ]; then
    eb_gate_fail
fi
echo "  Health: ${EB_LAST_BODY}"

# ── ヘルスチェック ────────────────────────────────────────────────────────────
echo "--- ヘルスチェック (モデルロードに数十秒かかる場合があります) ---"
echo "  embed-llm      : ${HEALTH_URL_EMBED} (${EMBED_STATE})"
echo "  agent-llm      : ${HEALTH_URL_LLM} (${LLM_STATE})"
echo "  eventbus       (:8015): $(curl -s -H "${EB_AUTH_HEADER}" "${EVENTBUS_HEALTH_URL}" 2>/dev/null || echo 'まだ起動中')"
echo ""
echo "  ※ MCP サーバ (ports 8004-8014) はエージェント起動時に自動起動します"
echo "     llama-agent 起動後に /mcp status で確認してください"

echo ""
echo "--- サービス状況サマリ ---"
echo "  Event Bus (:8015, PID ${EB_PID}): READY (db ok, dlq_task running)"
echo "  agent-llm (${HEALTH_URL_LLM}): ${LLM_STATE}"
echo "  embed-llm (${HEALTH_URL_EMBED}): ${EMBED_STATE}"

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
