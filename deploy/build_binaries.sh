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
#   # LTO を有効化 (既定は無効。ビルド時間・メモリが増える):
#   NUTKA_LTO=yes bash deploy/build_binaries.sh
#   # デバッグ用 (strip しない。サイズは増える):
#   NUTKA_UNSTRIPPED=1 bash deploy/build_binaries.sh
#   # 出力先を変更:
#   BIN_DIR=/opt/llm/bin OUTPUT_DIR=/data/nuitka_dist bash deploy/build_binaries.sh
#   # 一部のバイナリのみ再ビルド (空白区切りの出力名):
#   BUILD_ONLY="agent" bash deploy/build_binaries.sh
#   # 直前の swap 前のバイナリ一式へ戻す (Nuitka 不要。${BIN_DIR}.prev から復元):
#   bash deploy/build_binaries.sh --rollback
#
# ビルドは ${OUTPUT_DIR}/stage に出力し、要求した全バイナリが成功した後にだけ
# tools/manage_binaries.py swap で ${BIN_DIR} へ入れ替える。各バイナリの横に
# <name>.build-info.json (ビルド元 commit・checksum) を記録し、入れ替え前の一式は
# ${BIN_DIR}.prev に残す。
#
# nuitka4.x に関する注記:
#   --onefile（スタンドアロン実行可能）と --module（インポート用拡張モジュール）は
#   x4 で両立できない。そのため各エントリの __main__ を再現するランチャ (.py) を
#   生成し、それを --onefile の対象（位置引数）としてコンパイルする。

set -euo pipefail

# ── 設定 (環境変数で上書き可能) ───────────────────────────────────────────────
BIN_DIR="${BIN_DIR:-/opt/llm/bin}"
OUTPUT_DIR="${OUTPUT_DIR:-/opt/llm/dist}"

# プロジェクトの `agent` / `mcp_servers` は installed package ではない
# (scripts/ に __init__.py が無い)。tests/conftest.py が sys.path に挿入するのと同様、
# nuitka が対象モジュールを解析できるように PYTHONPATH に scripts/ を追加する。
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${REPO_ROOT}/scripts${PYTHONPATH:+:${PYTHONPATH}}"

# 直前のバイナリ一式へ戻す。Nuitka や uv の事前チェックより前に処理する。
if [[ "${1:-}" == "--rollback" ]]; then
    exec python3 "${REPO_ROOT}/tools/manage_binaries.py" rollback --bin-dir "${BIN_DIR}"
fi

# 既定の Nuitka フラグ (サイズ最小化重視)。
#   --onefile            : 単一バイナリ (payload は既定で圧縮される。--onefile-no-compression は使わない)
#   --include-package-data=sudachipy : sudachipy/resources/* の同梱 (必須・数KB)
#   --lto                : 既定 no (NUTKA_LTO=yes で有効化)。計測 (agent, 非圧縮同条件) で
#                          サイズ差は約 0.5% に留まり時間短縮も確認できなかったため。
#   --python-flag=no_docstrings : docstring を除去。実行時の __doc__ 依存は scripts/ の
#                          ビルド対象経路に無い (argparse description の 2 箇所は非ビルド対象)。
#                          -O (no_asserts) は assert の実行時ガード用途を壊しうるため使わない。
#   --noinclude-*-mode=nofollow : 取り込むと巨大化する開発用パッケージの追跡を抑止
#   --nofollow-import-to : テスト/GUI 等、実行に不要なモジュールの追跡を抑止
#   --remove-output      : ビルド中間物 (*.build, *.onefile-build) を削除しディスクを節約
# strip は nuitka の既定 (有効) に任せる。--unstripped はトレース用に NUTKA_UNSTRIPPED=1 で有効化。
BASE_NUTKA_ARGS=(
    --onefile
    --include-package-data=sudachipy
    --lto="${NUTKA_LTO:-no}"
    --python-flag=no_docstrings
    --noinclude-unittest-mode=nofollow
    --noinclude-pytest-mode=nofollow
    --noinclude-setuptools-mode=nofollow
    --noinclude-pydoc-mode=nofollow
    --noinclude-IPython-mode=nofollow
    --noinclude-dask-mode=nofollow
    --noinclude-numba-mode=nofollow
    --nofollow-import-to=tkinter
    --nofollow-import-to=doctest
    --nofollow-import-to=*.tests
    --nofollow-import-to=*.test
    --remove-output
)
if [[ "${NUTKA_UNSTRIPPED:-0}" == "1" ]]; then
    BASE_NUTKA_ARGS+=(--unstripped)
