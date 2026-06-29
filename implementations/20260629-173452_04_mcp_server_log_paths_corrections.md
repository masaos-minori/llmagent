# Implementation: Correct MCP server log paths and audit log documentation

## Goal

Update `docs/04_mcp_06_configuration_and_operations.md` with verified application log paths and audit log paths for all 11 MCP servers, correcting three confirmed inaccuracies in the existing tables.

## Scope

- **In-Scope**:
  - Correct the per-server application log table (add sqlite-mcp row, correct "No server module yet" claim)
  - Correct the per-server audit log table (fix github-mcp filename inconsistency, correct git-mcp and sqlite-mcp "not implemented" notes)
  - Update the inline note about cicd-mcp and git-mcp audit logging
  - Verify deploy.sh already creates `/opt/llm/logs/` (confirmed: `mkdir -p "${DEPLOY_LOGS}"`)
  - Add troubleshooting note about sqlite-mcp audit_log_path being a no-op (config key exists but `SqliteConfig.from_dict` ignores it)
- **Out-of-Scope**:
  - Changing log format or log rotation
  - Adding FileHandler to cicd-mcp, git-mcp, or sqlite-mcp server code
  - Implementing git-mcp or sqlite-mcp audit logging (requires separate issue)
  - Modifying deploy scripts (log dir already created by `mkdir -p "${DEPLOY_LOGS}"`)

## Assumptions

- `/opt/llm/logs/` is always created by `deploy/deploy.sh` before any server starts; no per-server mkdir needed.
- The authoritative log path for each server is its `server.py` `Logger(...)` call and/or its TOML `audit_log_path` value, not the documentation.
- `mcp/audit.py::_audit_log()` always writes through the Python logging system (no dedicated file), so cicd-mcp audit records appear in the Python root logger output, not a named file.
- The deployed `/opt/llm/scripts/mcp/sqlite/server.py` is the canonical implementation reference for sqlite-mcp (no corresponding source file exists in the repo at `scripts/mcp/sqlite/*.py`).

## Unknowns Resolution

| ID | Description | Resolution |
|---|---|---|
| UNK-01 | github-mcp audit log filename: TOML says `github_audit.log` but doc says `github-audit.log` | TOML value is `audit_log_path = "/opt/llm/logs/github_audit.log"` → doc is wrong |
| UNK-02 | git-mcp audit_log_path in `git_mcp_server.toml` (`/opt/llm/logs/git-mcp.log`) but no audit write code in service.py | Config key is dead; doc should state "config key exists but no audit write code" |
| UNK-03 | sqlite-mcp: `sqlite_mcp_server.toml` has `audit_log_path = "/opt/llm/logs/sqlite-mcp.log"` but `SqliteConfig.from_dict` does not parse it | Config key is unused; doc should state "config key is not parsed; no audit log written" |
| UNK-04 | sqlite-mcp: doc row says "No server module yet" but `/opt/llm/scripts/mcp/sqlite/server.py` exists (deployed) | sqlite-mcp is implemented (SELECT-only, port 8011); update app log row accordingly |
| UNK-05 | cicd-mcp audit log destination: uses `_audit_log(logger, ...)` where `logger = logging.getLogger(__name__)` | No FileHandler attached; output goes to Python root logger / uvicorn stdout |

## Implementation

### Target file: `docs/04_mcp_06_configuration_and_operations.md`

#### Procedure

1. Fix inline grep example (line 264): correct `github-audit.log` → `github_audit.log`
2. Fix application log table (line 292): update sqlite-mcp row
3. Fix audit log table (lines 302, 307, 308): fix github-mcp filename and git/sqlite-mcp notes

#### Method

Direct file edit — four replacements in the same file.

#### Details

**1. Fix inline grep example (line 264):**
```markdown
# Before:
grep "op=create_pull_request" /opt/llm/logs/github-audit.log

# After:
grep "op=create_pull_request" /opt/llm/logs/github_audit.log
```

**2. Fix application log table sqlite-mcp row (line 292):**
```markdown
# Before:
| sqlite-mcp | No server module yet | Config exists but no implementation (planned) |

# After:
| sqlite-mcp | No dedicated log file | Uses `logging.getLogger(__name__)` (SELECT-only, port 8011) |
```

**3. Fix audit log table github-mcp row (line 302):**
```markdown
# Before:
| github-mcp | `/opt/llm/logs/github-audit.log` | Structured (ISO8601 + op + repo + user) |

# After:
| github-mcp | `/opt/llm/logs/github_audit.log` | Structured (ISO8601 + op + repo + user) |
```

**4. Fix audit log table git-mcp row (line 307):**
```markdown
# Before:
| git-mcp | Config field defined but not implemented | `audit_log_path` in config exists but no actual audit logging code |

# After:
| git-mcp | Config key exists but no write implementation | `audit_log_path = "/opt/llm/logs/git-mcp.log"` in config; no audit write code in `service.py`; key reserved for future use |
```

**5. Fix audit log table sqlite-mcp row (line 308):**
```markdown
# Before:
| sqlite-mcp | No server module yet | Config has `audit_log_path = "/opt/llm/logs/sqlite-mcp.log"` but no implementation (planned) |

# After:
| sqlite-mcp | Config key exists but not parsed | `audit_log_path = "/opt/llm/logs/sqlite-mcp.log"` in config; `SqliteConfig.from_dict` does not parse this key; no audit log written |
```

**6. Add inline note about cicd-mcp/git-mcp/sqlite-mcp audit logging:**

Add after line 274 (after the grep examples):
```markdown
**Note:** cicd-mcp, git-mcp, and sqlite-mcp do not have dedicated audit log files. cicd-mcp uses `mcp/audit.py::_audit_log()` which writes through the Python root logger (no FileHandler). git-mcp and sqlite-mcp have `audit_log_path` in their TOML configs but no write implementation — these keys are reserved for future use.
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_06_configuration_and_operations.md` | Grep for stale text | `grep -n "No server module\|github-audit.log" docs/04_mcp_06_configuration_and_operations.md` | No output (stale text removed) |
| github-mcp audit log filename | Grep for old name across all docs | `grep -rn "github-audit.log" docs/` | No output (all occurrences fixed) |
| All 11 servers present | Count server rows in app log table | `grep -c "|-mcp|" docs/04_mcp_06_configuration_and_operations.md` | Both tables have 11 server rows |
| Cross-check with TOML | Verify doc paths match config | `grep "audit_log_path" config/github_mcp_server.toml config/shell_mcp_server.toml config/file_delete_mcp_server.toml config/mdq_mcp_server.toml config/git_mcp_server.toml config/sqlite_mcp_server.toml` | Paths match doc |

## Risks & Mitigations

- **Risk**: Other documentation files reference `github-audit.log` (wrong name) → **Mitigation**: Run `grep -rn "github-audit.log" docs/` before committing; fix any additional occurrences
- **Risk**: sqlite-mcp `audit_log_path` TOML key being documented as "not parsed" may confuse operators trying to configure it → **Mitigation**: Add a parenthetical note in the doc: "(config key is present in TOML for future use but is not read by `SqliteConfig.from_dict`)"
- **Risk**: git-mcp `audit_log_path` is loaded into `GitConfig` but never written to; a future code change could silently start writing to a path operators do not expect → **Mitigation**: Note in doc that the key is "reserved; write implementation pending separate issue"
