## Goal

Add nine new stale-pattern detector functions to `scripts/check_mcp_docs_consistency.py`, remove `"ondemand"` from `VALID_STARTUP_MODES`, wire all new checks into `main()` with `--skip` flag support, and confirm zero false positives on the current `docs/` directory.

## Scope

- In-Scope:
  - Remove `"ondemand"` from `VALID_STARTUP_MODES` constant (line 32)
  - Add eight new check functions: `check_live_discovery_routing`, `check_routing_authority_v1tools`, `check_tool_names_routing_input`, `check_audit_log_single_format`, `check_transport_error_is_error`, `check_stdio_active_transport`, `check_watchdog_restarts_on_dependency_failure`, `check_strict_validation_skips_unreachable`
  - Add corresponding skip tokens to `skip_choices` and `main()` dispatch block
  - Add module-level regex constants for each new check
  - Add `HISTORICAL_MARKERS` frozenset mirroring the set from `scripts/checks/check_mcp_docs_consistency.py`

- Out-of-Scope:
  - Changes to `scripts/checks/check_mcp_docs_consistency.py` (old checker)
  - Changes to any documentation file under `docs/`
  - Changes to `scripts/checks/check_docs_consistency.py` (RAG-focused)
  - Changes to implementation code (`scripts/shared/`, `scripts/mcp/`, `scripts/agent/`)

## Assumptions

