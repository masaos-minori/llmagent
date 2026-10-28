# mcpcompat001-add-the-two-syntax-tree-rules-to-the-compat-checker

Plan source: `plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md`
Generated: 2026-10-28T01:32:16+09:00

## Goal

Add two syntax-tree (AST) rules to `tools/check_compat_shims.py`, each in its own function:
one reporting a `shared.mcp_config` import of either Health type, and one reporting a
`McpToolDiscoveryService(` construction without `posture_gates` (REQ-005; AC-7).

## Scope

- New module constant `_MCP_HEALTH_REEXPORT_NAMES` (new) and two new functions
  `check_mcp_health_reexport_import(content, filepath)` (new) and
  `check_gateless_discovery_construction(content, filepath)` (new).
- Wiring into `check_all()` (current L520) as unconditional additions after the existing
  pattern checks.
- No CLI flag changes, no changes to `check_compat_patterns`, `check_removed_name_reintroduction`,
  `check_doc_symbols`, or `main()`.

## Assumptions

- Verified 2026-10-28 against the current source: `check_compat_patterns` (L482) matches single
  stripped lines and cannot see multi-line `from shared.mcp_config import (...)` blocks or
  keyword arguments; `main()` (L549) already walks `scripts/`, `docs/`, `tests/`, `tools/` for
  `**/*.py` and `**/*.md` and feeds every file through `check_all()`, so the new rules reach
  the whole corpus with no `main()` edits.
- `main()`'s cyclomatic complexity (18, plan target row) is untouched because the rules hang off
  `check_all()`, not `main()`.
- Self-reference safety: the checker's own source mentions the names only as string literals in
  the constant and messages; string constants are not `ImportFrom`/`Call` nodes, so the AST
  rules cannot flag the checker itself. `tools/check_compat_shims.py` and
  `tests/tools/test_check_compat_shims.py` also carry manifest allowlist entries
  (`check-compat-shims-source`, `check-compat-shims-test-data`) as a second guard.
- The rules land after plan Phases 1-2, when the live corpus is already clean, so the default
  run's pass/fail behavior is unchanged (REQ-005).

## Design decisions

- AST instead of line patterns: the compat surfaces this Issue removes are multi-line import
  blocks and constructor calls with keyword arguments — exactly the shapes line matching cannot
  see (plan target row); an `ast.walk` scan is precise about module, alias, and keyword names.
- Two separate functions, one finding type each (plan wording "in separate functions"): the
  messages stay single-purpose and the unit tests in procedure 18 exercise each rule
  independently.
- Unconditional wiring (not another opt-in flag): the Issue's point is that these two paths are
  gone for good, so a reintroduction should block the default run like `check_compat_patterns`
  does; the manifest allowlist remains the only exemption channel.
