#!/bin/bash
# build_binaries.sh
# エージェント本体と各 MCP サーバー（計11）を Nuitka `--onefile` でビルドして
# ${BIN_DIR} へ配置する。sudachipy のリソースを同梱し、config/・Sudachi 辞書・
# sqlite-vec(vec0.so) は外部配置のままにする。
#
# 実行前提 (build host のみ。/opt/llm へデプロイされない):
#   * Python 3.13 (dev headers: Python.h あり)
#   * patchelf
#   * nuitka (uv run nuitka で利用可能)
#
# 使用例:
#   cd /path/to/repo
#   bash deploy/build_binaries.sh
#   # 低メモリホスト:
#   NUTKA_EXTRA_FLAGS="--onefile-no-compression" bash deploy/build_binaries.sh
#   # 出力先を変更:
#   BIN_DIR=/opt/llm/bin OUTPUT_DIR=/data/nuitka_dist bash deploy/build_binaries.sh

set -euo pipefail

# ── 設定 (環境変数で上書き可能) ───────────────────────────────────────────────
BIN_DIR="${BIN_DIR:-/opt/llm/bin}"
OUTPUT_DIR="${OUTPUT_DIR:-/opt/llm/dist}"

# 既定の Nuitka フラグ (implementation procedure method step 3 に準拠)。
#   --onefile            : 単一バイナリ
#   --no-strip           : デバッグシンタ保留 (問題時のトレース用)
#   --include-package-data=sudachipy : sudachipy/resources/* の同梱 (必須・数KB)
BASE_NUTKA_ARGS=(
    --onefile
    --no-strip
    --include-package-data=sudachipy
)

# ホスト固有のフラグ (空白区切り)。例: --onefile-no-compression (低メモリ用)。
# plan REQ-006 / Phase 0 事実(約3.7GB RAM で既定 zstd 圧縮が失敗) に従い、
# 低メモリホストで --onefile-no-compression を注入して使用する。
NUTKA_EXTRA_FLAGS="${NUTKA_EXTRA_FLAGS:-}"

# 遅延 import (--include-module)。PoC で発見した遅延 import を記載。
# rag_pipeline_server 現行には rag.pipeline の遅延 import は無し (未検証なら追加)。
# 例: LAZY_IMPORTS=("rag.pipeline")
LAZY_IMPORTS=()

# Nuitka コマンド (既定は `uv run nuitka`)。
NUTKA_CMD=("${NUTKA_CMD[@]:-uv}" run nuitka)

# ── エントリポイント表 (モジュールパス : 出力バイナリ名) ──────────────────────
# 計11件 (エージェント1 + MCP サーバー10)。出力名は config/agent.toml の
# [mcp_servers.<key>] セクション名 に準拠 (例: mcp_servers.shell -> mcp_shell)。
ENTRIES=(
    "agent.repl:agent"
    "mcp_servers.shell.shell_server:mcp_shell"
    "mcp_servers.git.git_server:mcp_git"
    "mcp_servers.web_search.web_search_server:mcp_web_search"
    "mcp_servers.file.delete_server:mcp_file_delete"
    "mcp_servers.file.write_server:mcp_file_write"
    "mcp_servers.file.read_server:mcp_file_read"
    "mcp_servers.github.github_server:mcp_github"
    "mcp_servers.cicd.cicd_server:mcp_cicd"
    "mcp_servers.rag_pipeline.rag_pipeline_server:mcp_rag_pipeline"
    "mcp_servers.mdq.mdq_server:mcp_mdq"
)

# ── 事前チェック ──────────────────────────────────────────────────────────────
command -v uv >/dev/null 2>&1 || { echo "[FATAL] uv not found. Install uv first." >&2; exit 1; }
if ! "${NUTKA_CMD[@]}" --version >/dev/null 2>&1; then
    echo "[FATAL] nuitka not available via: ${NUTKA_CMD[*]}" >&2
    exit 1
fi
if ! command -v patchelf >/dev/null 2>&1; then
    echo "[WARN] patchelf not found; nuitka --onefile が失敗する可能性がある。" >&2
fi

