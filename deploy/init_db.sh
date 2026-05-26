#!/bin/bash
# init_db.sh
# SQLite スキーマを初期化する。deploy.sh 実行後に一度だけ実行すること。
# 既存の DB がある場合は上書きされないため、再初期化には手動で DB ファイルを削除すること。
#
# 使用例:
#   bash deploy/init_db.sh

set -euo pipefail

VENV="/opt/llm/venv"
DEPLOY_SCRIPTS="/opt/llm/scripts"
DEPLOY_DB="/opt/llm/db"

echo "=== init_db.sh: DB 初期化開始 ==="

# ── venv 確認 ─────────────────────────────────────────────────────────────────
if [ ! -f "${VENV}/bin/activate" ]; then
    echo "エラー: venv が見つかりません: ${VENV}"
    echo "先に Python venv を構築してください: python3.11 -m venv ${VENV}"
    exit 1
fi

# ── create_schema.py 確認 ─────────────────────────────────────────────────────
if [ ! -f "${DEPLOY_SCRIPTS}/create_schema.py" ]; then
    echo "エラー: create_schema.py が見つかりません: ${DEPLOY_SCRIPTS}/create_schema.py"
    echo "先に deploy/deploy.sh を実行してください"
    exit 1
fi

# ── ディレクトリ作成 ──────────────────────────────────────────────────────────
mkdir -p "${DEPLOY_DB}"

# ── スキーマ初期化 ────────────────────────────────────────────────────────────
echo "--- スキーマ初期化: ${DEPLOY_DB}/rag.sqlite ---"
# shellcheck disable=SC1090
source "${VENV}/bin/activate"
python "${DEPLOY_SCRIPTS}/create_schema.py"

# ── テーブル確認 ──────────────────────────────────────────────────────────────
echo "--- テーブル確認 ---"
sqlite3 "${DEPLOY_DB}/rag.sqlite" ".tables"
# 期待値: chunks  chunks_fts  chunks_vec  documents

echo "=== init_db.sh: 完了 ==="
echo ""
echo "次のステップ:"
echo "  bash deploy/setup_services.sh  # OpenRC サービス登録・起動"
