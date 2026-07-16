#!/bin/bash
# start_agent.sh
# AgentREPL を起動する。
# 実行前提: リポジトリのルートディレクトリから実行すること。
#
# 使用例:
#   cd /path/to/repo
#   bash deploy/start_agent.sh

set -euo pipefail

# production: /opt/llm/pyproject.toml が存在すればそちらを優先
if [[ -f "/opt/llm/pyproject.toml" ]]; then
    REPO_ROOT="/opt/llm"
else
    REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fi

echo "=== start_agent.sh: AgentREPL 起動 ==="
echo "リポジトリ: ${REPO_ROOT}"

export PYTHONPATH="${REPO_ROOT}/scripts"

# ── 依存チェック ──────────────────────────────────────────────────────────────
if ! command -v uv &>/dev/null; then
    echo "[FATAL] uv not found. Install uv first." >&2
    exit 1
fi

if [[ ! -f "${REPO_ROOT}/pyproject.toml" ]]; then
    echo "[FATAL] pyproject.toml not found. Ensure the project is installed via uv." >&2
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

if ! PYTHONPATH="${PYTHONPATH}" UV_NATIVE_TLS=true uv run python -m agent.workflow.validate "${WORKFLOW_JSON}"; then
    echo "[FATAL] Workflow definition validation failed." >&2
    exit 1
fi

# ── AgentREPL 起動 ────────────────────────────────────────────────────────────
echo ""
echo "=== AgentREPL 起動中 ==="
echo "Ctrl+C で停止"
echo ""

PYTHONPATH="${PYTHONPATH}" UV_NATIVE_TLS=true uv run python -m agent.repl
