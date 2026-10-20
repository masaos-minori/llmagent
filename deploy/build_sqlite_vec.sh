#!/bin/bash
# build_sqlite_vec.sh
# sqlite-vec loadable extension (vec0.so) を取得・ビルドしてインストールする。
# 初回デプロイ時に一度実行する。バージョン更新時は再実行すること。
#
# 前提ツール: git, gcc, make, curl
#
# 使用例:
#   bash deploy/build_sqlite_vec.sh
#   SQLITE_VEC_REF=v0.1.10-alpha.4 bash deploy/build_sqlite_vec.sh  # タグ/コミットを固定
#
# SQLITE_VEC_REF を指定すると、その ref を checkout してビルドする (再現性が必要な
# CI 向け)。未指定の場合は従来どおり既定ブランチの最新を取得する。

set -euo pipefail

SQLITE_VEC_DIR="/opt/llm/sqlite-vec"
VEC_SO_DEST="${SQLITE_VEC_DIR}/vec0.so"
REPO_URL="https://github.com/asg017/sqlite-vec.git"
SQLITE_VEC_REF="${SQLITE_VEC_REF:-}"

echo "=== build_sqlite_vec.sh: sqlite-vec ビルド開始 ==="

# ── リポジトリの取得 ──────────────────────────────────────────────────────────
if [ -d "${SQLITE_VEC_DIR}/.git" ]; then
    if [ -n "${SQLITE_VEC_REF}" ]; then
        echo "--- 既存リポジトリを更新 (fetch + checkout ${SQLITE_VEC_REF}) ---"
        git -C "${SQLITE_VEC_DIR}" fetch --tags origin
    else
        echo "--- 既存リポジトリを更新 (git pull) ---"
        git -C "${SQLITE_VEC_DIR}" pull --ff-only
    fi
else
    echo "--- リポジトリをクローン ---"
    git clone "${REPO_URL}" "${SQLITE_VEC_DIR}"
fi
if [ -n "${SQLITE_VEC_REF}" ]; then
    git -C "${SQLITE_VEC_DIR}" checkout --detach "${SQLITE_VEC_REF}"
fi

# ── ビルド ────────────────────────────────────────────────────────────────────
cd "${SQLITE_VEC_DIR}"

echo "--- vendor.sh: 依存ファイルを取得 ---"
./scripts/vendor.sh

echo "--- make loadable: vec0.so をビルド ---"
make loadable

echo "--- ビルド成果物を確認 ---"
ls -l dist/vec0.so

# ── config が参照するパスへコピー ─────────────────────────────────────────────
# agent.toml: sqlite_vec_so = "/opt/llm/sqlite-vec/vec0.so"
echo "--- ${VEC_SO_DEST} へコピー ---"
cp dist/vec0.so "${VEC_SO_DEST}"

echo "=== build_sqlite_vec.sh: 完了 ==="
echo ""
echo "インストール先: ${VEC_SO_DEST}"
echo "  → config/agent.toml の sqlite_vec_so と一致しています"
echo ""
echo "次のステップ:"
echo "  bash deploy/init_db.sh  # DB スキーマ初期化 (vec0 仮想テーブルを含む)"
