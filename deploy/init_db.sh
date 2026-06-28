#!/bin/bash
# init_db.sh
# SQLite スキーマを初期化する。deploy.sh 実行後に一度だけ実行すること。
# 既存の DB がある場合は上書きされないため、再初期化には手動で DB ファイルを削除すること。
#
# 使用例:
#   bash deploy/init_db.sh

set -euo pipefail

DEPLOY_SCRIPTS="/opt/llm/scripts/db"
DEPLOY_DB="/opt/llm/db"

echo "=== init_db.sh: DB 初期化開始 ==="

# ── create_schema.py 確認 ─────────────────────────────────────────────────────
if [ ! -f "${DEPLOY_SCRIPTS}/create_schema.py" ]; then
    echo "エラー: create_schema.py が見つかりません: ${DEPLOY_SCRIPTS}/create_schema.py"
    echo "先に deploy/deploy.sh を実行してください"
    exit 1
fi

# ── ディレクトリ作成 ──────────────────────────────────────────────────────────
mkdir -p "${DEPLOY_DB}"

# ── スキーマ初期化 ────────────────────────────────────────────────────────────
echo "--- スキーマ初期化（rag + session + workflow）---"
(cd /opt/llm && PYTHONPATH="${DEPLOY_SCRIPTS}" uv run python "${DEPLOY_SCRIPTS}/create_schema.py")

# ── テーブル確認 ──────────────────────────────────────────────────────────────
echo "--- テーブル確認 ---"
sqlite3 "${DEPLOY_DB}/rag.sqlite" ".tables"
# 期待値: chunks  chunks_fts  chunks_vec  documents

sqlite3 "${DEPLOY_DB}/session.sqlite" ".tables"
# 期待値: memories  memory_links  messages  notes  sessions  session_diagnostics  tool_results

sqlite3 "${DEPLOY_DB}/workflow.sqlite" ".tables"
# expected: artifacts  attempts  approvals  processed_events  tasks

echo "--- Event Bus DB 初期化 ---"
EVENTBUS_DB="/opt/llm/db/eventbus.sqlite"

if [ ! -f "${EVENTBUS_DB}" ]; then
    echo "  eventbus.sqlite 作成: ${EVENTBUS_DB}"
    sqlite3 "${EVENTBUS_DB}" <<'SQL'
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS events (
    seq                    INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id               TEXT    NOT NULL UNIQUE,
    topic                  TEXT    NOT NULL,
    payload                TEXT    NOT NULL,
    producer               TEXT    NOT NULL,
    published_at           TEXT    NOT NULL,
    acked_at               TEXT,
    retry_count            INTEGER NOT NULL DEFAULT 0,
    delivery_failure_count INTEGER NOT NULL DEFAULT 0,
    dlq_requeue_count      INTEGER NOT NULL DEFAULT 0,
    dlq_at                 TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_topic ON events(topic);
CREATE INDEX IF NOT EXISTS idx_events_seq   ON events(seq);
CREATE INDEX IF NOT EXISTS idx_events_dlq_at ON events(dlq_at);
CREATE INDEX IF NOT EXISTS idx_events_dlq_seq ON events(dlq_at, seq);
SQL
    echo "  完了"
else
    echo "  eventbus.sqlite 既存のためスキップ（既存 DB は _migrate() でマイグレーション済み）"
fi

echo "=== init_db.sh: 完了 ==="
echo ""
echo "次のステップ:"
echo "  bash deploy/setup_services.sh  # サブプロセス登録・起動"
