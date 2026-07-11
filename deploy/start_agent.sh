#!/bin/bash
# start_agent.sh
# AgentREPL を起動する。
# 実行前提: リポジトリのルートディレクトリから実行すること。
#
# 使用例:
#   cd /path/to/repo
#   bash deploy/start_agent.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== start_agent.sh: AgentREPL 起動 ==="
echo "リポジトリ: ${REPO_ROOT}"

# ── 環境変数設定 ──────────────────────────────────────────────────────────────
export PYTHONPATH="${REPO_ROOT}/scripts"

# ── 依存チェック ──────────────────────────────────────────────────────────────
if ! command -v uv &>/dev/null; then
    echo "[FATAL] uv not found. Install uv first." >&2
    exit 1
fi

if [[ ! -d "${REPO_ROOT}/.venv" ]]; then
    echo "[FATAL] .venv not found. Run 'uv sync --dev --system-certs' first." >&2
    exit 1
fi

# ── デプロイ済みファイルの存在確認 ──────────────────────────────────────────────
DEPLOY_SCRIPTS="/opt/llm/scripts"
DEPLOY_CONFIG="/opt/llm/config"
DEPLOY_DB="/opt/llm/db"

if [[ ! -d "${DEPLOY_SCRIPTS}" ]]; then
    echo "[FATAL] Deployed scripts directory not found: ${DEPLOY_SCRIPTS}" >&2
    echo "Run deploy/deploy.sh first." >&2
    exit 1
fi

if [[ ! -f "${DEPLOY_CONFIG}/agent.toml" ]]; then
    echo "[FATAL] Deployed config not found: ${DEPLOY_CONFIG}/agent.toml" >&2
    echo "Run deploy/deploy.sh first." >&2
    exit 1
fi

if [[ ! -f "${DEPLOY_DB}/workflow.sqlite" ]]; then
    echo "[FATAL] Workflow DB not found: ${DEPLOY_DB}/workflow.sqlite" >&2
    echo "Run deploy/init_db.sh first." >&2
    exit 1
fi

# ── ワークフロー定義のバリデーション ──────────────────────────────────────────
WORKFLOW_JSON="${DEPLOY_CONFIG}/workflows/default.json"
if [[ ! -f "${WORKFLOW_JSON}" ]]; then
    echo "[FATAL] Missing required workflow definition: ${WORKFLOW_JSON}" >&2
    exit 1
fi

if ! PYTHONPATH="${DEPLOY_SCRIPTS}" uv run python -m agent.workflow.validate "${WORKFLOW_JSON}"; then
    echo "[FATAL] Workflow definition validation failed." >&2
    exit 1
fi

# ── Event Bus のヘルスチェック ─────────────────────────────────────────────────
EVENTBUS_HEALTH=$(curl -s http://127.0.0.1:8015/health 2>/dev/null || true)
if [[ -z "${EVENTBUS_HEALTH}" ]]; then
    echo "[WARN] Event Bus health check failed at port 8015." >&2
    echo "  Start Event Bus manually: bash deploy/setup_services.sh" >&2
else
    echo "Event Bus health: OK"
fi

# ── LLM サービスのヘルスチェック ──────────────────────────────────────────────
for svc_port in 8001 8003; do
    HEALTH=$(curl -s http://127.0.0.1:${svc_port}/health 2>/dev/null || true)
    if [[ -n "${HEALTH}" ]]; then
        echo "LLM service (port ${svc_port}): OK"
    else
        echo "[WARN] LLM service not ready on port ${svc_port}." >&2
        echo "  Wait for model loading or start manually: bash deploy/setup_services.sh" >&2
    fi
done

# ── AgentREPL 起動 ────────────────────────────────────────────────────────────
echo ""
echo "=== AgentREPL 起動中 ==="
echo "Ctrl+C で停止"
echo ""

PYTHONPATH="${DEPLOY_SCRIPTS}" uv run python -m agent.repl
