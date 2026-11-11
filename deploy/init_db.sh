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

# eventbus.sqlite is owned by the EventBus service: its path comes from
# EVENTBUS_CONFIG_PATH (default /opt/llm/config/eventbus.toml) and creation, shape
# validation, and verification live in eventbus.db_tools. init_db.sh no longer
# resolves, validates, or touches eventbus.sqlite; deploy.sh delegates entirely
# to `eventbus.db_tools ensure` and `eventbus.db_tools verify`.

# ── テーブル確認 ──────────────────────────────────────────────────────────────
echo "--- テーブル確認 ---"
sqlite3 "${DEPLOY_DB}/rag.sqlite" ".tables"
# 期待値: chunks  chunks_fts  chunks_vec  documents

sqlite3 "${DEPLOY_DB}/session.sqlite" ".tables"
# 期待値: memories  memories_fts  memories_vec  memory_links  messages  session_diagnostics  sessions  tool_results

# ── 指紋ゲート (REQ-003/REQ-004) ──────────────────────────────────────────────
# workflow.sqlite, rag.sqlite, session.sqlite must each match the canonical DDL
# shape exactly (shared.schema_fingerprint). Extra tables — including the legacy
# migration marker tables schema_migrations and workflow_schema_version — missing
# tables, and shape drift are all refused by the exact-match comparison, so the
# former marker-table query and the workflow table-name-only gate are subsumed.
# No migration or re-stamping is supported; the script performs no write, archive,
# or delete itself (fail-closed).
echo "--- 指紋検証 (workflow/rag/session) ---"
if ! (cd /opt/llm && PYTHONPATH="${DEPLOY_SCRIPTS}" UV_SYSTEM_CERTS=true \
    uv run "${UV_PROD_FLAGS[@]}" python - "${DEPLOY_DB}" <<'PY'
import sqlite3
import sys
from pathlib import Path

from db.schema_sql import (
    build_rag_schema_sql,
    build_session_schema_sql,
    build_workflow_schema_sql,
)
from db.store_protocols import get_embedding_dims
from shared.schema_fingerprint import assert_matches

deploy_db = Path(sys.argv[1])
dims = get_embedding_dims()
targets = {
    "workflow.sqlite": build_workflow_schema_sql(),
    "rag.sqlite": build_rag_schema_sql(dims),
    "session.sqlite": build_session_schema_sql(dims),
}
failed = False
for name, ddl in sorted(targets.items()):
    path = deploy_db / name
    if not path.is_file():
        print(f"[gate] missing database: {path}", file=sys.stderr)
        failed = True
        continue
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        assert_matches(conn, ddl, label=name)
    except RuntimeError as exc:
        print(f"[gate] {exc}", file=sys.stderr)
        failed = True
    finally:
        conn.close()
sys.exit(1 if failed else 0)
PY
); then
    echo "[FATAL] Database schema does not match the current schema (workflow/rag/session)." >&2
    echo "Automatic migration and version stamping are not supported." >&2
    echo "Stop the service, archive the existing database if required, remove or rename it, and create a new database using the current schema:" >&2
    echo "  1. Archive it with the rotation step (rotate_all_dbs)" >&2
    echo "  2. Remove or rename the reported database under ${DEPLOY_DB}" >&2
    echo "  3. Re-run deploy/init_db.sh" >&2
    exit 1
fi
echo "OK: workflow.sqlite, rag.sqlite, session.sqlite match the canonical schema fingerprint"

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
