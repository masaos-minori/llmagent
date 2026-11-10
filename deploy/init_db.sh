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

# ── eventbus.sqlite（EventBus 側ツールが作成・検証する）─────────────────────────
# eventbus.sqlite is owned by the EventBus service: its path comes from
# EVENTBUS_CONFIG_PATH (default /opt/llm/config/eventbus.toml) and creation, shape
# validation, archive, and verification live in eventbus.db_tools. The tool reads only
# db_path, so no EventBus token variable is needed here.
eventbus_db_tool() {
  (cd /opt/llm && PYTHONPATH="${DEPLOY_SCRIPTS}" UV_SYSTEM_CERTS=true \
    uv run "${UV_PROD_FLAGS[@]}" python -m eventbus.db_tools "$@")
}

echo "--- eventbus.sqlite パス解決（eventbus.db_tools）---"
EVENTBUS_DB="$(eventbus_db_tool path)" || {
    echo "[FATAL] EventBus database path cannot be resolved from the EventBus configuration" >&2
    exit 1
}

# ── テーブル確認 ──────────────────────────────────────────────────────────────
echo "--- テーブル確認 ---"
sqlite3 "${DEPLOY_DB}/rag.sqlite" ".tables"
# 期待値: chunks  chunks_fts  chunks_vec  documents

sqlite3 "${DEPLOY_DB}/session.sqlite" ".tables"
# 期待値: memories  memories_fts  memories_vec  memory_links  messages  session_diagnostics  sessions  tool_results

# Workflow: schema table verification (see docs/02_deployment.md §3.1)
echo "--- workflow.sqlite テーブル確認 ---"
REQUIRED_WORKFLOW_TABLES="tasks attempts processed_events artifacts tool_call_state"
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

# ── レガシー マーカー ゲート (REQ-005) ────────────────────────────────────────
# workflow.sqlite and eventbus.sqlite must not carry legacy migration marker
# tables. A database created or carried by the removed migration tooling predates
# the current-schema-only policy; no migration or re-stamping is supported, so
# reject it before the shape checks (fail-closed, same style as the workflow
# table gate above). The script performs no write, archive, or delete itself.
echo "--- legacy migration marker check ---"
for DB_FILE in "${DEPLOY_DB}/workflow.sqlite" "${EVENTBUS_DB}"; do
  # eventbus.sqlite does not exist yet on a fresh deploy (it is created below);
  # sqlite3 would create an empty file, so skip a missing one.
  [ -f "${DB_FILE}" ] || continue
  DB_NAME="$(basename "${DB_FILE}")"
  COUNT=$(sqlite3 "${DB_FILE}" \
    "SELECT count(*) FROM sqlite_master WHERE type='table' AND name IN ('schema_migrations','workflow_schema_version');")
  if [ "${COUNT}" != "0" ]; then
    echo "[FATAL] ${DB_NAME} carries legacy migration marker table(s) and does not match the current schema." >&2
    echo "Automatic migration and version stamping are not supported." >&2
    echo "Stop the service, archive the existing database if required, remove or rename it, and create a new database using the current schema:" >&2
    echo "  1. Archive it with the rotation step (rotate_all_dbs)" >&2
    echo "  2. Remove or rename ${DB_FILE}" >&2
    echo "  3. Re-run deploy/init_db.sh" >&2
    exit 1
  fi
done
echo "OK: no legacy migration marker tables in workflow.sqlite and eventbus.sqlite"

# ── eventbus.sqlite 作成・形状ゲート（REQ-003）──────────────────────────────────
# レガシー マーカー ゲートを通過した後に eventbus.db_tools ensure で作成（または検証）し、
# 存在確認だけでなく eventbus.db_tools verify（integrity_check と
# shared.eventbus_schema_fingerprint による正準形状比較）を通し、
# バージョン一致で形状だけのずれた DB を service 起動前に reject する。
echo "--- eventbus.sqlite 作成・形状検証 ---"
if ! eventbus_db_tool ensure >/dev/null; then
    echo "[FATAL] EventBus database schema is missing or malformed: ${EVENTBUS_DB}" >&2
    echo "Delete the database and re-run init_db.sh before starting the Event Bus services." >&2
    exit 1
fi
if [ ! -f "${EVENTBUS_DB}" ]; then
    echo "[FATAL] EventBus database is missing: ${EVENTBUS_DB}" >&2
    exit 1
fi
if ! eventbus_db_tool verify >/dev/null; then
    echo "[FATAL] EventBus database schema is missing or malformed: ${EVENTBUS_DB}" >&2
    echo "Delete the database and re-run init_db.sh before starting the Event Bus services." >&2
    exit 1
fi
echo "OK: ${EVENTBUS_DB} matches the canonical EventBus schema"
echo "tables: $(sqlite3 "${EVENTBUS_DB}" ".tables" | tr -s ' \n' ' ')"

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
    # eventbus.sqlite is verified by the EventBus-owned tool (integrity and shape);
    # recovery_drill.py covers rag, session, and workflow.
    if eventbus_db_tool verify >/dev/null; then
      echo "OK: eventbus.sqlite verified by eventbus.db_tools"
    else
      echo "[FATAL] eventbus.db_tools verify failed for ${EVENTBUS_DB}" >&2
      exit 1
    fi
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
