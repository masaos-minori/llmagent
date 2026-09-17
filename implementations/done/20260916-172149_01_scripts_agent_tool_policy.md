## Goal

Replace `_special_case_risk()`'s raw `cmd.startswith(p)` shell-command safe-prefix check with a parsed-command authorization scheme that establishes real executable identity, applies per-executable argument/path constraints, and fails closed (`RiskLevel.HIGH`) on any ambiguous or compound shell syntax. (REQ-001; "Replace the raw `cmd.startswith(p)` match in `_special_case_risk()`'s `shell_run` branch with a parsed, tokenized executable-identity check")

## Scope

- Replace `cmd.startswith(p)` with exact leading-token-sequence equality matching against `approval_shell_safe_prefixes`.
- Add metacharacter fail-closed check (REQ-002).
- Route matched commands' remaining positional tokens through `approval_protected_paths`/`allowed_root` checks (REQ-003).
- Implement the `cat`/`find`/`grep` NONE-eligibility decision and its unsafe-flag denylist (REQ-004).

## Assumptions

- `shlex.split()` is available and correctly tokenizes the command string; a `ValueError` (e.g. unbalanced quotes) or empty result fails closed to `RiskLevel.HIGH`.
- The existing `approval_shell_safe_prefixes` list values (e.g. `"git log"`, `"git status"`) are multi-word entries where the second word is a subcommand — both the prefix entry and incoming command must be tokenized identically before comparison.
- The `_escalate_for_path()` function already exists and handles protected-path escalation; `check_allowed_root()` already exists and handles `allowed_root` containment. Both need to be called for `shell_run`'s positional arguments.

## Design decisions

- Tokenize both the configured prefix entry and the incoming command with `shlex.split()` before comparison — mirroring the same parsing discipline used by `shell_service.py::_check_command()`. This ensures multi-word entries like `"git log"` match only `git log ...` and not `git-log ...`.
- Use `os.path.basename(argv[0])` for single-word entries (e.g. `"cat"`) to avoid matching `/bin/cat` as a different executable. For multi-word entries, compare the corresponding leading tokens directly.
- Fail closed on any metacharacter detection in the *raw* command string before attempting tokenization — `shlex.split()` cannot detect these as operators (they become literal tokens), so raw-string scanning is required.

## Alternatives considered

- Adding a new `is_none_mode` property on `StartupMode` — unnecessary since `is_disabled` already covers this.
- Checking `cfg.startup_mode` directly instead of `cfg.is_disabled` — equivalent but less semantic; `is_disabled` is the established convention.

## Compatibility considerations

- Existing non-disabled servers are unaffected; the added `is_disabled` check only prevents registry publication for disabled servers.
- A disabled server excluded by this change will not appear in the registry's `_tools` dict, which is consistent with treating it as "not configured."

## Security considerations

- Preventing registry publication for disabled servers eliminates the possibility of a disabled server's tools being available for execution even if other gates are bypassed.

## Rollback considerations

- Reverting the `is_disabled` check in `publish_all()` restores the pre-fix behavior where disabled servers get their tools published to the registry.

## Implementation

### Target file

`scripts/agent/tool_policy.py`

### Procedure

1. **Phase 1: Metacharacter fail-closed**
   - In `_special_case_risk()`'s `shell_run` branch, add a raw-string scan for shell control operators (`;`, `&&`, `||`, `&`, `|`, backtick, `$(`, `<(`, `>(`, `>`, `>>`, `<`, newline) — any match fails closed to `RiskLevel.HIGH` regardless of prefix match.

2. **Phase 2: Parsed identity match**
   - Replace `cmd.startswith(p)` with `shlex.split()` tokenization + exact leading-token-sequence equality against `approval_shell_safe_prefixes`.
   - On `ValueError` (unbalanced quotes) or empty result, fail closed to `RiskLevel.HIGH`.
   - For single-word entries: compare `os.path.basename(argv[0])` against the entry.
   - For multi-word entries: compare the corresponding leading tokens after tokenizing both the entry and the command.