fi

# C コンパイラの同時実行数 (--jobs)。既定は CPU スレッド数の半分 (最小 1)。
# 全 CPU を使うと LTO リンク時にメモリ不足になりやすいため。NUTKA_JOBS で上書き可能。
_cpu_threads="$(nproc 2>/dev/null || echo 2)"
NUTKA_JOBS="${NUTKA_JOBS:-$(( _cpu_threads / 2 > 0 ? _cpu_threads / 2 : 1 ))}"
BASE_NUTKA_ARGS+=(--jobs="${NUTKA_JOBS}")

# ホスト固有のフラグ (空白区切り)。BASE の後に追加され、同一オプションは後勝ち。例: --lto=no (低メモリ用)。
NUTKA_EXTRA_FLAGS="${NUTKA_EXTRA_FLAGS:-}"

# 空白区切りの出力バイナリ名 (例: "agent mcp_shell") のみビルドする。空なら全件。
BUILD_ONLY="${BUILD_ONLY:-}"

# 遅延 import (--include-module)。PoC で発見した遅延 import を記載。
# rag_pipeline_server 現行には rag.pipeline の遅延 import は無し (未検証なら追加)。
# 例: LAZY_IMPORTS=("rag.pipeline")
LAZY_IMPORTS=()

# Nuitka コマンド (既定は `uv run nuitka`)。
# nuitka は pyproject の依存ではないことが多いため、既定が解決できなければ
# `uv run --with nuitka` で都度解決する。バージョンは再現のため固定デフォルト。
NUTKA_VERSION="${NUTKA_VERSION:-4.2.2}"
NUTKA_PRIMARY_CMD=( "${NUTKA_CMD[@]:-uv}" run nuitka )
# [onefile] extra は zstandard を含む。無いと onefile payload が非圧縮になり約2倍のサイズになる。
NUTKA_FALLBACK_CMD=( uv run --with "nuitka[onefile]==${NUTKA_VERSION}" nuitka )
# dev 依存 (mypy 等) を build 環境に入れない。Nuitka が辿るファイルが約4割減り時間が半減する。
export UV_NO_DEV="${UV_NO_DEV:-1}"

# uv は既定で内蔵の証明書バンドルを使うため、システムの証明書ストアにしか証明書がない
# 環境では PyPI から nuitka を取得できず UnknownIssuer で失敗する。他の deploy スクリプト
# と同様に既定でシステムの証明書ストアを使う (UV_SYSTEM_CERTS=false で無効化できる)。
export UV_SYSTEM_CERTS="${UV_SYSTEM_CERTS:-true}"

# ── エントリ表 (モジュールパス : 出力バイナリ名 : サーバークラス) ──────────────
# 計11件 (エージェント1 + MCP サーバー10)。出力名は config/agent.toml の
# [mcp_servers.<key>] セクション名 に準拠 (例: mcp_servers.shell -> mcp_shell)。
# クラス名が空のエントリは agent.repl のように main() を呼ぶ種別。
ENTRIES=(
    "agent.repl:agent:"
    "mcp_servers.shell.shell_server:mcp_shell:ShellMCPServer"
    "mcp_servers.git.git_server:mcp_git:GitMCPServer"
    "mcp_servers.web_search.web_search_server:mcp_web_search:WebSearchMCPServer"
    "mcp_servers.file.delete_server:mcp_file_delete:FileDeleteMCPServer"
    "mcp_servers.file.write_server:mcp_file_write:FileWriteMCPServer"
    "mcp_servers.file.read_server:mcp_file_read:FileReadMCPServer"
    "mcp_servers.github.github_server:mcp_github:GithubMCPServer"
    "mcp_servers.cicd.cicd_server:mcp_cicd:CiCdMCPServer"
    "mcp_servers.rag_pipeline.rag_pipeline_server:mcp_rag_pipeline:RagPipelineMCPServer"
    "mcp_servers.mdq.mdq_server:mcp_mdq:MdqMCPServer"
)