- The name set covers both current Health types and the three historical names
  (MCPHealthSnapshot, ServerHealthState, `classify_server_failure` — the pre-rename trio
  recorded in `scripts/shared/mcp_health.py`'s docstring), so an old-style import cannot slip
  back in under a superseded name.
- `SyntaxError` tolerance: a file that fails `ast.parse` returns no findings from the new rules
  (line-based rules still see it); a broken file never silently suppresses the other checks.

## Alternatives considered

- Extending `COMPAT_PATTERNS` with regexes: rejected — multi-line imports defeat single-line
  matching (the checker's own docstring notes this limitation) and regexes would flag the
  checker's and tests' own fixture strings, forcing allowlist growth.
- Gating the rules behind a new CLI flag: rejected — opt-in rules are skipped by callers that
  forget the flag; `--check-removed-names` exists only because its corpus semantics are
  docs-specific, which does not apply here.
- One combined function: rejected — the plan mandates separate functions and separate finding
  types for the two compat surfaces.

## Implementation

### Target file

`tools/check_compat_shims.py`

### Procedure

1. Add `import ast` to the module imports (top of file; `argparse` etc. live at L16).
2. Add the constant near the other pattern constants:
   ```python
   _MCP_HEALTH_REEXPORT_NAMES = frozenset(
       {
           "McpServerHealthRegistry",
           "McpServerHealthState",
           "MCPHealthSnapshot",  # pre-rename name
           "ServerHealthState",  # pre-rename name
           "classify_server_failure",  # pre-rename name
       }
   )
   ```
3. Add the two functions after `check_removed_name_reintroduction()` (L418-L475), following its
   `(content, filepath) -> list[str]` signature convention:
   ```python
   def check_mcp_health_reexport_import(content: str, filepath: Path) -> list[str]:
       """Flag an import of a Health name from the removed shared.mcp_config re-export."""
       if filepath.suffix != ".py":
           return []
       try:
           tree = ast.parse(content)
       except SyntaxError:
           return []
       issues: list[str] = []
       for node in ast.walk(tree):
           if isinstance(node, ast.ImportFrom) and node.module == "shared.mcp_config":
               for alias in node.names:
                   if alias.name in _MCP_HEALTH_REEXPORT_NAMES:
                       issues.append(
                           f"{filepath}:{node.lineno}: Health name imported from the "
                           f"removed shared.mcp_config re-export path — import "
                           f"'{alias.name}' from shared.mcp_health instead"
                       )
       return issues


   def check_gateless_discovery_construction(content: str, filepath: Path) -> list[str]:
       """Flag a McpToolDiscoveryService construction that omits the posture_gates argument."""
       if filepath.suffix != ".py":
           return []
       try:
           tree = ast.parse(content)
       except SyntaxError:
           return []
       issues: list[str] = []
       for node in ast.walk(tree):
           if (
               isinstance(node, ast.Call)
               and isinstance(node.func, ast.Name)
               and node.func.id == "McpToolDiscoveryService"
               and "posture_gates" not in {kw.arg for kw in node.keywords if kw.arg}
               and len(node.args) < 2
           ):
               issues.append(
                   f"{filepath}:{node.lineno}: McpToolDiscoveryService constructed without "
                   f"posture_gates — the argument is required (no None default)"
               )
       return issues
   ```
4. Wire both into `check_all()` after the existing composition line (L543-545), before the
   `include_removed_names` block:
   ```python
   issues += check_mcp_health_reexport_import(content, filepath)
   issues += check_gateless_discovery_construction(content, filepath)
   ```
   and extend `check_all()`'s docstring with one sentence naming the two new always-on AST rules.
5. Run the live corpus check (after Phases 1-2 have landed). One manifest entry is expected:
   procedure 13 deliberately keeps a gate-less `McpToolDiscoveryService(ctx)` inside
   `pytest.raises(TypeError)` in `tests/agent/services/test_mcp_tool_discovery_posture_gate.py`,
   and the AST rule cannot tell a negative-test construction from a reintroduction. Add
   `[[compatibility_exceptions]]` `id = "mcp-posture-gate-negative-test"`,
   `path = "tests/agent/services/test_mcp_tool_discovery_posture_gate.py"`,
   `reason = "Negative test that asserts construction without posture_gates raises TypeError"`,
   `owner = "Repository owner"`, `expires = "2027-04-22"`, `removal_condition = "Remove when this test no longer constructs the service without posture_gates."`,
   `category = "fixture"` — the plan's "explicit allowlist for negative tests" path. Also update the `tools/compat_exceptions.toml` header comment ("These 20 paths" -> "These 21 paths") and procedure 18's `TestManifestParity` expectation in the same change set. No other
   exemptions are expected: the AST design keeps the checker's and other tests' fixture strings
   clean (Assumptions).

### Method

Additive functions plus a two-line wiring edit; existing checks byte-for-byte unchanged.

### Details

- The positional-argument escape (`len(node.args) < 2`) keeps a hypothetical
  `McpToolDiscoveryService(ctx, gates)` positional call legal while flagging the truly
  gate-less `McpToolDiscoveryService(ctx)`.
- Finding strings follow the `f"{filepath}:{lineno}: message"` format used by every existing
  rule, so `main()`'s printing and exit-code counting work unchanged.

## Compatibility considerations

- Hard ordering: lands after plan Phases 1-2 (procedures 01-15) — running the rules against a
  corpus that still contains the re-export or gate-less calls would block, which is correct
  behavior but not the plan's sequence (Phase 3 after Phases 1-2).
- CI (`backward-compat-check.yml`) and the pre-commit hook already invoke the tool without
  listing files; no workflow edits are needed because the rules hang off the default scan
  (REQ-007).
- `tools/TOOL_DESCRIPTIONS.md` must be updated in the same change set — procedure 19
  (`check_tool_descriptions_sync.py` guard).

## Security considerations

- Read-only static analysis; no execution of scanned code, no network.

## Rollback considerations

- Revert the checker edit alone: the rules are additive, so removing them restores exactly the
  prior pass/fail behavior; no other procedure depends on the rules.

## Validation plan

- `uv run python tools/check_compat_shims.py` — exit 0 with both rules active on the live
  corpus (plan Phase 3 step 10; AC-7).
- `uv run pytest tests/tools/test_check_compat_shims.py -q` — existing tests pass unmodified
  plus procedure 18's new tests pass.
- `uv run ruff check tools/check_compat_shims.py`, `uv run mypy --no-namespace-packages tools/check_compat_shims.py` — clean.
- `uv run python tools/check_tool_descriptions_sync.py` — in sync after procedure 19.

## Completion criteria

- A `shared.mcp_config` import of any name in `_MCP_HEALTH_REEXPORT_NAMES` (new) and a
  `McpToolDiscoveryService(` construction lacking `posture_gates` each produce a finding in a
  fixture and none in the live corpus once the `mcp-posture-gate-negative-test` manifest entry
  covers the one intentional gate-less construction (REQ-005, AC-7).
- All pre-existing checker tests pass unmodified (REQ-007).

## Out of Scope

- Test additions for the rules — procedure 18.
- Catalog wording — procedure 19.
- The compat removals themselves — procedures 01-16.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | In Progress | 2026-10-28 | — | Lands after procedures 01-16 (plan Phase 3) |
| 2 | Add or update tests per Validation plan | In Progress | 2026-10-28 | — | New rule tests covered by procedure 18 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | In Progress | 2026-10-28 | — | checker run, pytest, ruff, mypy |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | In Progress | 2026-10-28 | — | Procedure 19 covers the catalog |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261027-104222_mcpcompat001_remove-mcp-compat-paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-013216
- **Related target files**: tools/check_compat_shims.py
