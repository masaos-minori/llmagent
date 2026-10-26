#!/bin/bash
# load_env.sh
# .env パースと必須環境変数ゲートを共有する sourcing 専用ライブラリ。
# 単体では実行しない（shell options such as -euo pipefail are set on the sourcing script side）。
#
# 使用例:
#   source "${REPO_ROOT}/deploy/load_env.sh"
#   parse_env_file "${ENV_FILE}"
#   require_env_vars "Event Bus" "bash deploy/setup_services.sh" "${CONFIG_FILES[@]}"
#
# require_env_vars は呼び出し側の ENV_FILE と REPO_ROOT を ${VAR:-} で読む。
# デプロイホスト既定パスは持たない（パスは引数と呼び出し側変数のみ）。

# .env の行を安全にパースし、KEY=VALUE を連想配列に格納する（既存変数を上書きしない）。
parse_env_file() {
    local env_file="$1"
    local key value line
    # 秘密が含まれる可能性のあるファイルの権限を警告
    local env_perms
    env_perms="$(stat -c '%a' "${env_file}" 2>/dev/null || echo "")"
    if [[ -n "${env_perms}" && "${env_perms}" != "600" && "${env_perms}" != "400" ]]; then
        echo "[WARN] ${env_file} permissions are ${env_perms}; consider 'chmod 600 ${env_file}' (contains secrets)." >&2
    fi
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

# 必須環境変数がすべて設定されているか確認（未設定・空も対象）。
# 引数: "<label>" "<再実行コマンド>" <設定ファイル...>
require_env_vars() {
    local label="$1"
    local rerun_command="$2"
    shift 2
    local -a config_files=("$@")
    local -a missing=()
    local var

    while IFS= read -r var; do
        [[ -z "${var}" ]] && continue
        if [[ -z "${!var+x}" || -z "${!var}" ]]; then
            missing+=("${var}")
        fi
    done < <(collect_required_env_vars "${config_files[@]}")

    if (( ${#missing[@]} > 0 )); then
        local env_file_hint="${ENV_FILE:-}"
        local repo_root_hint="${REPO_ROOT:-}"
        echo "" >&2
        echo "[FATAL] ${#missing[@]} required ${label} environment variable(s) not set or empty:" >&2
        printf '  - %s\n' "${missing[@]}" >&2
        echo "" >&2
        if [[ -n "${env_file_hint}" ]]; then
            echo "Set them in ${env_file_hint} (or your shell), e.g.:" >&2
        elif [[ -n "${repo_root_hint}" ]]; then
            echo "Create ${repo_root_hint}/.env with these variables, e.g.:" >&2
        else
            echo "Set them in your environment or a .env file, e.g.:" >&2
        fi
        for var in "${missing[@]}"; do
            # Single quotes are intentional: the example command is printed, not expanded.
            # shellcheck disable=SC2016
            printf '  %s="$(openssl rand -hex 32)"\n' "${var}" >&2
        done
        echo "Then re-run: ${rerun_command}" >&2
        exit 1
    fi
}

# preflight_eventbus_tokens は require_env_vars の後に呼ぶ設定レベルのゲート。
# app.py の lifespan と同じ順序 (load_config → _populate_token_maps) で
# トークンマップを構築し、設定の各トークンがマップに一致するかを指紋で検証する。
# 呼び出し側の EVENTBUS_CONFIG_PATH / DEPLOY_SCRIPTS / UV_PROD_FLAGS を読む
# (require_env_vars が ENV_FILE / REPO_ROOT を読むのと同じ規約)。
preflight_eventbus_tokens() {
    local py_output
    if ! py_output="$(PYTHONPATH="${DEPLOY_SCRIPTS}" UV_SYSTEM_CERTS=true \
        EVENTBUS_CONFIG_PATH="${EVENTBUS_CONFIG_PATH}" \
        uv run "${UV_PROD_FLAGS[@]}" python - <<'PYEOF' 2>&1
from eventbus import auth
from eventbus.config import get_config_path, load_config

config = load_config(get_config_path())
auth._populate_token_maps(config)
principal_map = auth._TOKEN_PRINCIPAL_MAP
for field in (
    "auth_token",
    "admin_token",
    "monitoring_token",
    "operator_token",
    "publisher_token",
    "consumer_token",
):
    token = getattr(config, field, "")
    if not token:
        continue
    principal = principal_map.get(token)
    if principal is None:
        raise SystemExit(f"token for config field '{field}' is absent from the token map")
    if principal.token_fingerprint != auth._derive_token_fingerprint(token):
        raise SystemExit(f"token fingerprint mismatch for config field '{field}'")
PYEOF
    )"; then
        echo "[FATAL] Event Bus token-map preflight failed (config: ${EVENTBUS_CONFIG_PATH}):" >&2
        echo "${py_output}" >&2
        echo "Fix the EventBus config and re-run: bash deploy/setup_services.sh" >&2
        exit 1
    fi
}