# ── 事前チェック ──────────────────────────────────────────────────────────────
command -v uv >/dev/null 2>&1 || { echo "[FATAL] uv not found. Install uv first." >&2; exit 1; }

# Nuitka は Python.h (開発ヘッダ) を持つ Python を要求する。uv が選ぶ Python がシステムの
# python3.13 でヘッダ無し (libpython3.13-dev 未導入) の場合、nuitka は exit 1 で終了し、
# 後段で「nuitka not available」と誤認される。uv 管理の Python (ヘッダ同梱) へ切り替える。
# UV_PYTHON 明示時はそれを尊重する。切替時は .venv を再作成させないため
# UV_PROJECT_ENVIRONMENT もビルド専用 venv に向ける (明示済みならそれを尊重)。
_py_has_headers() {
    "$1" -c 'import os, sys, sysconfig; sys.exit(0 if os.path.exists(os.path.join(sysconfig.get_paths()["include"], "Python.h")) else 1)' 2>/dev/null
}
if [[ -z "${UV_PYTHON:-}" ]]; then
    _default_py="$(uv python find 2>/dev/null || true)"
    if [[ -n "${_default_py}" ]] && ! _py_has_headers "${_default_py}"; then
        for _cand in "$(uv python dir 2>/dev/null)"/cpython-3.1[3-9]*/bin/python3.*; do
            if [[ -x "${_cand}" ]] && _py_has_headers "${_cand}"; then
                export UV_PYTHON="${_cand}"
                export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-${XDG_CACHE_HOME:-${HOME}/.cache}/llmagent-build-venv}"
                echo "[INFO] ${_default_py} has no Python.h; using uv-managed ${UV_PYTHON} (venv: ${UV_PROJECT_ENVIRONMENT})." >&2
                break
            fi
        done
        if [[ -z "${UV_PYTHON:-}" ]]; then
            echo "[WARN] ${_default_py} has no Python.h and no uv-managed Python with headers was found." >&2
            echo "       Install libpython3.13-dev, or run 'uv python install 3.13'." >&2
        fi
    fi
fi

# nuitka の実コマンドを解決する。既定 (NUTKA_PRIMARY_CMD) が解決できなければ
# `uv run --with nuitka` で都度解決する (nuitka が pyproject 依存ではないため)。
if "${NUTKA_PRIMARY_CMD[@]}" --version >/dev/null 2>&1; then
    NUTKA_CMD=( "${NUTKA_PRIMARY_CMD[@]}" )
elif "${NUTKA_FALLBACK_CMD[@]}" --version >/dev/null 2>&1; then
    NUTKA_CMD=( "${NUTKA_FALLBACK_CMD[@]}" )
else
    echo "[INFO] fallback nuitka output (cause of failure):" >&2
    "${NUTKA_FALLBACK_CMD[@]}" --version 2>&1 | head -5 >&2 || true
    echo "[FATAL] nuitka not available (tried: '${NUTKA_PRIMARY_CMD[*]}' and '${NUTKA_FALLBACK_CMD[*]}')." >&2
    exit 1
fi
# patchelf の事前チェック。nuitka 4.x は既知のバグ版 (0.18.x) をコンパイル時に拒否する
# (実行段階ではなく、C ビルド後に FATAL で止まる)。検出を早期化し明確なエラーにする。
if command -v patchelf >/dev/null 2>&1; then
    _pe_ver="$(patchelf --version 2>/dev/null | awk '{print $2}')"
    if [[ -n "${_pe_ver}" ]]; then
        _pe_major="${_pe_ver%%.*}"
        _pe_minor="${_pe_ver#*.}"; _pe_minor="${_pe_minor%%.*}"
        [[ "${_pe_major}" =~ ^[0-9]+$ ]] || _pe_major=0
        [[ "${_pe_minor}" =~ ^[0-9]+$ ]] || _pe_minor=0
        if (( _pe_major * 100 + _pe_minor < 19 )); then
            echo "[FATAL] patchelf ${_pe_ver} is too old; nuitka 4.x rejects patchelf < 0.19." >&2
            echo "       Upgrade patchelf to >= 0.19 (e.g. 'pip install --user patchelf'). or set PATH ahead of it." >&2
            exit 1
        fi
    else
        echo "[WARN] patchelf --version returned nothing; assuming compatible." >&2
    fi
