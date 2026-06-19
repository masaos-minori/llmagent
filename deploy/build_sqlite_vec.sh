#!/bin/bash
# build_sqlite_vec.sh
# sqlite-vec loadable extension (vec0.so) を取得・ビルドしてインストールする。
# 初回デプロイ時に一度実行する。バージョン更新時は再実行すること。
#
# 前提ツール: git, gcc, make, curl
#
# 使用例:
#   bash deploy/build_sqlite_vec.sh

set -euo pipefail

SQLITE_VEC_DIR="/opt/llm/sqlite-vec"
VEC_SO_DEST="${SQLITE_VEC_DIR}/vec0.so"
REPO_URL="https://github.com/asg017/sqlite-vec.git"

echo "=== build_sqlite_vec.sh: sqlite-vec ビルド開始 ==="

# ── リポジトリの取得 ──────────────────────────────────────────────────────────
if [ -d "${SQLITE_VEC_DIR}/.git" ]; then
    echo "--- 既存リポジトリを更新 (git pull) ---"
    git -C "${SQLITE_VEC_DIR}" pull --ff-only
else
    echo "--- リポジトリをクローン ---"
    git clone "${REPO_URL}" "${SQLITE_VEC_DIR}"
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
# common.toml: sqlite_vec_so = "/opt/llm/sqlite-vec/vec0.so"
echo "--- ${VEC_SO_DEST} へコピー ---"
cp dist/vec0.so "${VEC_SO_DEST}"

echo "=== build_sqlite_vec.sh: 完了 ==="
echo ""
echo "インストール先: ${VEC_SO_DEST}"
echo "  → config/common.toml の sqlite_vec_so と一致しています"
echo ""
echo "次のステップ:"
echo "  bash deploy/init_db.sh  # DB スキーマ初期化 (vec0 仮想テーブルを含む)"
