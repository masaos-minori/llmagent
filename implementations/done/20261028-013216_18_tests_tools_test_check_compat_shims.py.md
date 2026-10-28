# mcpcompat001-test-the-two-new-compat-checker-rules

Plan source: `plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md`
Generated: 2026-10-28T01:32:16+09:00

## Goal

Add unit tests for the two new AST rules of `tools/check_compat_shims.py` to
`tests/tools/test_check_compat_shims.py`, and a manifest-parity guard for the new allowlist
entry (REQ-005; AC-7).

## Scope

- Two new test classes appended to the existing test module:
  - `TestMcpHealthReexportImport` (new)
  - `TestGatelessDiscoveryConstruction` (new)
- Extension of the existing `TestManifestParity` pattern: a case asserting
  `tests/agent/services/test_mcp_tool_discovery_posture_gate.py` is allowlisted against the
  gate-less construction rule (the intentional `pytest.raises(TypeError)` construction).
- One deliberate edit to the existing `TestManifestParity.test_loaded_paths_match_needed_paths`: it pins the exact manifest path set (20 paths, `len(expected) == 20`), so the new `tests/agent/services/test_mcp_tool_discovery_posture_gate.py` entry from procedure 17 step 5 must be added to `expected`, `len(expected)` becomes 21 and the class docstring count is updated. No other existing test class changes.

## Assumptions

- Test idiom verified against the current file (2026-10-28): rule tests feed inline content
  strings with synthetic paths such as `Path("scripts/test.py")` straight into the rule
  functions with `allowlist=set()` (e.g. `TestPatternDetection`, L44; `TestRemovedNameReintroduction`,
  L305), so no on-disk fixtures are needed.
- The two new rule functions and the constant import from `tools.check_compat_shims` per the
  procedure 17 names: `check_mcp_health_reexport_import` (new), `check_gateless_discovery_construction` (new).
- `tests/tools/test_check_compat_shims.py` already holds the `check-compat-shims-test-data`
  manifest entry, so the repo-wide scan tolerates the new fixture snippets in this file itself.

## Design decisions

- Positive and negative cases per rule: each test class asserts (a) the violating shape is
  flagged with a line number, (b) the canonical replacement shape produces zero findings, and
  (c) a multi-line / keyword-argument shape — the reason AST rules replaced line matching — is
  handled correctly.
- Fixtures are inline strings, not files on disk: matches the module's existing style and keeps
  the tests independent of the live corpus.

## Alternatives considered

- Corpus-wide assertions only (scan the repo, expect zero): rejected as the sole test — it
  proves "clean today" but not that each rule actually detects its shape; the plan requires
  checker tests for the rules themselves.

## Implementation

### Target file

`tests/tools/test_check_compat_shims.py`

### Procedure

1. Extend the `from tools.check_compat_shims import (...)` block with
   `check_gateless_discovery_construction` (new) and `check_mcp_health_reexport_import` (new).
2. Append the two classes:
   ```python
   class TestMcpHealthReexportImport:
       """AST rule: shared.mcp_config must not be a source of Health names."""

       def test_multiline_reexport_import_is_flagged(self) -> None:
           content = (
               "from shared.mcp_config import (\n"
               "    McpServerConfig,\n"
               "    McpServerHealthRegistry,\n"
               "    McpServerHealthState,\n"
               ")\n"
           )
           issues = check_mcp_health_reexport_import(content, Path("scripts/test.py"))
           assert len(issues) == 2
           assert "shared.mcp_config" in issues[0] and ":2:" in issues[0]

       def test_canonical_import_is_clean(self) -> None:
           content = "from shared.mcp_health import McpServerHealthState\n"
           assert check_mcp_health_reexport_import(content, Path("scripts/test.py")) == []

       def test_other_mcp_config_names_are_clean(self) -> None:
           content = "from shared.mcp_config import McpServerConfig, TransportType\n"
           assert check_mcp_health_reexport_import(content, Path("scripts/test.py")) == []

       def test_non_python_file_is_skipped(self) -> None:
           content = "from shared.mcp_config import McpServerHealthState\n"
           assert check_mcp_health_reexport_import(content, Path("docs/test.md")) == []


   class TestGatelessDiscoveryConstruction:
       """AST rule: McpToolDiscoveryService requires the posture_gates argument."""

       def test_gateless_construction_is_flagged(self) -> None:
           content = "svc = McpToolDiscoveryService(ctx)\n"
           issues = check_gateless_discovery_construction(content, Path("scripts/test.py"))
           assert len(issues) == 1
           assert "posture_gates" in issues[0] and ":1:" in issues[0]

       def test_keyword_gates_construction_is_clean(self) -> None:
           content = "svc = McpToolDiscoveryService(ctx, posture_gates=gates)\n"
           assert check_gateless_discovery_construction(content, Path("scripts/test.py")) == []

       def test_positional_gates_construction_is_clean(self) -> None:
           content = "svc = McpToolDiscoveryService(ctx, gates)\n"
           assert check_gateless_discovery_construction(content, Path("scripts/test.py")) == []

       def test_multiline_gateless_construction_is_flagged(self) -> None:
           content = (
               "svc = McpToolDiscoveryService(\n"
               "    ctx,\n"
               ")\n"
           )
           issues = check_gateless_discovery_construction(content, Path("tests/test.py"))
           assert len(issues) == 1
   ```