else
    echo "[WARN] patchelf not found; nuitka --onefile が失敗する可能性がある。" >&2
fi
# ccache: nuitka の Scons は ccache を使う。CCACHE_DIR が読み取り専用だと
# "ccache: error: Permission denied" で C ビルドが中断する。書けない場合のみ無効化。
# ディレクトリ未作成は「書けない」ではない (初回は ccache が作る) ため、先に作成を試みる。
if [[ -z "${CCACHE_DISABLE:-}" ]] && command -v ccache >/dev/null 2>&1; then
    _cc_dir="${CCACHE_DIR:-${XDG_CACHE_HOME:-${HOME}/.cache}/ccache}"
    mkdir -p "${_cc_dir}" 2>/dev/null || true
    if [[ ! -w "${_cc_dir}" ]]; then
        echo "[WARN] ccache dir '${_cc_dir}' is not writable; setting CCACHE_DISABLE=1." >&2
        export CCACHE_DISABLE=1
    fi
fi

mkdir -p "${OUTPUT_DIR}"
# 計画の假设: 出力先は小さい tmpfs にしない。tmpfs 時は警告 (明示的に許容する場合のみ続行)。
FS_TYPE="$(df -T "${OUTPUT_DIR}" 2>/dev/null | awk 'NR==2 {print $2}')"
if [[ "${FS_TYPE}" == *"tmpfs"* && "${ALLOW_TMPFS_OUTPUT:-0}" != "1" ]]; then
    echo "[FATAL] OUTPUT_DIR ${OUTPUT_DIR} is on tmpfs (${FS_TYPE}); a large build can exhaust it." >&2
    echo "       Use a real disk, or set ALLOW_TMPFS_OUTPUT=1 to override." >&2
    exit 1
fi

# 生成するランチャを置く一時ディレクトリ（ビルド後に削除）。
LAUNCHER_DIR="${OUTPUT_DIR}/.launchers"
# ビルド済みバイナリの一時置き場。全件成功後に swap で BIN_DIR へ入れ替える。
STAGE_DIR="${OUTPUT_DIR}/stage"
mkdir -p "${STAGE_DIR}"
find "${STAGE_DIR}" -mindepth 1 -delete
BUILT_NAMES=()
mkdir -p "${LAUNCHER_DIR}"
cleanup_launchers() { rm -rf "${LAUNCHER_DIR}"; }
trap cleanup_launchers EXIT

# ── ランチャ生成 ──────────────────────────────────────────────────────────────
# {final_name}.py を生成し、そのエントリの __main__ で行っていた処理を再現する。
# nuitka4x では --module モードと --onefile は競合するため、ランチャを位置引数で
# コンパイルしてスタンドアロン実行可能を生産する。
gen_launcher() {
    local module="$1" final_name="$2" cls="$3"
    local dest="${LAUNCHER_DIR}/${final_name}_launcher.py"

    if [[ -z "${cls}" ]]; then
        # agent.repl など main() を呼ぶ種別
        cat > "${dest}" <<EOF
# Auto-generated by build_binaries.sh (nuitka4.x launcher for ${module})
from ${module} import main

if __name__ == "__main__":
    main()
EOF
    else
        # MCP サーバー。インスタンス化して run_http() を呼ぶ。
        cat > "${dest}" <<EOF
# Auto-generated by build_binaries.sh (nuitka4.x launcher for ${module})
from ${module} import ${cls}

if __name__ == "__main__":
    ${cls}().run_http()
EOF
    fi
}

# ── ビルド関数 ────────────────────────────────────────────────────────────────
total_seconds=0
total_bytes=0

