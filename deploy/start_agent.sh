#!/bin/bash
# start_agent.sh
# AgentREPL を起動する。
# 実行前提: リポジトリのルートディレクトリから実行すること。
#
# 使用例:
#   cd /path/to/repo
#   bash deploy/start_agent.sh

set -euo pipefail

# Production never installs the dev dependency group and never rewrites uv.lock.
UV_PROD_FLAGS=(--frozen --no-dev)

# production: /opt/llm/pyproject.toml が存在すればそちらを優先
if [[ -f "/opt/llm/pyproject.toml" ]]; then
    REPO_ROOT="/opt/llm"
else
    REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fi

echo "=== start_agent.sh: AgentREPL 起動 ==="
echo "リポジトリ: ${REPO_ROOT}"

export PYTHONPATH="${REPO_ROOT}/scripts"

# ── .env ロード + MCP 認証トークンの事前チェック ──────────────────────────────
# 操作者は MCP 認証トークン等（MCP_*_AUTH_TOKEN）を .env に定義できる。
#   production: /opt/llm/.env
#   dev       : <repo>/.env
# 既定の環境変数が優先されます（.env は上書きしない）。.env は安全にパースのみ
# （eval/source せず、コマンド置換も許可しない）。トークンが未設定の場合は、
# 深い traceback ではなく 起動前に必須変数を一覧して失敗する（fail-fast）。

# .env の行を安全にパースし、KEY=VALUE を連想配列に格納する（既存変数を上書きしない）。
parse_env_file() {
    local env_file="$1"
    local key value line
    declare -A _loaded=()
    while IFS= read -r line || [[ -n "${line}" ]]; do
        # コメント行・空行をスキップ
        [[ "${line}" =~ ^[[:space:]]*# ]] && continue
        [[ "${line}" =~ ^[[:space:]]*$ ]] && continue
        # KEY=value のみ許可。キーは [A-Za-z_][A-Za-z0-9_]*
        if [[ "${line}" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
            key="${BASH_REMATCH[1]}"
            value="${BASH_REMATCH[2]}"
            # 前後の空白を削除
            value="${value#"${value%%[![:space:]]*}"}"
            value="${value%"${value##*[![:space:]]}"}"
            # 一重/二重引用符を除去（両端が一致する場合のみ）
            case "${value}" in
                \"*\") value="${value#\"}"; value="${value%\"}" ;;
                \'*\') value="${value#\'}"; value="${value%\'}" ;;
            esac
            # 未設定の変数のみ適用（既定の環境変数が優先）
            if [[ -z "${!key+x}" ]]; then
                _loaded["${key}"]="${value}"
            fi
        else
            echo "[WARN] Skipping unsafe .env line (not KEY=value): ${line}" >&2
        fi
    done < "${env_file}"
    # 取り込んだ変数をエクスポート
    local k
    for k in "${!_loaded[@]}"; do
        export "${k}=${_loaded[$k]}"
    done
}

# 必須環境変数を列出する（起動時に参照される全設定ファイルの ${ENV:VAR} 参照から自動取得）。
collect_required_env_vars() {
    local cfg
    for cfg in "$@"; do
        [[ -f "${cfg}" ]] || continue
        # no-match は exit 1（set -e/pipefail で関数が中断されないよう許容）
        { grep -oE '\$\{ENV:[A-Za-z_][A-Za-z0-9_]*\}' "${cfg}" || true; } \
            | sed -E 's/^\$\{ENV:([^}]*)\}$/\1/'
    done | sort -u
}

ENV_FILE=""
if [[ -f "/opt/llm/.env" ]]; then
    ENV_FILE="/opt/llm/.env"
elif [[ -f "${REPO_ROOT}/.env" ]]; then
    ENV_FILE="${REPO_ROOT}/.env"
fi

if [[ -n "${ENV_FILE}" ]]; then
    # 秘密が含まれる可能性のあるファイルの権限を警告
    env_perms="$(stat -c '%a' "${ENV_FILE}" 2>/dev/null || echo "")"
    if [[ -n "${env_perms}" && "${env_perms}" != "600" && "${env_perms}" != "400" ]]; then
        echo "[WARN] ${ENV_FILE} permissions are ${env_perms}; consider 'chmod 600 ${ENV_FILE}' (contains secrets)." >&2
    fi
    echo "=== start_agent.sh: .env を読み込み中 ==="
    echo "${ENV_FILE}"
    parse_env_file "${ENV_FILE}"
fi

# 必須環境変数がすべて設定されているか確認（未設定・空も対象）。
# 起動時に参照される全設定ファイル（agent + 各 MCP サーバー専用設定）から抽出する。
CONFIG_FILES=()
if [[ -f "/opt/llm/config/agent.toml" ]]; then
    CONFIG_FILES+=("/opt/llm/config/agent.toml")
elif [[ -f "${REPO_ROOT}/config/agent.toml" ]]; then
    CONFIG_FILES+=("${REPO_ROOT}/config/agent.toml")
fi
for cfg_glob in /opt/llm/config/*_mcp_server.toml "${REPO_ROOT}"/config/*_mcp_server.toml; do
    [[ -f "${cfg_glob}" ]] && CONFIG_FILES+=("${cfg_glob}")
done

missing_tokens=()
while IFS= read -r var; do
    [[ -z "${var}" ]] && continue
    if [[ -z "${!var+x}" || -z "${!var}" ]]; then
        missing_tokens+=("${var}")
    fi
done < <(collect_required_env_vars "${CONFIG_FILES[@]}")

if (( ${#missing_tokens[@]} > 0 )); then
    echo ""
    echo "[FATAL] ${#missing_tokens[@]} required MCP auth environment variable(s) not set or empty:" >&2
    printf '  - %s\n' "${missing_tokens[@]}" >&2
    echo "" >&2
    if [[ -n "${ENV_FILE}" ]]; then
        echo "Set them in ${ENV_FILE} (or your shell), e.g.:" >&2
    else
        echo "Create ${REPO_ROOT}/.env with these variables, e.g.:" >&2
    fi
    for var in "${missing_tokens[@]}"; do
        printf '  %s="$(openssl rand -hex 32)"\n' "${var}" >&2
    done
    echo "Then re-run: bash deploy/start_agent.sh" >&2
    exit 1
fi

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

if ! PYTHONPATH="${PYTHONPATH}" UV_SYSTEM_CERTS=true uv run "${UV_PROD_FLAGS[@]}" python -m agent.workflow.validate "${WORKFLOW_JSON}"; then
    echo "[FATAL] Workflow definition validation failed." >&2
    exit 1
fi

# ── リゾルバー入力 (コンパイル済みバイナリ用) ────────────────────────────────────────────────────────────
# 外部 config ディレクトリと Sudachi 辞書を明示指定。缺失時は resolver がパス名を
# 添えて fail-fast する (AC-01, AC-05)。
export LLMAGENT_CONFIG_DIR="${DEPLOY_CONFIG}"
export LLMAGENT_SUDACHI_DICT="/opt/llm/dict/system.dic"

# ── AgentREPL 起動 ────────────────────────────────────────────────────────────
echo ""
echo "=== AgentREPL 起動中 ==="
echo "Ctrl+C で停止"
echo ""

UV_SYSTEM_CERTS=true /opt/llm/bin/agent