3. In `TestManifestParity.test_loaded_paths_match_needed_paths`, add `ROOT_DIR / "tests/agent/services/test_mcp_tool_discovery_posture_gate.py"` to `expected` (sorted position), change `assert len(expected) == 20` to `21`, and change the docstring "20 paths" to "21 paths".
4. Add one case asserting `check_all()` surfaces both new rules by default
   (`include_removed_names=False`) and honors the allowlist for the posture-gate negative-test
   file:
   ```python
   class TestNewAstRulesWiring:
       def test_check_all_runs_both_new_rules_by_default(self) -> None:
           content = (
               "from shared.mcp_config import McpServerHealthState\n"
               "svc = McpToolDiscoveryService(ctx)\n"
           )
           issues = check_all(content, Path("scripts/test.py"), allowlist=set())
           assert any("removed shared.mcp_config re-export path" in i for i in issues)
           assert any("without posture_gates" in i for i in issues)

       def test_allowlisted_negative_test_file_is_exempt(self) -> None:
           content = "with pytest.raises(TypeError):\n    McpToolDiscoveryService(ctx)\n"
           path = Path("tests/agent/services/test_mcp_tool_discovery_posture_gate.py")
           assert check_all(content, path, allowlist={path}) == []
   ```

### Method

Append-only test classes plus one import-block extension; existing test classes untouched.

### Details

- Message substrings asserted (`"removed shared.mcp_config re-export path"`, `"without
  posture_gates"`) match procedure 17's finding strings exactly; if 17 lands with wording
  drift, align the test strings to the landed rule (the pairing is a contract, not a coincidence).
- The negative-test-file exemption case documents, in the test suite, why the manifest entry
  `mcp-posture-gate-negative-test` (procedure 17 step 5) exists.

## Compatibility considerations

- Lands directly after procedure 17 (the rules must exist to be imported).
- The `check-compat-shims-test-data` manifest entry already exempts this file from the live
  scan; no new manifest entry for the test file itself is needed.

## Security considerations

- Pure string fixtures; nothing executed beyond the checker's `ast.parse`.

## Rollback considerations

- Revert together with procedure 17; the tests import names that only exist after 17.

## Validation plan

- `uv run pytest tests/tools/test_check_compat_shims.py -q` — all new and pre-existing tests
  pass (AC-7).
- `uv run ruff check tests/tools/`, `uv run mypy --no-namespace-packages tests/tools/` — clean.
- `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` on the
  live corpus — exit 0 with this file's fixtures allowlisted.

## Completion criteria

- Each new rule has a flagged case and a clean case; `check_all()` default wiring and allowlist
  behavior are pinned by tests (REQ-005, AC-7).

## Out of Scope

- The rule implementations — procedure 17.
- Catalog wording — procedure 19.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | In Progress | 2026-10-28 | — | Lands directly after procedure 17 |
| 2 | Add or update tests per Validation plan | In Progress | 2026-10-28 | — | This document is the test procedure |
| 3 | Run the validation sequence (`rules/toolchain.md`) | In Progress | 2026-10-28 | — | pytest, ruff, mypy |
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
- **Related target files**: tests/tools/test_check_compat_shims.py
