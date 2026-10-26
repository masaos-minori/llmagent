#!/bin/bash
# init_db.sh
# SQLite スキーマを初期化する。deploy.sh 実行後に一度だけ実行すること。
# 既存の DB がある場合は上書きされないため、再初期化には手動で DB ファイルを削除すること。
#
# 使用例:
#   bash deploy/init_db.sh

set -euo pipefail

# Production never installs the dev dependency group and never rewrites uv.lock.
UV_PROD_FLAGS=(--frozen --no-dev)

# Production paths. DEPLOY_SCRIPTS/DEPLOY_DB honor environment overrides so the
# sandboxed integration tests (tests/deploy/test_init_db_eventbus_schema.py) can run the
# real script without touching /opt/llm; production invocations set neither variable.
DEPLOY_SCRIPTS="${DEPLOY_SCRIPTS:-/opt/llm/scripts}"
DEPLOY_DB="${DEPLOY_DB:-/opt/llm/db}"

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
(cd /opt/llm && PYTHONPATH="${DEPLOY_SCRIPTS}" UV_SYSTEM_CERTS=true uv run "${UV_PROD_FLAGS[@]}" python "${DEPLOY_SCRIPTS}/db/create_schema.py")

# ── テーブル確認 ──────────────────────────────────────────────────────────────
echo "--- テーブル確認 ---"
sqlite3 "${DEPLOY_DB}/rag.sqlite" ".tables"
# 期待値: chunks  chunks_fts  chunks_vec  documents

sqlite3 "${DEPLOY_DB}/session.sqlite" ".tables"
# 期待値: memories  memories_fts  memories_vec  memory_links  messages  session_diagnostics  sessions  tool_results

# Workflow: schema table verification (see docs/02_deployment.md §3.1)
echo "--- workflow.sqlite テーブル確認 ---"
REQUIRED_WORKFLOW_TABLES="tasks attempts processed_events artifacts"
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

# ── eventbus.sqlite 形状ゲート（REQ-003）────────────────────────────────────────
# 存在確認だけでなく shared.eventbus_schema_fingerprint で正準形状と比較し、
# バージョン一致で形状だけのずれた DB を service 起動前に reject する。
echo "--- eventbus.sqlite 形状検証 ---"
EVENTBUS_DB="${DEPLOY_DB}/eventbus.sqlite"
if [ ! -f "${EVENTBUS_DB}" ]; then
    echo "[FATAL] EventBus database is missing: ${EVENTBUS_DB}" >&2
    exit 1
fi
if ! (cd /opt/llm && PYTHONPATH="${DEPLOY_SCRIPTS}" EVENTBUS_DB="${EVENTBUS_DB}" \
    UV_SYSTEM_CERTS=true uv run "${UV_PROD_FLAGS[@]}" python - <<'PY'
import os
import sqlite3

from shared.eventbus_schema_fingerprint import assert_matches

db_path = os.environ["EVENTBUS_DB"]
conn = sqlite3.connect(db_path)
try:
    assert_matches(conn, label=db_path)
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    tables = [row[0] for row in rows]
finally:
    conn.close()
print(f"OK: {db_path} matches the canonical EventBus schema")
print("tables:", " ".join(tables))
PY
); then
    echo "[FATAL] EventBus database schema is missing or malformed: ${EVENTBUS_DB}" >&2
    echo "Delete the database and re-run init_db.sh before starting the Event Bus services." >&2
    exit 1
fi

echo "=== init_db.sh: 完了 ==="
echo ""
echo "次のステップ:"
echo "  bash deploy/setup_services.sh  # サブプロセス登録・起動"
