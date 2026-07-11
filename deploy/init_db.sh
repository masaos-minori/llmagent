#!/bin/bash
# init_db.sh
# SQLite スキーマを初期化する。deploy.sh 実行後に一度だけ実行すること。
# 既存の DB がある場合は上書きされないため、再初期化には手動で DB ファイルを削除すること。
#
# 使用例:
#   bash deploy/init_db.sh

set -euo pipefail

DEPLOY_SCRIPTS="/opt/llm/scripts"
DEPLOY_DB="/opt/llm/db"

echo "=== init_db.sh: DB 初期化開始 ==="

# ── create_schema.py 確認 ─────────────────────────────────────────────────────
if [ ! -f "${DEPLOY_SCRIPTS}/db/create_schema.py" ]; then
    echo "エラー: create_schema.py が見つかりません: ${DEPLOY_SCRIPTS}/db/create_schema.py"
    echo "先に deploy/deploy.sh を実行してください"
    exit 1
fi

# ── ディレクトリ作成 ──────────────────────────────────────────────────────────
mkdir -p "${DEPLOY_DB}"

# ── スキーマ初期化（rag + session + workflow + eventbus）──────────────────────
echo "--- スキーマ初期化（rag + session + workflow + eventbus）---"
(cd /opt/llm && PYTHONPATH="${DEPLOY_SCRIPTS}" UV_NATIVE_TLS=true uv run python "${DEPLOY_SCRIPTS}/db/create_schema.py")

# ── テーブル確認 ──────────────────────────────────────────────────────────────
echo "--- テーブル確認 ---"
sqlite3 "${DEPLOY_DB}/rag.sqlite" ".tables"
# 期待値: chunks  chunks_fts  chunks_vec  documents

sqlite3 "${DEPLOY_DB}/session.sqlite" ".tables"
# 期待値: memories  memories_fts  memories_vec  memory_links  messages  session_diagnostics  sessions  tool_results

# Workflow: schema table verification (see docs/02_deployment.md §3.1)
echo "--- workflow.sqlite テーブル確認 ---"
REQUIRED_WORKFLOW_TABLES="tasks attempts processed_events artifacts approvals"
MISSING_TABLES=""
for t in ${REQUIRED_WORKFLOW_TABLES}; do
  FOUND=$(sqlite3 "${DEPLOY_DB}/workflow.sqlite" \
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
echo "OK: all required workflow.sqlite tables present (${REQUIRED_WORKFLOW_TABLES})"

sqlite3 "${DEPLOY_DB}/eventbus.sqlite" ".tables"
# expected: events

echo "=== init_db.sh: 完了 ==="
echo ""
echo "次のステップ:"
echo "  bash deploy/setup_services.sh  # サブプロセス登録・起動"