build_one() {
    local module="$1" final_name="$2" cls="$3"
    # The launcher is compiled as a top-level module named after its file, so its
    # name must not equal a scripts/ package (e.g. "agent"), or `import agent.repl`
    # resolves to the launcher itself ("'agent' is not a package").
    local launcher="${LAUNCHER_DIR}/${final_name}_launcher.py"

    echo "--- ビルド: ${module} -> ${final_name} ---"
    gen_launcher "${module}" "${final_name}" "${cls}"

    # 遅延 import 用の --include-module フラグを構築
    local include_args=()
    local mod
    for mod in "${LAZY_IMPORTS[@]+"${LAZY_IMPORTS[@]}"}"; do
        include_args+=(--include-module="${mod}")
    done

    local args=("${BASE_NUTKA_ARGS[@]+"${BASE_NUTKA_ARGS[@]}"}" "${include_args[@]+"${include_args[@]}"}")
    if [[ -n "${NUTKA_EXTRA_FLAGS}" ]]; then
        # 意図的に単語分割してフラグを渡す
        # shellcheck disable=SC2206
        args+=(${NUTKA_EXTRA_FLAGS})
    fi
    # nuitka4x: --onefile 実行可能はランチャ(.py)を位置引数として対象に。--module は不要。
    args+=(--output-dir="${OUTPUT_DIR}" "${launcher}")

    local start=${SECONDS}
    if ! "${NUTKA_CMD[@]}" "${args[@]}"; then
        echo "[FATAL] Nuitka build failed for ${module}" >&2
        exit 1
    fi
    local elapsed=$(( SECONDS - start ))

    # onefile 出力は nuitka が <final_name>.bin として生成（--onefile の既定名）。
    # 念のため拡張子なし / .so にも対応。
    local produced=""
    local cand
    for cand in "${OUTPUT_DIR}/${final_name}_launcher.bin" "${OUTPUT_DIR}/${final_name}_launcher" "${OUTPUT_DIR}/${final_name}.bin" "${OUTPUT_DIR}/${final_name}" "${OUTPUT_DIR}/${final_name}.so" "${OUTPUT_DIR}/${final_name}".*.so; do
        if [[ -f "${cand}" ]]; then produced="${cand}"; break; fi
    done
    if [[ -z "${produced}" ]]; then
        echo "[FATAL] Expected Nuitka output not found for ${final_name}" >&2
        ls -l "${OUTPUT_DIR}" >&2 || true
        exit 1
    fi

    mv "${produced}" "${STAGE_DIR}/${final_name}"
    chmod 0755 "${STAGE_DIR}/${final_name}"
    python3 "${REPO_ROOT}/tools/manage_binaries.py" write-info \
        --binary "${STAGE_DIR}/${final_name}" --module "${module}" \
        --repo "${REPO_ROOT}" > /dev/null
    BUILT_NAMES+=("${final_name}")

    local size_bytes size_h
    size_bytes="$(du -sb "${STAGE_DIR}/${final_name}" | cut -f1)"
    size_h="$(du -h "${STAGE_DIR}/${final_name}" | cut -f1)"
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
echo "  NUTKA_JOBS  : ${NUTKA_JOBS} (cpu threads: ${_cpu_threads})"
[[ -n "${NUTKA_EXTRA_FLAGS}" ]] && echo "  EXTRA FLAGS : ${NUTKA_EXTRA_FLAGS}"
echo "  エントリポイント数: ${#ENTRIES[@]}"
echo ""

built=0
for entry in "${ENTRIES[@]}"; do
    module="${entry%%:*}"
    rest="${entry#*:}"
    final_name="${rest%%:*}"
    cls="${rest#*:}"
    if [[ -n "${BUILD_ONLY}" && " ${BUILD_ONLY} " != *" ${final_name} "* ]]; then
        continue
    fi
    build_one "${module}" "${final_name}" "${cls}"
    built=$(( built + 1 ))
done
if (( built == 0 )); then
    echo "[FATAL] BUILD_ONLY='${BUILD_ONLY}' matched no entry." >&2
    exit 1
fi

# 要求した全バイナリが成功した後にだけ BIN_DIR へ入れ替える (途中失敗では BIN_DIR は不変)。
echo "--- swap: ${STAGE_DIR} -> ${BIN_DIR} ---"
if ! python3 "${REPO_ROOT}/tools/manage_binaries.py" swap \
        --stage-dir "${STAGE_DIR}" --bin-dir "${BIN_DIR}" \
        --names "${BUILT_NAMES[*]}" --consume; then
    echo "[FATAL] swap failed; ${BIN_DIR} was left unchanged or restored." >&2
    exit 1
fi

echo ""
echo "=== build_binaries.sh: 完了 (${built} 本) ==="
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
echo "入れ替え前の一式: ${BIN_DIR}.prev (戻すには bash deploy/build_binaries.sh --rollback)"