1. `VALID_STARTUP_MODES` at line 32 currently reads `{"persistent", "ondemand", "subprocess"}`; after this change it should be `{"persistent", "subprocess"}`.
2. `"ondemand"` is a stale startup mode value — after removal, `check_startup_modes` will flag any doc that still contains `startup_mode = "ondemand"`.
3. Transport errors in `scripts/shared/tool_executor.py` still return `is_error=True` via `_record_transport_error` (line 415: `is_error=True`); therefore `check_transport_error_is_error` should use `WARNING` severity as a future-guard rather than `ERROR`.
4. Historical section detection should use a `HISTORICAL_MARKERS` frozenset (strings: `"legacy"`, `"historical"`, `"archive only"`, `"resolved"`, `"was:"`, `"removed"`) and look backward up to 10 lines, consistent with `scripts/checks/check_mcp_docs_consistency.py` line 65.
5. Fenced code block exemptions use an `in_fenced_block` boolean toggled by lines starting with triple backtick (```` ``` ````), consistent with existing checks in the old checker.
6. The `--skip` argument uses `nargs="+"` and `choices=skip_choices` — adding new tokens to `skip_choices` list is sufficient.
7. `MCP_KNOWN_ISSUES_FILE = "04_mcp_90_inconsistencies_and_known_issues.md"` (already defined at line 34) is the allowlist file for several checks.
8. The `main()` dispatch block follows the pattern `if "token" not in skip: all_issues.extend(check_fn(docs_dir, files))`.

## Implementation

### Target file

`/home/masaos/llmagent/scripts/check_mcp_docs_consistency.py`

### Procedure

1. **Remove `"ondemand"` from `VALID_STARTUP_MODES`** (line 32):
   - Change `{"persistent", "ondemand", "subprocess"}` to `{"persistent", "subprocess"}`.

2. **Add `HISTORICAL_MARKERS` frozenset** after the `_ACTIVE_ISSUE_ALLOWLIST` block (after line 48):
   ```python
   HISTORICAL_MARKERS: frozenset[str] = frozenset(
       {"legacy", "historical", "archive only", "resolved", "was:", "removed"}
   )
   ```

3. **Add `_is_historical_context` helper** after `HISTORICAL_MARKERS`:
   ```python
   def _is_historical_context(lines: list[str], line_idx: int) -> bool:
       """Return True if line_idx is within 10 lines of a historical section marker."""
       start = max(0, line_idx - 10)
       for i in range(start, line_idx):
           if any(marker in lines[i].lower() for marker in HISTORICAL_MARKERS):
               return True
       return False
   ```

4. **Add `_in_fenced_block` tracking helper** (stateful toggle used inline in each check):
   Each new check that needs fenced-block exemption tracks `in_fenced_block: bool = False` locally and toggles on lines starting with ` ``` `.

5. **Add `check_live_discovery_routing`** (Step 2 of plan):
   - Regex: `_DISCOVERY_OVERRIDES_RE = re.compile(r"discovery.*overrides.*registry|discovery\s+map.*wins", re.IGNORECASE)`
   - Skip: lines where `doc.rel_path == MCP_KNOWN_ISSUES_FILE`
   - Skip: lines where `_is_historical_context(doc.lines, i - 1)` is True
   - Severity: `"ERROR"`
   - Skip token: `"discoveryrouting"`

6. **Add `check_routing_authority_v1tools`** (Step 3):
   - Regex: `_V1TOOLS_AUTHORITY_RE = re.compile(r"/v1/tools.*routing\s+authority|/v1/tools.*single\s+source", re.IGNORECASE)`
   - Negation exclusion: skip lines matching `re.search(r"not.*routing\s+authority|not.*source\s+of\s+truth", line, re.IGNORECASE)`
   - Severity: `"ERROR"`
   - Skip token: `"v1toolsrouting"`

7. **Add `check_tool_names_routing_input`** (Step 4):
   - Regex: port `TOOL_NAMES_ROUTING_PATTERN` from old checker (line 56 of `scripts/checks/check_mcp_docs_consistency.py`):
     `r"(?:tool_names.*(routing\s+input|routing\s+drives?|routing\s+determines?)|(?:(?:routing\s+drives?|routing\s+determines?).*tool_names))"`
   - Negation exclusion: skip lines where `"not a routing input"` or `"not routing inputs"` in `line.lower()`
   - Allowlist: skip if `"04_mcp_90_"` in `doc.rel_path` or `"04_mcp_00_"` in `doc.rel_path`
   - Skip code blocks with `in_fenced_block` toggle
   - Severity: `"ERROR"`
   - Skip token: `"toolnamesrouting"`

8. **Add `check_audit_log_single_format`** (Step 5):
   - Regex 1: `_AUDIT_KV_RE = re.compile(r"audit\.log.*key.value|AUDIT\s+session=.*format", re.IGNORECASE)`
   - Regex 2: `_AUDIT_SESSION_PROSE_RE = re.compile(r"AUDIT\s+session=")`
   - Apply only outside fenced code blocks (`in_fenced_block` toggle)
   - For Regex 2: also check that the surrounding ±3 lines do not contain `"json"` or `"jsonl"` as a caveat; if caveat absent, flag
   - Historical context exempt
   - Severity: `"ERROR"`
   - Skip token: `"auditformat"`

9. **Add `check_transport_error_is_error`** (Step 6):
   - Regex: `_TRANSPORT_IS_ERROR_RE = re.compile(r"HttpTransport.*is_error\s*=\s*True|is_error=True.*transport", re.IGNORECASE)`
   - Apply only outside fenced code blocks
   - Allowlist: skip if `doc.rel_path == MCP_KNOWN_ISSUES_FILE`
   - Severity: `"WARNING"` (current code still returns `is_error=True`; this is a future-guard)
   - Skip token: `"transportiserror"`

10. **Add `check_stdio_active_transport`** (Step 7):
    - Regex patterns (list): `[(r"(?:^|[^a-zA-Z])stdio(?:[^a-zA-Z]|$)", "stdio"), (r"StdioTransport", "StdioTransport")]`
    - Allowlist (from old checker line 26-31): `STDIO_ALLOWLIST = frozenset({"04_mcp_02_protocol_and_transport.md", "04_mcp_06_configuration_and_operations.md", "04_mcp_05_security_and_safety_model.md", "04_mcp_00_document-guide.md"})`
    - Skip lines in fenced code blocks
    - Historical context exempt
    - Severity: `"ERROR"`
    - Skip token: `"stdiotransport"`
    - Note: define `_STDIO_ALLOWLIST` as a module-level `frozenset[str]` constant.

11. **Add `check_watchdog_restarts_on_dependency_failure`** (Step 8):
    - Regex: `_WATCHDOG_RESTART_RE = re.compile(r"watchdog.*restart.*dependency|dependency.*failure.*watchdog.*restart", re.IGNORECASE)`
    - Historical context exempt
    - Severity: `"ERROR"`
    - Skip token: `"watchdogrestart"`

12. **Add `check_strict_validation_skips_unreachable`** (Step 9):
    - Regex: `_STRICT_SKIP_RE = re.compile(r"strict.*skip.*unreachable|skip.*unreachable.*strict", re.IGNORECASE)`
    - Historical context exempt
    - Severity: `"ERROR"`
    - Skip token: `"strictskip"`

13. **Update `main()` dispatch block** (Step 10):
    - Extend `skip_choices` list from `["startup", "failopen", "routing", "active", "toolcount"]` to include:
      `"discoveryrouting"`, `"v1toolsrouting"`, `"toolnamesrouting"`, `"auditformat"`, `"transportiserror"`, `"stdiotransport"`, `"watchdogrestart"`, `"strictskip"`
    - Add dispatch lines after existing checks:
      ```python
      if "discoveryrouting" not in skip:
          all_issues.extend(check_live_discovery_routing(docs_dir, files))
      if "v1toolsrouting" not in skip:
          all_issues.extend(check_routing_authority_v1tools(docs_dir, files))
      if "toolnamesrouting" not in skip:
          all_issues.extend(check_tool_names_routing_input(docs_dir, files))
      if "auditformat" not in skip:
          all_issues.extend(check_audit_log_single_format(docs_dir, files))
      if "transportiserror" not in skip:
          all_issues.extend(check_transport_error_is_error(docs_dir, files))
      if "stdiotransport" not in skip:
          all_issues.extend(check_stdio_active_transport(docs_dir, files))
      if "watchdogrestart" not in skip:
          all_issues.extend(check_watchdog_restarts_on_dependency_failure(docs_dir, files))
      if "strictskip" not in skip:
          all_issues.extend(check_strict_validation_skips_unreachable(docs_dir, files))
      ```

14. **Update module docstring** at the top of the file to list the eight new `--skip` tokens alongside the existing five.

### Method

- All new check functions share the signature: `def check_NAME(docs_dir: Path, files: list[DocFile]) -> list[Issue]`
- `DocFile` and `Issue` dataclasses are already defined; use them directly.
- Fenced block tracking pattern (inline, per function):
  ```python
  in_fenced_block = False
  for i, line in enumerate(doc.lines, start=1):
      if line.startswith("```"):
          in_fenced_block = not in_fenced_block
          continue
      if in_fenced_block:
          continue
      # ... check logic
  ```
- Historical context helper signature: `_is_historical_context(lines: list[str], line_idx: int) -> bool`
  - `line_idx` is 0-based (pass `i - 1` when iterating with `enumerate(start=1)`)
- `_STDIO_ALLOWLIST` should use basename comparison: `doc.rel_path` already stores the relative path from `docs/`; filenames in the allowlist use bare filenames, so use `Path(doc.rel_path).name in _STDIO_ALLOWLIST` or ensure `rel_path` values match.

### Details

- `VALID_STARTUP_MODES` is at line 32; the change is a one-line edit.
- `MCP_KNOWN_ISSUES_FILE = "04_mcp_90_inconsistencies_and_known_issues.md"` is already defined at line 34 — reuse it in new check allowlists.
- `skip_choices` list is defined at line 507 inside `main()`.
- The `if "..." not in skip:` dispatch starts at line 531.
- The old checker's `STDIO_ALLOWLIST` contains four files (lines 26-31 of `scripts/checks/check_mcp_docs_consistency.py`) — copy those exact filenames.
- For `check_tool_names_routing_input`, the regex literal is copied verbatim from the old checker's `TOOL_NAMES_ROUTING_PATTERN` (line 56) but assigned to a module-level constant `_TOOL_NAMES_ROUTING_RE = re.compile(TOOL_NAMES_ROUTING_PATTERN)`.
- For `check_audit_log_single_format`: the "caveat nearby" logic checks `doc.lines[max(0, i-4):i+3]` for the string `"json"` (case-insensitive); if absent, flag.

## Validation plan

```bash
# 1. Existing tests still pass (includes updated ondemand test)
uv run pytest tests/test_check_mcp_docs_consistency.py -v

# 2. Script runs against real docs with zero false positives
uv run python scripts/check_mcp_docs_consistency.py
# Expected: exit 0, "No issues found."

# 3. Lint check
uv run ruff check scripts/check_mcp_docs_consistency.py

# 4. Type check (if mypy configured)
uv run mypy scripts/check_mcp_docs_consistency.py

# 5. Manual stale-pattern smoke test
# Create /tmp/test_stale.md with content: `startup_mode = "ondemand"`
# Run: uv run python scripts/check_mcp_docs_consistency.py --docs-dir /tmp/testdocs/
# Expected: exit 1 with [ERROR] ... Unsupported startup_mode value: 'ondemand'

# 6. Verify skip tokens work
uv run python scripts/check_mcp_docs_consistency.py --skip discoveryrouting v1toolsrouting toolnamesrouting auditformat transportiserror stdiotransport watchdogrestart strictskip
# Expected: exit 0 (same as running with only the original 5 checks)
```