3. **Phase 3: Path/argument constraint**
   - For a matched entry, extract every remaining non-flag (positional, path-like) token and route it through `_escalate_for_path()` and `check_allowed_root()`.
   - If either returns HIGH or False respectively, escalate to `RiskLevel.HIGH`.

4. **Phase 4: cat/find/grep NONE-eligibility**
   - Implement an unsafe-flag denylist per executable: e.g. `find -exec`, `find -delete`; `cat --force` (if applicable); `grep -r /etc/passwd` (restricted paths).
   - NONE-eligible only when every REQ-003 path check passes AND no argument matches a documented unsafe-flag denylist for that executable.

### Method

- **Step 1**: Edit `_special_case_risk()` at lines 134-140 — add metacharacter check, replace `startswith` with tokenized matching, add path/argument routing.
- **Step 2**: Add helper functions `_has_metacharacters(cmd: str) -> bool` and `_match_executable_identity(argv: list[str], prefixes: list[str]) -> RiskLevel | None` inside `tool_policy.py`.
- **Step 3**: Add `_check_positional_args(cfg, argv: list[str], base: RiskLevel) -> RiskLevel | None` helper for path/argument constraint enforcement.
- **Step 4**: Add `_unsafe_flag_denylist(tool_name: str, args: list[str]) -> bool` helper for per-executable flag checking.

### Details

**Step 1 — Metacharacter fail-closed:**