mkdir -p "${OUTPUT_DIR}"
# 計画の假设: 出力先は小さい tmpfs にしない。tmpfs 時は警告 (明示的に許容する場合のみ続行)。
FS_TYPE="$(df -T "${OUTPUT_DIR}" 2>/dev/null | awk 'NR==2 {print $2}')"
if [[ "${FS_TYPE}" == *"tmpfs"* && "${ALLOW_TMPFS_OUTPUT:-0}" != "1" ]]; then
    echo "[FATAL] OUTPUT_DIR ${OUTPUT_DIR} is on tmpfs (${FS_TYPE}); a large build can exhaust it." >&2
    echo "       Use a real disk, or set ALLOW_TMPFS_OUTPUT=1 to override." >&2
    exit 1
fi

# ── ビルド関数 ────────────────────────────────────────────────────────────────
total_seconds=0
total_bytes=0

build_one() {
    local module="$1" final_name="$2"
    local intermediate="${module##*.}"
    local out_file="${OUTPUT_DIR}/${intermediate}"

    echo "--- ビルド: ${module} -> ${final_name} ---"

    # 遅延 import 用の --include-module フラグを構築
    local include_args=()
    local mod
    for mod in "${LAZY_IMPORTS[@]+"${LAZY_IMPORTS[@]}"}"; do
        include_args+=(--include-module="${mod}")
    done

    local args=("${BASE_NUTKA_ARGS[@]+"${BASE_NUTKA_ARGS[@]}"}" "${include_args[@]+"${include_args[@]}"}")
    if [[ -n "${NUTKA_EXTRA_FLAGS}" ]]; then
        # shellcheck disable=SC2086  (意図的に単語分割してフラグを渡す)
        args+=(${NUTKA_EXTRA_FLAGS})
    fi
    args+=(--module="${module}" --output-dir="${OUTPUT_DIR}")

    local start=${SECONDS}
    if ! "${NUTKA_CMD[@]}" "${args[@]}"; then
        echo "[FATAL] Nuitka build failed for ${module}" >&2
        exit 1
    fi
    local elapsed=$(( SECONDS - start ))

    # Nuitka (--module) の出力名はモジュール最終コンポーネント。存在確認後に rename。
    if [[ ! -f "${out_file}" ]]; then
        echo "[FATAL] Expected Nuitka output not found: ${out_file}" >&2
        ls -l "${OUTPUT_DIR}" >&2 || true
        exit 1
    fi

    mkdir -p "${BIN_DIR}"
    mv "${out_file}" "${BIN_DIR}/${final_name}"
    chmod 0755 "${BIN_DIR}/${final_name}"

    local size_bytes size_h
    size_bytes="$(du -sb "${BIN_DIR}/${final_name}" | cut -f1)"
    size_h="$(du -h "${BIN_DIR}/${final_name}" | cut -f1)"
    total_bytes=$(( total_bytes + size_bytes ))
    total_seconds=$(( total_seconds + elapsed ))

    printf '  OK  %-22s module=%-45s build=%4ds size=%s\n' \
        "${final_name}" "${module}" "${elapsed}" "${size_h}"
}

# ── メイン ────────────────────────────────────────────────────────────────────
echo "=== build_binaries.sh: Nuitka --onefile ビルド開始 ==="
echo "  BIN_DIR     : ${BIN_DIR}"
echo "  OUTPUT_DIR  : ${OUTPUT_DIR} (${FS_TYPE:-unknown})"
echo "  NUTKA_CMD   : ${NUTKA_CMD[*]}"
[[ -n "${NUTKA_EXTRA_FLAGS}" ]] && echo "  EXTRA FLAGS : ${NUTKA_EXTRA_FLAGS}"
echo "  エントリポイント数: ${#ENTRIES[@]}"
echo ""

for entry in "${ENTRIES[@]}"; do
    module="${entry%%:*}"
    final_name="${entry##*:}"
    build_one "${module}" "${final_name}"
done

echo ""
echo "=== build_binaries.sh: 完了 (${#ENTRIES[@]} 本) ==="
# 総ビルド時間 (秒) と総サイズ (人間が読みやすい形式) を出力。Plan の Execution Status 用に利用。
awk -v secs="${total_seconds}" -v bytes="${total_bytes}" 'BEGIN {
    split("B KiB MiB GiB TiB", u, " ");
    s = bytes; i = 1;
    while (s >= 1024 && i < 5) { s /= 1024; i++; }
    printf "  総ビルド時間 : %d 秒\n", secs;
    printf "  総サイズ     : %.1f %s (%d バイト)\n", s, u[i], bytes;
}'
echo ""
echo "配置先: ${BIN_DIR}/"
ls -l "${BIN_DIR}"
