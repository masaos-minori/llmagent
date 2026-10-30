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

# ── Ledger baseline gate (REQ-006) ───────────────────────────────────────────
# workflow.sqlite and eventbus.sqlite must carry the schema_migrations ledger.
# A database created before the migration baseline existed cannot serve as a
# migration-compatible recovery point, so reject it before starting services
# (fail-closed, same style as the workflow table gate above).
echo "--- schema_migrations ledger check ---"
for DB_NAME in "workflow.sqlite" "eventbus.sqlite"; do
  COUNT=$(sqlite3 "${DEPLOY_DB}/${DB_NAME}" \
    "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='schema_migrations';")
  if [ "${COUNT}" != "1" ]; then
    echo "[FATAL] ${DB_NAME} is missing the schema_migrations ledger table." >&2
    echo "This database predates the migration baseline and cannot be used as a " >&2
    echo "migration-compatible recovery point." >&2
    case "${DB_NAME}" in
      workflow.sqlite)
        echo "Bootstrap the ledger first:" >&2
        echo "  python ${DEPLOY_SCRIPTS}/db/migrate_db.py --apply" >&2 ;;
      eventbus.sqlite)
        echo "Bootstrap the ledger first:" >&2
        echo "  python ${DEPLOY_SCRIPTS}/eventbus/migrate.py --apply" >&2 ;;
    esac
    exit 1
  fi
done
echo "OK: schema_migrations ledger present in workflow.sqlite and eventbus.sqlite"

# ── Recovery drill hook (REQ-007) ────────────────────────────────────────────
# Default OFF. Only run the read-only drill when an operator opts in with
# RUN_RECOVERY_DRILL=1 (drill cadence is undecided until UNK-01 is resolved).
# Resolve the configured archive dir so the artifact path is accurate.
ARCHIVE_DIR="$(
  cd /opt/llm && PYTHONPATH="${DEPLOY_SCRIPTS}" UV_SYSTEM_CERTS=true uv run "${UV_PROD_FLAGS[@]}" python - <<'PY' 2>/dev/null
from db.rotation import _resolve_archive_dir

print(_resolve_archive_dir())
PY
)"
[ -z "${ARCHIVE_DIR}" ] && ARCHIVE_DIR="/opt/llm/db/archive"
DRILLS_DIR="${ARCHIVE_DIR}/drills"

if [ "${RUN_RECOVERY_DRILL:-0}" = "1" ]; then
  echo "--- recovery drill (RUN_RECOVERY_DRILL=1) ---"
  if (cd /opt/llm && PYTHONPATH="${DEPLOY_SCRIPTS}" UV_SYSTEM_CERTS=true uv run "${UV_PROD_FLAGS[@]}" python "${DEPLOY_SCRIPTS}/db/recovery_drill.py" --domain all); then
    echo "OK: recovery drill passed for all domains; artifacts in ${DRILLS_DIR}"
  else
    echo "[FATAL] recovery drill reported failures; artifacts in ${DRILLS_DIR}" >&2
    exit 1
  fi
else
  echo "Recovery drill: set RUN_RECOVERY_DRILL=1 to exercise recovery on these databases (artifacts: ${DRILLS_DIR})"
fi

echo "=== init_db.sh: 完了 ==="
echo ""
echo "次のステップ:"
echo "  bash deploy/setup_services.sh  # サブプロセス登録・起動"