```python
import re

# At module level:
_METACHAR_RE = re.compile(r'[;|&]|&&|\|\||`|\$\(|<\(|>\(|>>|<<|[<>]|\n')

def _has_metacharacters(cmd: str) -> bool:
    """Return True if the raw command contains shell metacharacters/control operators."""
    return bool(_METACHAR_RE.search(cmd))
```

After line 134 (`if tool_name == "shell_run":`):

```python
if tool_name == "shell_run":
    cmd = args.get("command")
    if not isinstance(cmd, str):
        return RiskLevel.HIGH
    # REQ-002: fail closed on any shell metacharacter in raw command
    if _has_metacharacters(cmd):
        return RiskLevel.HIGH
    # REQ-001: parsed identity match replaces startswith below
    # ... rest of the method
```

**Step 2 — Parsed identity match:**

```python
def _match_executable_identity(
    argv: list[str],
    prefixes: list[str],
) -> RiskLevel | None:
    """Return NONE if the parsed command exactly matches a safe prefix entry, else None."""
    if not argv:
        return None
    for prefix_entry in prefixes:
        prefix_tokens = shlex.split(prefix_entry) if prefix_entry.strip() else []
        if not prefix_tokens:
            continue
        # Single-word prefix: match basename of the first argv token
        if len(prefix_tokens) == 1:
            if os.path.basename(argv[0]) == prefix_tokens[0]:
                return RiskLevel.NONE
        # Multi-word prefix: match corresponding leading tokens
        elif len(argv) >= len(prefix_tokens):
            if all(os.path.basename(a) == p for a, p in zip(argv[:len(prefix_tokens)], prefix_tokens)):
                return RiskLevel.NONE
    return None
```

After the metacharacter check (around line 138):

```python
    if tool_name == "shell_run":
        cmd = args.get("command")
        if not isinstance(cmd, str):
            return RiskLevel.HIGH
        # REQ-002: fail closed on any shell metacharacter in raw command
        if _has_metacharacters(cmd):
            return RiskLevel.HIGH
        # REQ-001: parsed identity match
        try:
            argv = shlex.split(cmd)
        except ValueError:
            return RiskLevel.HIGH
        if not argv:
            return RiskLevel.HIGH
        if match := _match_executable_identity(argv, cfg.approval.approval_shell_safe_prefixes):
            return match
        return RiskLevel.HIGH
```

**Step 3 — Path/argument constraint:**

```python
def _check_positional_args(
    cfg: AgentConfig,
    argv: list[str],
    base: RiskLevel,
) -> RiskLevel | None:
    """Route positional args through protected-path and allowed-root checks."""
    if base == RiskLevel.HIGH:
        return None
    # Extract positional (non-flag) tokens from argv[1:]
    positional = [a for a in argv[1:] if not a.startswith("-")]
    if not positional:
        return None
    path_keys = cfg.approval.approval_resource_keys.get("path_keys", [])
    for pos in positional:
        # Check protected paths
        for val in [pos]:
            if any(val.startswith(p) for p in cfg.approval.approval_protected_paths):
                return RiskLevel.HIGH
        # Check allowed_root
        if cfg.approval.allowed_root:
            root = Path(cfg.approval.allowed_root).resolve()
            try:
                resolved = Path(pos).resolve()
            except (ValueError, OSError):
                return RiskLevel.HIGH
            if not resolved.is_relative_to(root):
                return RiskLevel.HIGH
    return None
```

After the identity match in `_special_case_risk()`:

```python
        if match := _match_executable_identity(argv, cfg.approval.approval_shell_safe_prefixes):
            # REQ-003: route positional args through path/argument checks
            if escalated := _check_positional_args(cfg, argv, match):
                return escalated
            # REQ-004: check unsafe flags for this executable
            if _unsafe_flag_denylist(argv[0], argv[1:]):
                return RiskLevel.HIGH
            return match
```

**Step 4 — Unsafe flag denylist:**

```python
_UNSAFE_FLAGS = {
    "find": {"-exec", "-delete", "-ok"},
    "cat": set(),  # cat has no known unsafe flags; path constraints apply via REQ-003
    "grep": {"-r", "-R"},  # recursive grep may traverse outside allowed_root
}

def _unsafe_flag_denylist(executable: str, args: list[str]) -> bool:
    """Return True if any argument matches a documented unsafe-flag denylist for this executable."""
    flags = _UNSAFE_FLAGS.get(executable, set())
    if not flags:
        return False
    return any(arg in flags for arg in args)
```

## Validation plan

- Run unit tests: `uv run pytest tests/agent/test_tool_policy.py tests/agent/test_tool_policy_comprehensive.py -v`
- Verify prefix collision rejection: add a test asserting `category_dump_secrets` does NOT match the `"cat"` prefix.
- Verify metacharacter rejection: add tests for each metacharacter class (`;`, `&&`, `|`, backtick, `$()`).
- Verify path/argument routing: add a test with a `cat /etc/shadow` command and assert HIGH escalation.
- Static analysis: `uv run ruff check scripts/agent/tool_policy.py`, `uv run mypy scripts/agent/tool_policy.py`, `uv run bandit scripts/agent/tool_policy.py`.

## Completion criteria

- [ ] `_special_case_risk()` rejects prefix collisions (e.g. `category_dump_secrets` ≠ `cat`).
- [ ] `_special_case_risk()` rejects metacharacter-bearing commands.
- [ ] `_special_case_risk()` routes positional arguments through protected-path/allowed-root checks.
- [ ] All existing tests pass without regression.
- [ ] No new lint/type/security errors introduced.

## Out of scope

- Modifying `scripts/mcp_servers/shell/` (the shell-mcp server's own `command_allowlist` check is a separate defense layer).
- Any MCP server business logic unrelated to the startup/discovery/registry-publication path.

## execution_status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260917-102843 | 20260917-102843 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260917-102929 | 20260917-102929 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260917-102955 | 20260917-102955 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260917-103407 | 20260917-103407 | N/A: no docs/00_index.md task-scope mapping for scripts/agent/tool_policy.py |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20260914-103045_mcpagent02_shell-command-parsed-policy-enforcement.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-120003_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-172149
- **Related target files**: scripts/agent/tool_policy.py