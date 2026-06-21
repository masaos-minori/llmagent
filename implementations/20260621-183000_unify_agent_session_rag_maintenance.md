# Implementation: Unify AgentSession/RAG Maintenance Responsibility Boundary

## Goal

Document that `AgentSession` has zero RAG-layer dependency, all RAG maintenance routes through `RagMaintenanceService`, and add the session.sqlite corruption-recovery gap note.

## Scope

**In:**
- Verify `AgentSession` (session.py) has no RAG-layer imports or schema references
- Confirm `/db` RAG subcommands route through `RagMaintenanceService` (cmd_db.py)
- Confirm `DbMaintenanceService` is session.sqlite-only after the 2bcb195 split
- Document the session.sqlite corruption-recovery gap (`/db recover` targets rag.sqlite only)
- Update `docs/05_agent_90_inconsistencies_and_known_issues.md` with OQ-01 resolution and session recovery gap

**Out:**
- Redesigning the RAG retrieval pipeline itself
- Removing `/db` maintenance commands
- Changing `recover_corruption()` internal logic in `db/maintenance.py`

## Assumptions

1. `AgentSession` has zero RAG imports — verified by grep on `session.py`.
2. `RagMaintenanceService` is the sole RAG rag.sqlite maintainer in the agent layer — verified by `test_mdq_rag_boundary.py::test_agent_layer_rag_sqlite_access_only_in_maintenance_service`.
3. `recover_corruption()` has a `target` parameter defaulting to `"rag"` — confirmed in `db/maintenance.py:356`.
4. `/db recover` routes through `RagMaintenanceService.recover()` which calls `recover_corruption(backup_path)` with default `target="rag"`, so it targets rag.sqlite only.
5. No existing test or operator path exercises session.sqlite corruption recovery.

## Implementation

### Target files

- `docs/05_agent_90_inconsistencies_and_known_issues.md` — add OQ-01 resolution + session-recover gap notes (doc-only)
- `scripts/agent/services/db_maintenance_service.py` — optionally add `recover_session()` method (low churn)
- `scripts/agent/commands/cmd_db.py` — optionally expose `/db recover --target session` (low churn)

### Procedure

#### Step 1: Verify boundary completeness (no code change)

1. Grep `session.py` for RAG-layer imports:
   ```bash
   grep -n 'rag\|RagMaintenance\|SQLiteHelper.*rag' scripts/agent/session.py
   ```
2. Confirm only these imports exist: `db.helper`, `shared.types`, `agent.note_repo`, `agent.session_message_repo`
3. Run boundary test:
   ```bash
   uv run pytest tests/test_mdq_rag_boundary.py -v
   ```
4. Confirm `cmd_db.py`: `_db_rebuild_fts`, `_db_consistency`, `_db_recover` call `RagMaintenanceService`

#### Step 2: Document the session.sqlite recovery gap

Add to `docs/05_agent_90_inconsistencies_and_known_issues.md`:

```markdown
### Session SQLite corruption recovery gap

- `/db recover` only targets `rag.sqlite` (via `RagMaintenanceService`)
- No session.sqlite corruption recovery path exists in the agent REPL
- Resolution: add `DbMaintenanceService.recover_session()` + `/db recover --target session` if needed
```

#### Step 3: Add OQ-01 resolution note to inconsistencies doc

Add to `docs/05_agent_90_inconsistencies_and_known_issues.md`:

```markdown
### OQ-01: AgentSession RAG-layer dependency

**Status:** Resolved

`AgentSession` has zero RAG-layer imports. All RAG maintenance routes through `RagMaintenanceService`.
```

#### Step 4 (Optional): Add session.sqlite recover path

1. Add `recover_session()` method to `DbMaintenanceService`:
   ```python
   def recover_session(self, backup_path: str) -> None:
       """Recover session.sqlite from a backup file."""
       self._db.recover_corruption(backup_path, target="session")
   ```

2. Update `_db_recover()` in `cmd_db.py` to accept optional `--target` flag:
   ```python
   def _db_recover(self, backup_path: str, target: str = "rag") -> None:
       """Recover a database from backup."""
       if target == "session":
           self._db_maint.recover_session(backup_path)
       else:
           self._rag_maint.recover(backup_path)
   ```

3. Update CLI argument parser to accept `--target rag|session` (default: rag)

### Method

- Doc-only changes for steps 1-3 (no code changes required)
- Optional code changes for step 4 (low blast radius, session.sqlite only)

### Details

- The session-recovery gap is a documentation issue, not a code defect. No existing operator path exercises it.
- OQ-01 resolution is already confirmed by `test_mdq_rag_boundary.py` — only the inconsistencies doc needs updating.
- If step 4 is implemented, default to `rag` for backward compatibility and document clearly in changelog.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors |
| Architecture | `uv run lint-imports` | 0 violations |
| Boundary test | `uv run pytest tests/test_mdq_rag_boundary.py -v` | all pass |
| DB tests | `uv run pytest tests/test_agent_cmd_db.py -v` | all pass |
| Full suite | `uv run pytest -q` | no new failures |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Adding `/db recover --target session` changes user-facing CLI | Low | Default to `rag` for backward compatibility; document clearly |
| `recover_corruption(target="session")` path untested | Low | Add unit test covering session-target recovery path |
| Doc-only change causes no test failures but misses something | Low | Cross-check with boundary test passing |
