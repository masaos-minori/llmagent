## Goal

Harden SQLite connection and transaction management for MDQ by enabling WAL mode, setting busy_timeout, using explicit write transactions, preferring atomic replace per document during indexing, adding FTS consistency check, adding FTS rebuild operation, and ensuring connections are closed reliably.

## Scope

**In-Scope**:
- Enable WAL mode
- Set busy_timeout
- Use explicit write transactions
- Prefer atomic replace per document during indexing
- Add FTS consistency check
- Add FTS rebuild operation if needed
- Ensure connections are closed reliably

**Out-of-Scope**:
- Adding new tools or features
- Changes to other MCP servers' SQLite configuration

## Assumptions

1. WAL mode is supported by SQLite version used (3.7+)
2. busy_timeout = 5000ms (5 seconds) is reasonable for production use
3. FTS consistency check compares chunks row count with chunks_fts row count
4. FTS rebuild uses `INSERT INTO chunks_fts(chunks_fts, chunks_fts) VALUES ('rebuild')`

## Implementation

### Target file: scripts/mcp/mdq/service.py

**Procedure**: Add WAL mode, busy_timeout, explicit transactions, FTS consistency/rebuild methods.

**Method**: Modify _get_db_connection() method and add new methods for FTS operations.

**Details**:
1. Enable WAL mode and busy_timeout in _get_db_connection():
   - After connection creation, add `conn.execute("PRAGMA journal_mode=WAL")`
   - Add `conn.execute("PRAGMA busy_timeout = 5000")`
2. Add explicit write transaction methods:
   - Add `begin_write_transaction()` method that executes BEGIN
   - Add `commit_write_transaction()` method that executes COMMIT
   - Add `rollback_write_transaction()` method that executes ROLLBACK
3. Add FTS consistency check method:
   - Compare chunks row count with chunks_fts row count
   - Return ConsistencyResult with mismatch flag and counts
4. Add FTS rebuild method:
   - Execute `INSERT INTO chunks_fts(chunks_fts, chunks_fts) VALUES ('rebuild')`
5. Ensure reliable connection closing:
   - Add try/finally with conn.close() in all code paths

### Target file: scripts/mcp/mdq/indexer.py

**Procedure**: Update indexing to use atomic replace and explicit transactions.

**Method**: Modify _index_single_file() function to use INSERT OR REPLACE and explicit transaction control.

**Details**:
1. In _index_single_file(), use INSERT OR REPLACE for documents table
2. Wrap DELETE + INSERT in single transaction using begin_write_transaction/commit_write_transaction
3. Replace implicit commit() calls with explicit transaction control

### Target file: scripts/mcp/mdq/models.py

**Procedure**: Add FtsConsistencyCheck model for rebuild operation.

**Method**: Add new BaseModel class definitions in models.py.

**Details**:
1. `FtsConsistencyCheckRequest`: empty request model (no parameters)
2. `FtsConsistencyCheckResponse`: add `consistent: bool`, `chunks_count: int`, `chunks_fts_count: int` fields
3. `FtsRebuildRequest`: empty request model (no parameters)

### Target file: scripts/mcp/mdq/tools.py

**Procedure**: Add FTS consistency check and rebuild tools.

**Method**: Add new tool definitions in tools.py.

**Details**:
1. Add fts_consistency_check tool with admin status
2. Add fts_rebuild tool with admin status
3. Both tools require admin privileges to execute

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| service.py | Test WAL mode is enabled | Check journal_mode pragma | WAL returned |
| service.py | Test busy_timeout handling | Simulate lock contention | No "database is locked" errors |
| indexer.py | Test atomic replace during indexing | Modify file, re-index | Document replaced atomically |
| service.py | Test FTS consistency check | Call consistency check | Match or mismatch reported |
| service.py | Test FTS rebuild | Call rebuild operation | FTS index rebuilt successfully |

## Risks

- **Risk**: WAL mode may increase disk space usage | **Likelihood**: Low | **Mitigation**: Document WAL implications; monitor disk usage | False
- **Risk**: busy_timeout too short for large indexing operations | **Likelihood**: Medium | **Mitigation**: Make busy_timeout configurable via config | False
