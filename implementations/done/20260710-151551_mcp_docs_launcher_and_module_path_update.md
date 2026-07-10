# Implementation: Document `mcp_launcher.py` and fix stale module paths (Phase 4)

## Goal

Document the new standalone-launch workflow (`scripts/mcp_launcher.py`, from Phase 2) in the MCP configuration/operations doc set, and correct the module-path column in `skills/mcp-server-add/SKILL.md`'s server reference table — both to the post-rename `mcp_servers.<name>.server` path, fixing the `mdq-mcp` row's pre-existing incorrect path along the way.

## Scope

**In:**
- Add a new "個別起動(開発/デバッグ用)" ("Standalone launch (dev/debug)") section documenting `mcp_launcher.py`'s usage and the reason for the `scripts/mcp` → `scripts/mcp_servers` rename (name collision with the PyPI `mcp` SDK), placed in whichever `docs/04_mcp_06_*.md` successor file covers server startup/operational procedures — the original monolithic `docs/04_mcp_06_configuration_and_operations.md` has since been split by a concurrent documentation-restructuring effort into ~16 focused files (`04_mcp_06_mcp-failure-diagnosis.md`, `04_mcp_06_watchdog-configuration-monitoring.md`, `04_mcp_06_verification-methods.md`, etc.); re-identify the correct target file at implementation time rather than assuming the original filename still exists
- `skills/mcp-server-add/SKILL.md`: update all 10 rows of the "Existing MCP servers (reference)" table from `mcp/<name>/server.py` to `mcp_servers/<name>/server.py`, and fix the `mdq-mcp` row specifically (currently the only stale entry, showing `scripts/mdq_mcp_server.py` instead of the `mcp/<name>/server.py` pattern used by every other row) to `mcp_servers/mdq/server.py`

**Out:**
- No change to the table's port numbers or service names — only the module path column and the mdq row's path format
- No renaming of any `docs/04_mcp_*.md` file — the doc-set's `04_mcp_*` numbering is independent of the Python package name (per Phase 1's own scope note)

## Assumptions

1. This document depends on Phase 1 (package rename) and Phase 2 (`mcp_launcher.py` creation) having landed first — the section text and table paths both reference `mcp_servers`, the post-rename name.
2. The original target file named in the source plan (`docs/04_mcp_06_configuration_and_operations.md`) no longer exists as of this planning pass — confirmed via `ls docs/04_mcp_06*.md`, which shows 16 split files instead (e.g. `04_mcp_06_purpose.md`, `04_mcp_06_verification-methods.md`, `04_mcp_06_mcp-failure-diagnosis.md`). The most topically fitting home for a new "standalone launch" section is likely `04_mcp_06_verification-methods.md` or a new dedicated file — this must be confirmed by reading the current split's document guide (`04_mcp_00_document-guide.md` or equivalent) at implementation time.
3. `skills/mcp-server-add/SKILL.md`'s table currently shows exactly one stale/inconsistent row (`mdq-mcp`); the other 9 rows consistently use the `mcp/<name>/server.py` pattern (confirmed by direct read at planning time) and need only the `mcp` → `mcp_servers` prefix substitution, not a structural fix.

## Implementation

### Target file

1. A `docs/04_mcp_06_*.md` file to be identified at implementation time (see Assumption 2)
2. `skills/mcp-server-add/SKILL.md`

### Procedure

1. Read `docs/04_mcp_00_document-guide.md` (or its current successor) to determine which `04_mcp_06_*` split file is the appropriate home for a "standalone launch for dev/debug" topic — likely alongside verification/diagnosis content given its audience (developers debugging one server).
2. Add a new section to that file:
   ```markdown
   ## Standalone launch (dev/debug)

   Each MCP server can be launched individually for local debugging via the unified launcher:

   \`\`\`bash
   uv run python scripts/mcp_launcher.py <server_key>      # launch one server standalone
   uv run python scripts/mcp_launcher.py --list             # list all discoverable server keys
   uv run python scripts/mcp_launcher.py <server_key> --force # bypass the port-collision guard
   \`\`\`

   **Why `mcp_servers`, not `mcp`**: the package was renamed from `scripts/mcp` to
   `scripts/mcp_servers` because the original name collided with the PyPI Model Context
   Protocol SDK (`mcp`), which is transitively installed via the `semgrep` dev dependency —
   this caused `ModuleNotFoundError: No module named 'mcp.audit'` when launching a server
   standalone in the dev venv.

   The launcher guards against accidentally starting a server whose port is already bound
   (e.g., by the running agent) — use `--force` only when intentionally starting a
   duplicate instance.
   ```
3. In `skills/mcp-server-add/SKILL.md`, update the "Existing MCP servers (reference)" table: replace the `mcp/` prefix with `mcp_servers/` in all 10 rows, and additionally fix the `mdq-mcp` row's path from `scripts/mdq_mcp_server.py` to `mcp_servers/mdq/server.py` to match the pattern used by every other row.
4. Run `python -m tools.check_docs_consistency` and `python tools/check_mcp_docs_consistency.py` (or its post-rename equivalent name) to confirm the doc set remains internally consistent.

### Method

Direct section addition + table cell correction; no new documentation structure beyond what the existing `04_mcp_06_*` split convention already uses (one focused topic per file, "## Related Documents"/"## Keywords" footer sections per the pattern observed in other recently-split files).

### Details

- The `mdq-mcp` path correction (`scripts/mdq_mcp_server.py` → `mcp_servers/mdq/server.py`) is a genuine pre-existing documentation bug being fixed opportunistically alongside the rename — not something introduced by Phase 1. It is called out explicitly here so the fix isn't mistaken for a rename artifact during review.
- If no existing `04_mcp_06_*` split file is a clean fit for the new "standalone launch" section, create a new one (e.g. `04_mcp_06_standalone-launch-for-debugging.md`) following the same frontmatter/footer conventions already used by its siblings, and add it to whichever index/document-guide file tracks the full `04_mcp_06_*` set.

## Validation plan

```bash
python -m tools.check_docs_consistency
python tools/check_mcp_docs_consistency.py   # or renamed successor; verify entry point name at implementation time
grep -rn "mcp_launcher" docs/04_mcp_06_*.md          # expect at least 1 match in the new section
grep -n "mcp/" skills/mcp-server-add/SKILL.md         # expect no output (all rows now use mcp_servers/)
grep -n "scripts/mdq_mcp_server.py" skills/mcp-server-add/SKILL.md   # expect no output (mdq row fixed)
```

Expected outcome: the doc set documents `mcp_launcher.py`'s usage and the rename rationale; the server-add skill's reference table uses consistent `mcp_servers/<name>/server.py` paths for all 10 servers, including a corrected `mdq-mcp` row.
